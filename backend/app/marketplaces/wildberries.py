"""
Wildberries адаптер.

WB не имеет официального публичного API для поиска товаров покупателем,
но мобильное приложение и сайт используют публично доступные endpoints:
  - search.wb.ru   — поиск
  - card.wb.ru     — детали товара (включая цены)
  - feedbacks*.wb.ru — отзывы

CPA: через Admitad — оборачиваем ссылку в deeplink.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from app.ai.schemas import MarketplaceProduct, ParsedRequest
from app.config import settings
from app.marketplaces._http import MarketplaceClient
from app.marketplaces.base import BaseMarketplaceAdapter

logger = logging.getLogger(__name__)

WB_SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v9/search"
WB_DETAIL_URL = "https://card.wb.ru/cards/v2/detail"

# Российский dest по умолчанию (Москва). Можно менять под пользователя.
DEFAULT_DEST = -1257786


def _wb_image_url(product_id: int) -> str:
    """
    Строит URL картинки WB по ID товара.
    Формула basket-номера известна из публичных source maps WB.
    """
    vol = product_id // 100000
    part = product_id // 1000
    # Границы basket-N для текущих ID (актуально на 2024-2026).
    # Если попадаем за пределы — используем дефолтный (новые товары).
    if vol < 144:        basket = 1
    elif vol < 288:      basket = 2
    elif vol < 432:      basket = 3
    elif vol < 720:      basket = 4
    elif vol < 1008:     basket = 5
    elif vol < 1062:     basket = 6
    elif vol < 1115:     basket = 7
    elif vol < 1169:     basket = 8
    elif vol < 1313:     basket = 9
    elif vol < 1601:     basket = 10
    elif vol < 1655:     basket = 11
    elif vol < 1856:     basket = 12
    elif vol < 2204:     basket = 13
    elif vol < 2400:     basket = 14
    elif vol < 2625:     basket = 15
    elif vol < 2837:     basket = 16
    elif vol < 3050:     basket = 17
    elif vol < 3263:     basket = 18
    elif vol < 3477:     basket = 19
    else:                basket = 20  # для новых товаров; URL может вернуть 404 — нестрашно
    return f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/1.webp"


def _price_from_product(raw: dict[str, Any]) -> int | None:
    """
    Возвращает финальную цену в рублях.
    WB цены приходят в копейках (×100), есть несколько путей:
      sizes[0].price.{total,product,basic,logistics}  — новая структура v9/v2
      salePriceU / priceU                              — старая структура (fallback)
    """
    sizes = raw.get("sizes") or []
    if sizes:
        price = (sizes[0].get("price") or {})
        # `total` — что увидит покупатель с учётом всех скидок
        for key in ("total", "product", "basic"):
            v = price.get(key)
            if isinstance(v, (int, float)) and v > 0:
                return int(v) // 100  # копейки → рубли

    for key in ("salePriceU", "priceU"):
        v = raw.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return int(v) // 100
    return None


def _reviews_sample(raw: dict[str, Any]) -> str:
    """
    На странице поиска отзывы не отдаются. Здесь возвращаем placeholder из
    publicly доступных полей (rating + feedbacks count) — Claude этого хватит
    для базового анализа. Полные отзывы тянутся отдельно при необходимости.
    """
    rating = raw.get("rating") or raw.get("reviewRating")
    feedbacks = raw.get("feedbacks") or raw.get("nmReviewRating")
    parts = []
    if rating:
        parts.append(f"Средняя оценка: {rating}")
    if feedbacks:
        parts.append(f"Количество отзывов: {feedbacks}")
    return ". ".join(parts) or "Отзывы недоступны"


class WildberriesAdapter(BaseMarketplaceAdapter):
    name = "wildberries"

    async def search(self, parsed: ParsedRequest, limit: int = 10) -> list[MarketplaceProduct]:
        query = " ".join(parsed.keywords) or parsed.category
        if not query:
            return []

        try:
            async with MarketplaceClient() as http:
                data = await http.get_json(
                    WB_SEARCH_URL,
                    params={
                        "ab_testing": "false",
                        "appType": "1",
                        "curr": "rub",
                        "dest": DEFAULT_DEST,
                        "query": query,
                        "resultset": "catalog",
                        "sort": "popular",
                        "spp": "30",
                        "suppressSpellcheck": "false",
                    },
                )
        except Exception as e:
            logger.warning("WB HTTP request failed: %s, using mock", e)
            return self._mock_products(parsed)

        if not isinstance(data, dict):
            logger.warning("WB returned non-dict, falling back to mock")
            return self._mock_products(parsed)

        products = (data.get("data") or {}).get("products") or []
        if not products:
            logger.info("WB returned no products for %r, using mock", query)
            return self._mock_products(parsed)

        result: list[MarketplaceProduct] = []
        for raw in products[:limit]:
            try:
                product = self._parse_product(raw, parsed)
                if product is None:
                    continue
                result.append(product)
            except Exception as e:
                logger.warning("Failed to parse WB product %s: %s", raw.get("id"), e)
                continue

        # Фильтр бюджета
        if parsed.budget_max:
            result = [p for p in result if p.price <= parsed.budget_max]
        if parsed.budget_min:
            result = [p for p in result if p.price >= parsed.budget_min]

        return result

    def _parse_product(self, raw: dict[str, Any], parsed: ParsedRequest) -> MarketplaceProduct | None:
        product_id = raw.get("id")
        if not product_id:
            return None

        price = _price_from_product(raw)
        if price is None:
            return None

        name_parts = []
        brand = raw.get("brand")
        if brand:
            name_parts.append(brand)
        name_parts.append(raw.get("name") or "")
        name = " ".join(p for p in name_parts if p).strip()

        url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"

        return MarketplaceProduct(
            sku=str(product_id),
            name=name or f"WB товар {product_id}",
            marketplace="wildberries",
            price=price,
            rating=raw.get("rating") or raw.get("reviewRating"),
            reviews_count=raw.get("feedbacks") or raw.get("nmReviewRating"),
            image_url=_wb_image_url(product_id),
            url=self._make_cpa_url(url),
            specs={
                "brand": brand,
                "supplier": raw.get("supplier"),
                "reviews_sample": _reviews_sample(raw),
            },
        )

    def _make_cpa_url(self, original_url: str) -> str:
        """Оборачивает ссылку WB через Admitad deeplink."""
        if not settings.admitad_api_key:
            return original_url
        encoded = quote(original_url, safe="")
        subid = settings.wb_cpa_subid or ""
        suffix = f"&subid={subid}" if subid else ""
        return f"https://ad.admitad.com/g/{settings.admitad_api_key}/?ulp={encoded}{suffix}"

    async def get_current_price(self, sku: str) -> int | None:
        """
        Получить актуальную цену товара по SKU.
        Используется price_tracker воркером.
        """
        try:
            nm_id = int(sku)
        except ValueError:
            return None

        async with MarketplaceClient() as http:
            data = await http.get_json(
                WB_DETAIL_URL,
                params={
                    "appType": "1",
                    "curr": "rub",
                    "dest": DEFAULT_DEST,
                    "nm": nm_id,
                    "spp": "30",
                },
            )

        if not isinstance(data, dict):
            return None
        products = (data.get("data") or {}).get("products") or []
        if not products:
            return None
        return _price_from_product(products[0])

    def _mock_products(self, parsed: ParsedRequest) -> list[MarketplaceProduct]:
        keywords = " ".join(parsed.keywords[:2]) or parsed.category
        return [
            MarketplaceProduct(
                sku=f"wb-mock-{i}",
                name=f"{parsed.category.title()} {keywords} WB (Mock {i})",
                marketplace="wildberries",
                price=(parsed.budget_max or 15000) - i * 800 - 200,
                rating=4.3 - i * 0.15,
                reviews_count=200 - i * 30,
                url=f"https://www.wildberries.ru/catalog/mock-{i}/detail.aspx",
                image_url=None,
                specs={"reviews_sample": "Mock-данные. Реальный API недоступен."},
            )
            for i in range(3)
        ]
