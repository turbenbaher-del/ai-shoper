"""
Яндекс.Маркет адаптер.

У Я.Маркета нет публичного Search API. Есть:
  1. Partner API (api.partner.market.yandex.ru) — требует OAuth-токен партнёра
  2. Content API (бывший) — снят с поддержки 2022
  3. Мобильный API m.market.yandex.ru/api/... — неофициальный, периодически меняется

Для MVP:
  - если YANDEX_MARKET_OAUTH задан → используем Partner API report/products
  - иначе → mock-данные (Wizard of Oz режим из ТЗ 2.4)
"""
from __future__ import annotations

import logging
from typing import Any

from app.ai.schemas import MarketplaceProduct, ParsedRequest
from app.config import settings
from app.marketplaces._http import MarketplaceClient
from app.marketplaces.base import BaseMarketplaceAdapter

logger = logging.getLogger(__name__)

YANDEX_PARTNER_API = "https://api.partner.market.yandex.ru"


class YandexMarketAdapter(BaseMarketplaceAdapter):
    name = "yandex_market"

    async def search(self, parsed: ParsedRequest, limit: int = 10) -> list[MarketplaceProduct]:
        if not settings.yandex_market_oauth:
            return self._mock_products(parsed)

        query = " ".join(parsed.keywords) or parsed.category
        if not query:
            return []

        headers = {
            "Authorization": f"Bearer {settings.yandex_market_oauth}",
            "Content-Type": "application/json",
        }

        body: dict[str, Any] = {"query": query}
        if parsed.budget_min or parsed.budget_max:
            body["filterPrice"] = {
                "from": parsed.budget_min or 0,
                "to": parsed.budget_max or 10**9,
            }

        async with MarketplaceClient() as http:
            data = await http.post_json(
                f"{YANDEX_PARTNER_API}/businesses/offers",
                body=body,
                headers=headers,
            )

        if not isinstance(data, dict):
            logger.info("Yandex.Market API unavailable, using mock")
            return self._mock_products(parsed)

        offers = (data.get("result") or {}).get("offers") or []
        if not offers:
            return []

        result: list[MarketplaceProduct] = []
        for raw in offers[:limit]:
            try:
                p = self._build_product(raw)
                if p:
                    result.append(p)
            except Exception as e:
                logger.warning("Failed to parse Yandex.Market offer: %s", e)

        if parsed.budget_max:
            result = [p for p in result if p.price <= parsed.budget_max]
        if parsed.budget_min:
            result = [p for p in result if p.price >= parsed.budget_min]

        return result

    def _build_product(self, raw: dict[str, Any]) -> MarketplaceProduct | None:
        offer_id = raw.get("offerId") or raw.get("shopSku")
        if not offer_id:
            return None

        price = raw.get("price") or raw.get("basicPrice", {}).get("value")
        if not isinstance(price, (int, float)):
            return None

        name = raw.get("name") or raw.get("title")
        if not name:
            return None

        url = raw.get("url") or f"https://market.yandex.ru/product/{offer_id}"
        image_url = None
        pictures = raw.get("pictures") or []
        if pictures and isinstance(pictures, list):
            first = pictures[0]
            image_url = first if isinstance(first, str) else first.get("url")

        return MarketplaceProduct(
            sku=str(offer_id),
            name=name,
            marketplace="yandex_market",
            price=int(price),
            rating=raw.get("rating"),
            reviews_count=raw.get("reviewsCount") or raw.get("opinionsCount"),
            image_url=image_url,
            url=self._make_cpa_url(url),
            specs={
                "vendor": raw.get("vendor"),
                "reviews_sample": "Отзывы на странице товара",
            },
        )

    def _make_cpa_url(self, original_url: str) -> str:
        """Добавляет clid/mclid партнёрской программы Яндекс.Маркет."""
        sep = "&" if "?" in original_url else "?"
        # clid 1003 — стандартный код партнёра для перехода с Я.Партнёрки
        return f"{original_url}{sep}clid=1003&mclid=1003"

    async def get_current_price(self, sku: str) -> int | None:
        if not settings.yandex_market_oauth:
            return None
        headers = {"Authorization": f"Bearer {settings.yandex_market_oauth}"}
        async with MarketplaceClient() as http:
            data = await http.get_json(
                f"{YANDEX_PARTNER_API}/offer-prices",
                params={"offerId": sku},
                headers=headers,
            )
        if not isinstance(data, dict):
            return None
        offers = (data.get("result") or {}).get("offers") or []
        if not offers:
            return None
        price = offers[0].get("price", {}).get("value")
        return int(price) if isinstance(price, (int, float)) else None

    def _mock_products(self, parsed: ParsedRequest) -> list[MarketplaceProduct]:
        keywords = " ".join(parsed.keywords[:2]) or parsed.category
        return [
            MarketplaceProduct(
                sku=f"ym-mock-{i}",
                name=f"{parsed.category.title()} {keywords} Я.Маркет (Mock {i})",
                marketplace="yandex_market",
                price=(parsed.budget_max or 15000) - i * 1200 + 100,
                rating=4.4 - i * 0.12,
                reviews_count=120 - i * 15,
                url=f"https://market.yandex.ru/product/mock-{i}",
                image_url=None,
                specs={"reviews_sample": "Mock-данные. Требуется YANDEX_MARKET_OAUTH."},
            )
            for i in range(3)
        ]
