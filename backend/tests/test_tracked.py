import pytest


async def _auth(client) -> str:
    resp = await client.post("/api/v1/auth/telegram", json={"init_data": "dev_mode"})
    return resp.json()["token"]


@pytest.mark.asyncio
async def test_tracked_list_empty(client):
    token = await _auth(client)
    resp = await client.get("/api/v1/tracked", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_tracked_add_and_list(client):
    token = await _auth(client)
    headers = {"Authorization": f"Bearer {token}"}

    item = {
        "marketplace": "ozon",
        "sku": "test-sku-123",
        "name": "Тестовый пылесос",
        "url": "https://ozon.ru/product/test",
        "image_url": None,
        "initial_price": 15990,
    }
    resp = await client.post("/api/v1/tracked", json=item, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["sku"] == "test-sku-123"
    assert data["current_price"] == 15990
    item_id = data["id"]

    list_resp = await client.get("/api/v1/tracked", headers=headers)
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_tracked_remove(client):
    token = await _auth(client)
    headers = {"Authorization": f"Bearer {token}"}

    add = await client.post("/api/v1/tracked", json={
        "marketplace": "wildberries", "sku": "wb-sku", "name": "Товар",
        "url": "https://wb.ru/1", "initial_price": 5000,
    }, headers=headers)
    item_id = add.json()["id"]

    del_resp = await client.delete(f"/api/v1/tracked/{item_id}", headers=headers)
    assert del_resp.status_code == 204

    list_resp = await client.get("/api/v1/tracked", headers=headers)
    assert list_resp.json() == []


@pytest.mark.asyncio
async def test_tracked_free_limit(client):
    """Free-пользователь не может добавить более 3 товаров."""
    token = await _auth(client)
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(3):
        resp = await client.post("/api/v1/tracked", json={
            "marketplace": "ozon", "sku": f"sku-{i}", "name": f"Товар {i}",
            "url": f"https://ozon.ru/{i}", "initial_price": 1000,
        }, headers=headers)
        assert resp.status_code == 201

    resp4 = await client.post("/api/v1/tracked", json={
        "marketplace": "ozon", "sku": "sku-4", "name": "Товар 4",
        "url": "https://ozon.ru/4", "initial_price": 1000,
    }, headers=headers)
    assert resp4.status_code == 402
