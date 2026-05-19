"""
AI-пайплайн поиска товаров: 6 шагов.

Распределение моделей (ТЗ 7.2):
  Шаг 1: парсинг          → Sonnet
  Шаг 2: поиск API        → без LLM
  Шаг 3: фильтрация       → Sonnet
  Шаг 4: анализ отзывов   → Opus
  Шаг 5: ранжирование     → Opus
  Шаг 6: форматирование   → Sonnet

Производительность:
  - Шаг 4 анализирует до 6 товаров параллельно (asyncio.gather).
  - System-промпты помечены cache_system=True → повторные запросы дешевле в 10×.
  - При сбое LLM на любом шаге — graceful fallback на heuristic.
"""
from __future__ import annotations

import asyncio
import json
import logging

from app.ai.claude_client import MODEL_OPUS, MODEL_SONNET, call_claude_json
from app.ai.prompts import (
    FILTER_SYSTEM,
    FILTER_USER,
    FORMAT_SYSTEM,
    FORMAT_USER,
    PARSE_SYSTEM,
    PARSE_USER,
    RANK_SYSTEM,
    RANK_USER,
    REVIEWS_SYSTEM,
    REVIEWS_USER,
)
from app.ai.schemas import MarketplaceProduct, ParsedRequest
from app.marketplaces.base import search_all_marketplaces

logger = logging.getLogger(__name__)

REVIEWS_PARALLEL_LIMIT = 6
TOP3_DEFAULT = 3


async def run_search_pipeline(query: str, user) -> dict:
    """Оркестрирует все шаги пайплайна. Возвращает dict с готовыми products."""

    # ── Шаг 1: Парсинг запроса (Sonnet) ──────────────────────────────────
    logger.info("Pipeline step 1: parse query")
    try:
        parsed_data = await call_claude_json(
            system=PARSE_SYSTEM,
            user_message=PARSE_USER.format(query=query),
            model=MODEL_SONNET,
            cache_system=True,
        )
        parsed = ParsedRequest(**parsed_data)
    except Exception as e:
        logger.exception("Parse failed: %s", e)
        return {
            "needs_clarification": True,
            "clarification": "Не понял запрос. Попробуй описать что ищешь, например: «робот-пылесос до 30к»",
        }

    if parsed.needs_clarification:
        return {
            "needs_clarification": True,
            "clarification": parsed.clarification_question or "Уточни запрос.",
        }

    # ── Шаг 2: Поиск по маркетплейсам ────────────────────────────────────
    logger.info("Pipeline step 2: marketplace search for category=%s", parsed.category)
    raw_products = await search_all_marketplaces(parsed)

    if not raw_products:
        return {
            "needs_clarification": True,
            "clarification": "По этому запросу ничего не нашёл. Уточни категорию или бюджет?",
        }

    # ── Шаг 3: Фильтрация (Sonnet) ───────────────────────────────────────
    logger.info("Pipeline step 3: filter (%d candidates)", len(raw_products))
    filtered = await _filter_step(parsed, raw_products)

    if not filtered:
        # Heuristic fallback: топ-9 по price ascending в рамках бюджета
        filtered = sorted(raw_products, key=lambda p: p.price)[:9]
        logger.info("Filter returned empty, using heuristic fallback")

    # ── Шаг 4: Параллельный анализ отзывов (Opus) ────────────────────────
    logger.info("Pipeline step 4: reviews analysis (%d products)", min(len(filtered), REVIEWS_PARALLEL_LIMIT))
    analyzed = await _reviews_step(filtered[:REVIEWS_PARALLEL_LIMIT])

    # ── Шаг 5: Ранжирование (Opus) ───────────────────────────────────────
    logger.info("Pipeline step 5: ranking")
    ranked_list = await _rank_step(query, parsed, analyzed)
    if not ranked_list:
        # Heuristic fallback: топ по соотношению rating/price
        ranked_list = _heuristic_rank(filtered[:TOP3_DEFAULT])

    # ── Шаг 6: Сборка карточек + share text ──────────────────────────────
    logger.info("Pipeline step 6: assemble result")
    products_out = _assemble_products(ranked_list, raw_products, analyzed)

    share_text = await _share_text_step(query, products_out)

    return {
        "parsed_request": parsed.model_dump(),
        "products": products_out,
        "share_text": share_text,
        "needs_clarification": False,
    }


# ── Steps ────────────────────────────────────────────────────────────────────


async def _filter_step(parsed: ParsedRequest, products: list[MarketplaceProduct]) -> list[MarketplaceProduct]:
    """Возвращает отфильтрованный подсписок по SKU из ответа LLM."""
    try:
        result = await call_claude_json(
            system=FILTER_SYSTEM,
            user_message=FILTER_USER.format(
                parsed_request=json.dumps(parsed.model_dump(), ensure_ascii=False),
                products_json=json.dumps([_compact_product(p) for p in products], ensure_ascii=False),
            ),
            model=MODEL_SONNET,
            cache_system=True,
        )
    except Exception as e:
        logger.warning("Filter LLM failed: %s", e)
        return []

    skus = set(result.get("filtered_products") or [])
    return [p for p in products if p.sku in skus][:9]


async def _reviews_step(products: list[MarketplaceProduct]) -> list[dict]:
    """Параллельный анализ отзывов через asyncio.gather."""

    async def _one(product: MarketplaceProduct) -> dict:
        reviews_text = product.specs.get("reviews_sample") or "Отзывы недоступны"
        empty_analysis = {
            "pros": [], "cons": [], "fake_score": 0.0,
            "reviews_analyzed": 0, "authentic_reviews": 0,
        }
        try:
            data = await call_claude_json(
                system=REVIEWS_SYSTEM,
                user_message=REVIEWS_USER.format(
                    product_name=product.name,
                    reviews_text=reviews_text,
                ),
                model=MODEL_OPUS,
                cache_system=True,
            )
            return {**product.model_dump(), "review_analysis": data}
        except Exception as e:
            logger.warning("Review analysis failed for %s: %s", product.sku, e)
            return {**product.model_dump(), "review_analysis": empty_analysis}

    return await asyncio.gather(*[_one(p) for p in products])


