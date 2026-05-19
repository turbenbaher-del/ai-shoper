import pytest


@pytest.mark.asyncio
async def test_auth_dev_mode(client):
    """В dev-режиме без TELEGRAM_BOT_TOKEN должна работать авторизация с любым init_data."""
    resp = await client.post("/api/v1/auth/telegram", json={"init_data": "dev_mode"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["tg_user_id"] == 123456789
    assert data["is_new"] is True


@pytest.mark.asyncio
async def test_auth_returns_same_user_on_second_call(client):
    """Повторная авторизация того же пользователя не создаёт дубликат."""
    resp1 = await client.post("/api/v1/auth/telegram", json={"init_data": "dev_mode"})
    resp2 = await client.post("/api/v1/auth/telegram", json={"init_data": "dev_mode"})
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["user"]["id"] == resp2.json()["user"]["id"]
    assert resp2.json()["is_new"] is False


@pytest.mark.asyncio
async def test_quiz_requires_auth(client):
    """Quiz endpoint требует авторизации."""
    resp = await client.post("/api/v1/quiz", json={
        "who": "для себя",
        "marketplaces": ["ozon"],
        "priority": "цена",
        "categories": ["электроника"],
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_quiz_saves_data(client):
    """Quiz сохраняет данные онбординга для авторизованного пользователя."""
    auth = await client.post("/api/v1/auth/telegram", json={"init_data": "dev_mode"})
    token = auth.json()["token"]

    resp = await client.post(
        "/api/v1/quiz",
        json={"who": "для семьи", "marketplaces": ["ozon", "wildberries"], "priority": "цена", "categories": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
