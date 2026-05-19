"""
Базовый интерфейс адаптера маркетплейса + точки входа `search_all_marketplaces`
и `get_price_by_marketplace`.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from app.ai.schemas import MarketplaceProduct, ParsedRequest

logger = logging.getLogger(__name__)


class BaseMarketplaceAdapter(ABC):
    name: str = ""

    @abstractmethod
    async def search(self, parsed: ParsedRequest, limit: int = 10) -> list[MarketplaceProduct]:
        ...

    async def get_current_price(self, sku: str) -> int | None:
        """Получить актуальную цену для отслеживания. Переопределить в адаптере."""
        return None

    def _make_cpa_url(self, original_url: str) -> str:
        return original_url


def _adapters() -> dict[str, BaseMarketplaceAdapter]:
    from app.marketplaces.ozon import OzonAdapter
    from app.marketplaces.wildberries import WildberriesAdapter
    from app.marketplaces.yandex_market import YandexMarketAdapter

    return {
        "ozon": OzonAdapter(),
        "wildberries": WildberriesAdapter(),
        "yandex_market": YandexMarketAdapter(),
    }


async def search_all_marketplaces(parsed: ParsedRequest) -> list[MarketplaceProduct]:
    """Параллельный поиск по всем маркетплейсам. Ошибки изолированы."""
    adapters = _adapters()

    async def _safe(adapter: BaseMarketplaceAdapter) -> list[MarketplaceProduct]:
        try:
            return await adapter.search(parsed)
        except Exception as e:
            logger.exception("Adapter %s failed: %s", adapter.name, e)
            return []

    results = await asyncio.gather(*[_safe(a) for a in adapters.values()])
    flat: list[MarketplaceProduct] = []
    for r in results:
        flat.extend(r)
    return flat


async def get_price_by_marketplace(marketplace: str, sku: str) -> int | None:
    """Получить актуальную цену конкретного товара (для price_tracker)."""
    adapter = _adapters().get(marketplace)
    if adapter is None:
        logger.warning("Unknown marketplace: %s", marketplace)
        return None
    try:
        return await adapter.get_current_price(sku)
    except Exception as e:
        logger.exception("get_current_price(%s, %s) failed: %s", marketplace, sku, e)
        return None