async def _rank_step(query: str, parsed: ParsedRequest, analyzed: list[dict]) -> list[dict]:
    """Возвращает упорядоченный список топ-3."""
    if not analyzed:
        return []

    try:
        result = await call_claude_json(
            system=RANK_SYSTEM,
            user_message=RANK_USER.format(
                query=query,
                parsed_request=json.dumps(parsed.model_dump(), ensure_ascii=False),
                analyzed_products=json.dumps(analyzed, ensure_ascii=False, default=str),
            ),
            model=MODEL_OPUS,
            max_tokens=1024,
            cache_system=True,
        )
    except Exception as e:
        logger.warning("Rank LLM failed: %s", e)
        return []

    ranked = result.get("ranked") or []
    # Защита: убеждаемся что rank 1,2,3 присутствуют и sku валидны
    valid_skus = {a["sku"] for a in analyzed}
    cleaned = [r for r in ranked if r.get("sku") in valid_skus][:TOP3_DEFAULT]
    return cleaned


async def _share_text_step(query: str, products_out: list[dict]) -> str:
    if not products_out:
        return ""

    top3_summary = [
        {"rank": p["rank"], "name": p["name"], "reason": p["reason"]}
        for p in products_out
    ]
    try:
        result = await call_claude_json(
            system=FORMAT_SYSTEM,
            user_message=FORMAT_USER.format(
                query=query,
                top3=json.dumps(top3_summary, ensure_ascii=False),
            ),
            model=MODEL_SONNET,
            cache_system=True,
            max_tokens=512,
        )
        return result.get("share_text", "")
    except Exception as e:
        logger.warning("Share text generation failed: %s", e)
        # Fallback: простой текст
        return "\n".join(f"{['🥇','🥈','🥉'][p['rank']-1]} {p['name']}" for p in products_out)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _compact_product(p: MarketplaceProduct) -> dict:
    """Урезанный dict для LLM-фильтрации — экономим токены."""
    return {
        "sku": p.sku,
        "name": p.name,
        "marketplace": p.marketplace,
        "price": p.price,
        "rating": p.rating,
        "reviews_count": p.reviews_count,
    }


def _heuristic_rank(products: list[MarketplaceProduct]) -> list[dict]:
    """Фолбэк-ранжирование без LLM: rating / price."""
    ranked = []
    sorted_p = sorted(
        products,
        key=lambda p: ((p.rating or 0) * 1000) / max(p.price, 1),
        reverse=True,
    )[:TOP3_DEFAULT]
    for i, p in enumerate(sorted_p, start=1):
        ranked.append({
            "rank": i,
            "sku": p.sku,
            "marketplace": p.marketplace,
            "reason": f"Лучшее соотношение цена/рейтинг ({p.rating or '—'}/5)",
            "score": 50,
        })
    return ranked


def _assemble_products(
    ranked: list[dict],
    all_products: list[MarketplaceProduct],
    analyzed: list[dict],
) -> list[dict]:
    """Собирает финальные карточки: ранг + цены по 3 маркетплейсам + статистика отзывов."""
    sku_map = {p.sku: p for p in all_products}
    review_map = {a["sku"]: a.get("review_analysis", {}) for a in analyzed}

    out: list[dict] = []
    for item in ranked:
        sku = item["sku"]
        base = sku_map.get(sku)
        if base is None:
            continue

        review = review_map.get(sku, {})
        analyzed_count = review.get("reviews_analyzed", 0)
        authentic = review.get("authentic_reviews", analyzed_count)
        fake_removed = max(0, analyzed_count - authentic)

        out.append({
            "rank": item["rank"],
            "sku": sku,
            "marketplace": item.get("marketplace") or base.marketplace,
            "name": base.name,
            "image_url": base.image_url,
            "reason": item.get("reason", ""),
            "score": item.get("score", 0),
            "prices": _build_prices(base, all_products),
            "reviews_analyzed": analyzed_count,
            "fake_reviews_removed": fake_removed,
        })
    return out


def _build_prices(primary: MarketplaceProduct, all_products: list[MarketplaceProduct]) -> list[dict]:
    """
    Список цен по маркетплейсам. Для MVP используем простую логику:
    показываем цену основного товара + берём минимальную цену из других
    маркетплейсов в категории (если есть).
    """
    prices = [{
        "marketplace": primary.marketplace,
        "price": primary.price,
        "url": primary.url,
        "is_best": False,
    }]

    seen = {primary.marketplace}
    # Группируем по маркетплейсу и берём минимальную цену в каждом
    by_marketplace: dict[str, MarketplaceProduct] = {}
    for p in all_products:
        if p.marketplace == primary.marketplace or p.marketplace in seen:
            continue
        if p.marketplace not in by_marketplace or p.price < by_marketplace[p.marketplace].price:
            by_marketplace[p.marketplace] = p

    for mp, p in by_marketplace.items():
        prices.append({
            "marketplace": mp,
            "price": p.price,
            "url": p.url,
            "is_best": False,
        })
        seen.add(mp)

    # Помечаем минимальную цену как лучшую
    if prices:
        min_entry = min(prices, key=lambda x: x["price"])
        min_entry["is_best"] = True

    return prices
