import pytest
from unittest.mock import AsyncMock, patch


async def _auth(client) -> str:
    resp = await client.post("/api/v1/auth/telegram", json={"init_data": "dev_mode"})
    return resp.json()["token"]


MOCK_PIPELINE_RESULT = {
    "parsed_request": {"category": "наушники", "budget_max": 15000, "requirements": [], "keywords": ["наушники"]},
    "products": [
        {
            "rank": 1, "sku": "ozon-mock-0", "marketplace": "ozon",
            "name": "Наушники Mock 1", "image_url": None,
            "reason": "Лучшее соотношение цена/качество",
            "score": 90,
            "prices": [{"marketplace": "ozon", "price": 9990, "url": "https://ozon.ru/1", "is_best": True}],
            "reviews_analyzed": 50, "fake_reviews_removed": 2,
        }
    ],
    "share_text": "Нашёл наушники до 15к",
    "needs_clarification": False,
}


@pytest.mark.asyncio
async def test_search_requires_auth(client):
    resp = await client.post("/api/v1/search", json={"query": "наушники"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_search_returns_results(client):
    token = await _auth(client)

    with patch("app.api.search.run_search_pipeline", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = MOCK_PIPELINE_RESULT
        resp = await client.post(
            "/api/v1/search",
            json={"query": "наушники до 15к"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "наушники до 15к"
    assert len(data["products"]) == 1
    assert data["needs_clarification"] is False


@pytest.mark.asyncio
async def test_search_free_limit(client):
    """После 3 запросов возвращается 402."""
    token = await _auth(client)
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.api.search.run_search_pipeline", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = MOCK_PIPELINE_RESULT
        for _ in range(3):
            resp = await client.post("/api/v1/search", json={"query": "тест"}, headers=headers)
            assert resp.status_code == 200

        resp4 = await client.post("/api/v1/search", json={"query": "тест"}, headers=headers)
        assert resp4.status_code == 402
        assert resp4.json()["detail"]["paywall"] is True


@pytest.mark.asyncio
async def test_search_history(client):
    token = await _auth(client)
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.api.search.run_search_pipeline", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = MOCK_PIPELINE_RESULT
        await client.post("/api/v1/search", json={"query": "наушники"}, headers=headers)

    hist = await client.get("/api/v1/search/history", headers=headers)
    assert hist.status_code == 200
    assert len(hist.json()) == 1
    assert hist.json()[0]["raw_text"] == "наушники"
