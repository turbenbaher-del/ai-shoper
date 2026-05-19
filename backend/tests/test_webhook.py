"""Тесты идемпотентности и обработки edge cases в YuKassa webhook."""
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.models.subscription import Subscription
from app.models.user import User


def _sign(body: bytes) -> str:
    return hmac.new(settings.yukassa_secret_key.encode(), body, hashlib.sha256).hexdigest()


def _payment_event(payment_id: str, user_id: int, plan: str = "month", amount: str = "590.00") -> dict:
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    return {
        "event": "payment.succeeded",
        "object": {
            "id": payment_id,
            "amount": {"value": amount, "currency": "RUB"},
            "metadata": {"user_id": str(user_id), "plan": plan, "expires_at": expires},
        },
    }


async def _create_user(session, tg_id: int = 999) -> User:
    user = User(tg_user_id=tg_id, tg_first_name="Test")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    resp = await client.post(
        "/api/v1/webhook/yukassa",
        content=b'{"event": "test"}',
        headers={"X-Yookassa-Signature": "wrong"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_webhook_activates_premium(client, db_engine):
    """Успешный платёж активирует премиум."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    settings.yukassa_secret_key = "test_secret"
    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async with session_maker() as s:
        user = await _create_user(s)
        user_id = user.id

    body = json.dumps(_payment_event("pay-001", user_id)).encode()
    resp = await client.post(
        "/api/v1/webhook/yukassa",
        content=body,
        headers={"X-Yookassa-Signature": _sign(body)},
    )
    assert resp.status_code == 200

    async with session_maker() as s:
        u = await s.get(User, user_id)
        assert u.is_premium is True
        assert u.premium_plan == "month"


@pytest.mark.asyncio
async def test_webhook_duplicate_event_is_noop(client, db_engine):
    """Повторное событие с тем же payment_id не должно ничего менять."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker

    settings.yukassa_secret_key = "test_secret"
    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async with session_maker() as s:
        user = await _create_user(s, tg_id=1001)
        user_id = user.id

    body = json.dumps(_payment_event("pay-dup", user_id)).encode()
    headers = {"X-Yookassa-Signature": _sign(body)}

    # Первый вызов — создаёт подписку
    resp1 = await client.post("/api/v1/webhook/yukassa", content=body, headers=headers)
    assert resp1.status_code == 200

    async with session_maker() as s:
        result = await s.execute(select(Subscription).where(Subscription.payment_id == "pay-dup"))
        subs_first = list(result.scalars().all())
        assert len(subs_first) == 1
        until_first = (await s.get(User, user_id)).premium_until

    # Второй вызов — должен быть no-op
    resp2 = await client.post("/api/v1/webhook/yukassa", content=body, headers=headers)
    assert resp2.status_code == 200

    async with session_maker() as s:
        result = await s.execute(select(Subscription).where(Subscription.payment_id == "pay-dup"))
        subs_second = list(result.scalars().all())
        assert len(subs_second) == 1  # не создалась вторая подписка
        until_second = (await s.get(User, user_id)).premium_until
        assert until_first == until_second  # премиум не продлился второй раз


@pytest.mark.asyncio
async def test_webhook_unknown_event_is_ignored(client):
    settings.yukassa_secret_key = "test_secret"
    body = json.dumps({"event": "subscription.created", "object": {}}).encode()
    resp = await client.post(
        "/api/v1/webhook/yukassa",
        content=body,
        headers={"X-Yookassa-Signature": _sign(body)},
    )
    assert resp.status_code == 200
