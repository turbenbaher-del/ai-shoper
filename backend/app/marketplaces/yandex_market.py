"""
Яндекс.Маркет адаптер.

Стратегия:
  1. Если задан YANDEX_MARKET_OAUTH — используем Partner API (рабочий, официальный).
  2. Иначе — скрапим market.yandex.ru/search, извлекаем __NEXT_DATA__ с нормализованными
     сущностями (Redux-стиль: entities.product + коллекция ids).
  3. Фолбэк на мок.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import quote

from app.ai.schemas import MarketplaceProduct, ParsedRequest
from app.config import settings
from app.marketplaces._http import MarketplaceClient
from app.marketplaces.base import BaseMarketplaceAdapter

logger = logging.getLogger(__name__)

YANDEX_PARTNER_API = "https://api.partner.market.yandex.ru"
YM_SEARCH_URL = "https://market.yandex.ru/search"

YM_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_YM_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://market.yandex.ru/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}


def _ym_image_url(raw: dict[str, Any]) -> str | None:
    """Берём первую фотографию товара из структуры YM."""
    photos = raw.get("photos") or raw.get("pictures") or []
    if not photos:
        return None
    first = photos[0] if isinstance(photos, list) else None
    if not first:
        return None
    # Структура: {original: {url: "//avatars.mds.yandex.net/..."}}
    url = (
        (first.get("original") or {}).get("url")
        or first.get("url")
        or first.get("thumbnails", [{}])[0].get("url") if isinstance(first.get("thumbnails"), list) else None
    )
    if not url:
        return None
    if url.startswith("//"):
        url = "https:" + url
    return url


def _ym_price(raw: dict[str, Any]) -> int | None:
    """Извлекает цену из разных мест структуры product."""
    prices = raw.get("prices") or {}
    # Пробуем разные поля
    for key in ("min", "avg", "value"):
        v = prices.get(key)
        if isinstance(v, (int, float)) and v > 0:
            return int(v)
    # Альтернативная структура
    price_obj = raw.get("price") or {}
    v = price_obj.get("value") or price_obj.get("min")
    if isinstance(v, (int, float)) and v > 0:
        return int(v)
    return None


def _ym_rating(raw: dict[str, Any]) -> float | None:
    r = raw.get("rating") or {}
    if isinstance(r, dict):
        v = r.get("value") or r.get("avg")
        return float(v) if v else None
    if isinstance(r, (int, float)):
        return float(r)
    return None


def _ym_reviews(raw: dict[str, Any]) -> int | None:
    r = raw.get("rating") or {}
    if isinstance(r, dict):
        c = r.get("count") or r.get("reviewCount")
        return int(c) if c else None
    return raw.get("reviewCount") or raw.get("opinionsCount")


def _ym_url(raw: dict[str, Any]) -> str:
    pid = raw.get("id") or raw.get("modelId")
    slug = raw.get("slug") or ""
    if pid and slug:
        return f"https://market.yandex.ru/product--{slug}/{pid}"
    if pid:
        return f"https://market.yandex.ru/product/{pid}"
    return "https://market.yandex.ru/"


class YandexMarketAdapter(BaseMarketplaceAdapter):
    name = "yandex_market"

    async def search(self, parsed: ParsedRequest, limit: int = 10) -> list[MarketplaceProduct]:
        if settings.yandex_market_oauth:
            return await self._search_partner_api(parsed, limit)
        return await self._search_scrape(parsed, limit)

    # ── Официальный Partner API ────────────────────────────────────────────

    async def _search_partner_api(self, parsed: ParsedRequest, limit: int) -> list[MarketplaceProduct]:
        query = " ".join(parsed.keywords) or parsed.category
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
            logger.info("Yandex.Market Partner API unavailable, trying scrape")
            return await self._search_scrape(parsed, limit)

        offers = (data.get("result") or {}).get("offers") or []
        result = []
        for raw in offers[:limit]:
            try:
                p = self._build_partner_product(raw)
                if p:
                    result.append(p)
            except Exception as e:
                logger.warning("Failed to parse YM partner offer: %s", e)

        if parsed.budget_max:
            result = [p for p in result if p.price <= parsed.budget_max]
        if parsed.budget_min:
            result = [p for p in result if p.price >= parsed.budget_min]

        return result or self._mock_products(parsed)

    def _build_partner_product(self, raw: dict[str, Any]) -> MarketplaceProduct | None:
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
        if pictures:
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
            specs={"vendor": raw.get("vendor"), "reviews_sample": "Отзывы на странице товара"},
        )

    # ── Неофициальный скрапинг market.yandex.ru ───────────────────────────

    async def _search_scrape(self, parsed: ParsedRequest, limit: int) -> list[MarketplaceProduct]:
        query = " ".join(parsed.keywords) or parsed.category
        params: dict[str, Any] = {"text": query, "viewtype": "list"}
        if parsed.budget_max:
            params["priceto"] = parsed.budget_max
        if parsed.budget_min:
            params["pricefrom"] = parsed.budget_min

        try:
            async with MarketplaceClient(ua=YM_UA, timeout=15.0) as http:
                resp = await http.request("GET", YM_SEARCH_URL, params=params, headers=_YM_HEADERS)
        except Exception as e:
            logger.warning("YM scrape request failed: %s, using mock", e)
            return self._mock_products(parsed)

        if resp is None or resp.status_code != 200:
            logger.info("YM scrape returned %s, using mock", resp.status_code if resp else "None")
            return self._mock_products(parsed)

        products = self._parse_next_data(resp.text, limit)
        if not products:
            logger.info("YM __NEXT_DATA__ parse yielded nothing, using mock")
            return self._mock_products(parsed)

        if parsed.budget_max:
            products = [p for p in products if p.price <= parsed.budget_max]
        if parsed.budget_min:
            products = [p for p in products if p.price >= parsed.budget_min]

        return products or self._mock_products(parsed)

    def _parse_next_data(self, html: str, limit: int) -> list[MarketplaceProduct]:
        match = re.search(
            r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        props = data.get("props", {}).get("pageProps", {})

        # YM хранит товары нормализованно: entities.product[id] + коллекция ids
        initial_state = props.get("initialState") or props.get("reduxState") or {}
        entities = initial_state.get("entities") or {}
        products_map: dict = entities.get("product") or entities.get("model") or {}

        # Список ID из результатов поиска
        collections = initial_state.get("collections") or {}
        search_col = collections.get("search") or collections.get("searchResult") or {}
        ids = search_col.get("ids") or search_col.get("data") or []

        result = []
        for pid in ids[:limit]:
            raw = products_map.get(str(pid)) or products_map.get(pid)
            if not raw:
                continue
            p = self._build_scraped_product(raw)
            if p:
                result.append(p)

        # Фолбэк: иногда данные лежат прямо в pageProps
        if not result:
            items = (
                (props.get("data") or {}).get("search", {}).get("results") or
                (props.get("searchResult") or {}).get("items") or
                []
            )
            for raw in items[:limit]:
                p = self._build_scraped_product(raw)
                if p:
                    result.append(p)

        return result

    def _build_scraped_product(self, raw: dict[str, Any]) -> MarketplaceProduct | None:
        pid = raw.get("id") or raw.get("modelId")
        if not pid:
            return None
        price = _ym_price(raw)
        if not price:
            return None
        name = (
            raw.get("name")
            or (raw.get("titles") or {}).get("raw")
            or (raw.get("titles") or {}).get("short")
        )
        if not name:
            return None
        return MarketplaceProduct(
            sku=str(pid),
            name=name,
            marketplace="yandex_market",
            price=price,
            rating=_ym_rating(raw),
            reviews_count=_ym_reviews(raw),
            image_url=_ym_image_url(raw),
            url=self._make_cpa_url(_ym_url(raw)),
            specs={
                "vendor": (raw.get("vendor") or {}).get("name") or raw.get("vendorName"),
                "reviews_sample": "Отзывы на странице товара",
            },
        )

    def _make_cpa_url(self, original_url: str) -> str:
        sep = "&" if "?" in original_url else "?"
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
        seeds = [f"ym-{parsed.category}-{i}" for i in range(3)]
        return [
            MarketplaceProduct(
                sku=f"ym-mock-{i}",
                name=f"{parsed.category.title()} {keywords} Я.Маркет (Mock {i})",
                marketplace="yandex_market",
                price=(parsed.budget_max or 15000) - i * 1200 + 100,
                rating=4.4 - i * 0.12,
                reviews_count=120 - i * 15,
                url=f"https://market.yandex.ru/product/mock-{i}",
                image_url=f"https://picsum.photos/seed/{seeds[i]}/300/300",
                specs={"reviews_sample": "Mock-данные. API недоступен."},
            )
            for i in range(3)
        ]
