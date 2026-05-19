"""
Ozon адаптер.

Ozon не предоставляет публичный Search API для покупателей. У них есть:
  1. Seller API (api-seller.ozon.ru) — только для продавцов, нам не подходит
  2. Affiliate Partners API — генерация партнёрских коротких ссылок
  3. composer-api.bx — внутренний API сайта, используется фронтом

Для MVP используем (3) — composer-api возвращает JSON с виджетами страницы поиска.
Парсер хрупкий (Ozon может менять структуру), потому при ошибке падаем на mock.

CPA: Если включён Affiliate-аккаунт, заворачиваем ссылки через API.
В простом случае — добавляем `?partner_id={OZON_CLIENT_ID}` в URL.
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

from app.ai.schemas import MarketplaceProduct, ParsedRequest
from app.config import settings
from app.marketplaces._http import MarketplaceClient
from app.marketplaces.base import BaseMarketplaceAdapter

logger = logging.getLogger(__name__)

OZON_BASE = "https://www.ozon.ru"
OZON_COMPOSER_URL = f"{OZON_BASE}/api/composer-api.bx/page/json/v2"


class OzonAdapter(BaseMarketplaceAdapter):
    name = "ozon"

    async def search(self, parsed: ParsedRequest, limit: int = 10) -> list[MarketplaceProduct]:
        query = " ".join(parsed.keywords) or parsed.category
        if not query:
            return []

        # Композер принимает URL внутреннего маршрута. Параметры — как в строке адреса.
        url_param = "/category/" if False else "/search/"
        inner_qs = urlencode({"text": query, "from_global": "true"})
        composer_params = {
            "url": f"{url_param}?{inner_qs}",
            "layout_container": "categorySearchMegapagination",
            "layout_page_index": "1",
        }

        async with MarketplaceClient(timeout=15.0) as http:
            data = await http.get_json(
                OZON_COMPOSER_URL,
                params=composer_params,
                headers={
                    "Accept-Language": "ru-RU,ru;q=0.9",
                    "Referer": f"{OZON_BASE}/search/?text={query}",
                    "x-o3-app-name": "dweb_client",
                },
            )

        products = self._extract_products(data) if isinstance(data, dict) else []
        if not products:
            logger.info("Ozon returned no products for %r, using mock", query)
            return self._mock_products(parsed)

        result: list[MarketplaceProduct] = []
        for raw in products[:limit]:
            try:
                p = self._build_product(raw)
                if p:
                    result.append(p)
            except Exception as e:
                logger.warning("Failed to parse Ozon product: %s", e)

        if parsed.budget_max:
            result = [p for p in result if p.price <= parsed.budget_max]
        if parsed.budget_min:
            result = [p for p in result if p.price >= parsed.budget_min]

        return result or self._mock_products(parsed)

    def _extract_products(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        composer-api возвращает JSON с разделом `widgetStates`. Карточки лежат
        в виджете `searchResultsV2-...` как сериализованный JSON.
        Структура нестабильна — обрабатываем максимально оборонительно.
        """
        widget_states = data.get("widgetStates") or {}
        products: list[dict[str, Any]] = []

        for key, raw_state in widget_states.items():
            if not key.startswith("searchResultsV2") and not key.startswith("tileGridDesktop"):
                continue
            try:
                import json
                state = json.loads(raw_state) if isinstance(raw_state, str) else raw_state
            except Exception:
                continue
            items = state.get("items") or []
            products.extend(items)

        return products

    def _build_product(self, raw: dict[str, Any]) -> MarketplaceProduct | None:
        # У Ozon карточек разные форматы — попытка достать поля без падения.
        sku = str(raw.get("sku") or raw.get("id") or "")
        if not sku:
            return None

        # Цена: ищем в `mainState` → `priceV2` или `atom.priceV2.price`
        price = self._extract_price(raw)
        if price is None:
            return None

        # Название: главное состояние или атом textSmall
        name = self._extract_name(raw)
        if not name:
            return None

        image_url = self._extract_image(raw)
        product_url = raw.get("link") or raw.get("action", {}).get("link")
        if product_url and not product_url.startswith("http"):
            product_url = f"{OZON_BASE}{product_url}"
        if not product_url:
            product_url = f"{OZON_BASE}/product/{sku}/"

        return MarketplaceProduct(
            sku=sku,
            name=name,
            marketplace="ozon",
            price=price,
            rating=self._extract_rating(raw),
            reviews_count=self._extract_reviews_count(raw),
            image_url=image_url,
            url=self._make_cpa_url(product_url),
            specs={"reviews_sample": "Отзывы доступны на странице товара"},
        )

    def _iter_atoms(self, raw: dict[str, Any]):
        """Возвращает все атомы из mainState (с фолбэками)."""
        ms = raw.get("mainState") or raw.get("cellTrackingInfo") or []
        if isinstance(ms, list):
            for cell in ms:
                atom = cell.get("atom") or {}
                yield atom.get("type"), atom

    def _extract_price(self, raw: dict[str, Any]) -> int | None:
        for atype, atom in self._iter_atoms(raw):
            if atype in ("priceV2", "price"):
                # price бывает строкой типа "12 990 ₽"
                price_block = (atom.get("priceV2") or atom).get("price") if atom else None
                if isinstance(price_block, list) and price_block:
                    text = price_block[0].get("text", "")
                    digits = "".join(c for c in text if c.isdigit())
                    if digits:
                        return int(digits)
                price_str = atom.get("price")
                if isinstance(price_str, str):
                    digits = "".join(c for c in price_str if c.isdigit())
                    if digits:
                        return int(digits)
        return None

    def _extract_name(self, raw: dict[str, Any]) -> str | None:
        for atype, atom in self._iter_atoms(raw):
            if atype in ("textSmall", "textAtom"):
                text = atom.get("textSmall", {}).get("text") or atom.get("text")
                if isinstance(text, str) and len(text) > 10:
                    return text
        return raw.get("title")

    def _extract_image(self, raw: dict[str, Any]) -> str | None:
        for atype, atom in self._iter_atoms(raw):
            if atype == "image" or "image" in atype.lower() if atype else False:
                img = atom.get("image", {}).get("link") or atom.get("link")
                if isinstance(img, str) and img.startswith("http"):
                    return img
        return None

    def _extract_rating(self, raw: dict[str, Any]) -> float | None:
        for atype, atom in self._iter_atoms(raw):
            if atype in ("labelList", "rating"):
                # Ищем "4.5" в текстовых полях
                items = atom.get("labelList", {}).get("items") or []
                for it in items:
                    title = it.get("title", "")
                    try:
                        # Часто формат "4.5 · 1234 отзыва"
                        first = title.split()[0].replace(",", ".")
                        return float(first)
                    except (ValueError, IndexError):
                        continue
        return None

    def _extract_reviews_count(self, raw: dict[str, Any]) -> int | None:
        for atype, atom in self._iter_atoms(raw):
            if atype == "labelList":
                items = atom.get("labelList", {}).get("items") or []
                for it in items:
                    title = it.get("title", "")
                    if "отзыв" in title.lower():
                        digits = "".join(c for c in title if c.isdigit())
                        if digits:
                            return int(digits)
        return None

    def _make_cpa_url(self, original_url: str) -> str:
        if not settings.ozon_client_id:
            return original_url
        sep = "&" if "?" in original_url else "?"
        return f"{original_url}{sep}partner_id={settings.ozon_client_id}"

    async def get_current_price(self, sku: str) -> int | None:
        """
        Получить актуальную цену товара по SKU.
        Используется price_tracker воркером.
        """
        async with MarketplaceClient(timeout=10.0) as http:
            data = await http.get_json(
                OZON_COMPOSER_URL,
                params={"url": f"/product/{sku}/"},
                headers={"x-o3-app-name": "dweb_client"},
            )
        if not isinstance(data, dict):
            return None

        # Цена лежит в widget webPrice / webStickyProducts
        widget_states = data.get("widgetStates") or {}
        for key, raw_state in widget_states.items():
            if "webPrice" not in key and "webStickyProducts" not in key:
                continue
            try:
                import json
                state = json.loads(raw_state) if isinstance(raw_state, str) else raw_state
            except Exception:
                continue
            price_text = (state.get("cardPrice") or {}).get("price") or state.get("price")
            if isinstance(price_text, str):
                digits = "".join(c for c in price_text if c.isdigit())
                if digits:
                    return int(digits)
        return None

    def _mock_products(self, parsed: ParsedRequest) -> list[MarketplaceProduct]:
        keywords = " ".join(parsed.keywords[:2]) or parsed.category
        return [
            MarketplaceProduct(
                sku=f"ozon-mock-{i}",
                name=f"{parsed.category.title()} {keywords} (Mock {i})",
                marketplace="ozon",
                price=(parsed.budget_max or 15000) - i * 1000,
                rating=4.5 - i * 0.1,
                reviews_count=150 - i * 20,
                url=f"https://www.ozon.ru/product/mock-{i}",
                image_url=None,
                specs={"reviews_sample": "Mock-данные. Реальный API недоступен."},
            )
            for i in range(3)
        ]
