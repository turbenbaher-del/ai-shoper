"""Тесты адаптеров маркетплейсов на парсинг и нормализацию данных."""
import pytest

from app.ai.schemas import ParsedRequest
from app.marketplaces.wildberries import WildberriesAdapter, _wb_image_url, _price_from_product
from app.marketplaces.ozon import OzonAdapter


def test_wb_image_url_low_id():
    url = _wb_image_url(1000)
    assert url.startswith("https://basket-")
    assert "1000" in url


def test_wb_image_url_high_id():
    """Для очень высоких ID должен возвращать дефолтный basket-20."""
    url = _wb_image_url(450_000_000)
    assert "basket-20" in url


def test_wb_price_v9_format():
    raw = {
        "sizes": [{"price": {"total": 1_299_000, "product": 1_299_000, "basic": 1_500_000}}]
    }
    assert _price_from_product(raw) == 12990


def test_wb_price_legacy_format():
    raw = {"salePriceU": 999_000, "priceU": 1_200_000}
    assert _price_from_product(raw) == 9990


def test_wb_price_missing():
    assert _price_from_product({}) is None
    assert _price_from_product({"sizes": []}) is None


def test_wb_mock_respects_budget():
    parsed = ParsedRequest(
        category="наушники",
        budget_max=15000,
        keywords=["наушники"],
    )
    adapter = WildberriesAdapter()
    mocks = adapter._mock_products(parsed)
    assert len(mocks) == 3
    for m in mocks:
        assert m.marketplace == "wildberries"
        assert m.price <= 15000


def test_wb_cpa_url_without_admitad():
    """Без ADMITAD_API_KEY ссылка остаётся оригинальной."""
    from app.config import settings
    original_key = settings.admitad_api_key
    settings.admitad_api_key = ""

    try:
        adapter = WildberriesAdapter()
        url = adapter._make_cpa_url("https://www.wildberries.ru/catalog/123/detail.aspx")
        assert "ad.admitad.com" not in url
        assert "wildberries.ru" in url
    finally:
        settings.admitad_api_key = original_key


def test_wb_cpa_url_with_admitad():
    from app.config import settings
    original_key = settings.admitad_api_key
    settings.admitad_api_key = "1234567"

    try:
        adapter = WildberriesAdapter()
        url = adapter._make_cpa_url("https://www.wildberries.ru/catalog/123/detail.aspx")
        assert "ad.admitad.com" in url
        assert "1234567" in url
    finally:
        settings.admitad_api_key = original_key


def test_ozon_cpa_url_with_client_id():
    from app.config import settings
    original = settings.ozon_client_id
    settings.ozon_client_id = "partner-abc"

    try:
        adapter = OzonAdapter()
        url = adapter._make_cpa_url("https://www.ozon.ru/product/123")
        assert "partner_id=partner-abc" in url
    finally:
        settings.ozon_client_id = original
