"""
ЮKassa webhook + хелперы для создания платежей.

Идемпотентность критична:
1. Создание платежа — `Idempotence-Key` стабильный по (user_id, plan, hour),
   чтобы быстрый double-click не создал два платежа.
2. Webhook обработка — проверяем по payment_id что событие ещё не обработано.
3. Race: webhook может прийти раньше чем мы сохраним Subscription
   (после redirect юзера) — UPSERT по payment_id.

Документация: https://yookassa.ru/developers/api
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models.subscription import Subscription
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

YUKASSA_API_URL = "https://api.yookassa.ru/v3"

# События, которые мы обрабатываем
_PAYMENT_SUCCEEDED = "payment.succeeded"
_PAYMENT_CANCELED = "payment.canceled"
_REFUND_SUCCEEDED = "refund.succeeded"


# ── Создание платежа ─────────────────────────────────────────────────────────


async def create_yukassa_payment(
    user: User,
    plan: str,
    amount_rub: int,
    expires_at: datetime,
    session: AsyncSession,
) -> str:
    """
    Создаёт платёж и возвращает URL для редиректа в ЮKassa.

    Idempotence-Key: (user_id, plan, час) — двойной клик не создаст дубликат,
    а через час уже считается новым платежом (старый протух).
    """
    now = datetime.now(timezone.utc)
    idempotence_key = f"sub-{user.id}-{plan}-{now.strftime('%Y%m%d%H')}"

    payload = {
        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": settings.telegram_mini_app_url,
        },
        "capture": True,
        "description": f"AI-шопер Premium {plan}",
        "metadata": {
            "user_id": str(user.id),
            "plan": plan,
            "expires_at": expires_at.isoformat(),
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{YUKASSA_API_URL}/payments",
            auth=(settings.yukassa_shop_id, settings.yukassa_secret_key),
            json=payload,
            headers={"Idempotence-Key": idempotence_key},
        )

    if resp.status_code >= 400:
        logger.error("YuKassa create payment failed %d: %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Payment provider error")

    data = resp.json()
    payment_id = data["id"]

    # UPSERT: создаём подписку или находим существующую (на случай ретрая Idempotence-Key)
    existing = await session.execute(
        select(Subscription).where(Subscription.payment_id == payment_id).limit(1)
    )
    sub = existing.scalar_one_or_none()

    if sub is None:
        sub = Subscription(
            user_id=user.id,
            plan=plan,
            status="pending",
            expires_at=expires_at,
            payment_provider="yukassa",
            payment_id=payment_id,
            amount_rub=amount_rub,
        )
        session.add(sub)
        await session.commit()

    return data["confirmation"]["confirmation_url"]


# ── Webhook ──────────────────────────────────────────────────────────────────


def _verify_signature(body: bytes, signature: str) -> bool:
    """ЮKassa подписывает webhook через HMAC-SHA256 от secret_key."""
    if not signature:
        return False
    expected = hmac.new(
        settings.yukassa_secret_key.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@router.post("/yukassa")
async def yukassa_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Обрабатывает уведомления ЮKassa. Идемпотентно: повторное событие с тем же
    payment_id просто возвращает {ok: true} без изменений.
    """
    body = await request.body()
    signature = request.headers.get("X-Yookassa-Signature", "")

    if not _verify_signature(body, signature):
        # Не отдаём 403 чтобы не светить детали проверки. 400 + общий текст.
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("event")
    obj = event.get("object") or {}

    if event_type == _PAYMENT_SUCCEEDED:
        await _handle_payment_succeeded(obj, session)
    elif event_type == _PAYMENT_CANCELED:
        await _handle_payment_canceled(obj, session)
    elif event_type == _REFUND_SUCCEEDED:
        await _handle_refund_succeeded(obj, session)
    else:
        logger.info("Unhandled YuKassa event: %s", event_type)

    return {"ok": True}


async def _handle_payment_succeeded(payment: dict, session: AsyncSession) -> None:
    payment_id = payment.get("id")
    if not payment_id:
        return

    metadata = payment.get("metadata") or {}
    try:
        user_id = int(metadata.get("user_id", 0))
    except (TypeError, ValueError):
        return
    plan = metadata.get("plan", "month")
    expires_at_str = metadata.get("expires_at")

    user = await session.get(User, user_id) if user_id else None
    if user is None:
        logger.warning("YuKassa webhook: user not found for payment %s", payment_id)
        return

    # Идемпотентность: ищем существующую подписку по payment_id
    result = await session.execute(
        select(Subscription).where(Subscription.payment_id == payment_id).limit(1)
    )
    sub = result.scalar_one_or_none()

    expires_at = (
        datetime.fromisoformat(expires_at_str)
        if expires_at_str
        else datetime.now(timezone.utc) + timedelta(days=30)
    )

    if sub is None:
        # Race condition: webhook пришёл раньше чем create_yukassa_payment
        # успел сохранить подписку. Создаём её здесь.
        amount = payment.get("amount", {}).get("value")
        try:
            amount_rub = float(amount) if amount else None
        except (TypeError, ValueError):
            amount_rub = None

        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status="active",
            expires_at=expires_at,
            payment_provider="yukassa",
            payment_id=payment_id,
            amount_rub=amount_rub,
        )
        session.add(sub)
    elif sub.status == "active":
        # Дубликат события — уже обработано. Не трогаем.
        logger.info("YuKassa duplicate payment.succeeded for %s, ignoring", payment_id)
        return
    else:
        sub.status = "active"

    # Продлеваем премиум. Если у пользователя уже активный — суммируем срок.
    now = datetime.now(timezone.utc)
    base = user.premium_until if (user.is_premium and user.premium_until and user.premium_until > now) else now
    # Срок подписки = разница между новой expires_at и now
    extension = expires_at - now
    new_until = base + extension

    user.is_premium = True
    user.premium_until = new_until
    user.premium_plan = plan
    sub.expires_at = new_until

    await session.commit()
    logger.info(
        "YuKassa: user %d → premium %s until %s",
        user_id, plan, new_until.isoformat(),
    )


async def _handle_payment_canceled(payment: dict, session: AsyncSession) -> None:
    payment_id = payment.get("id")
    if not payment_id:
        return

    result = await session.execute(
        select(Subscription).where(Subscription.payment_id == payment_id).limit(1)
    )
    sub = result.scalar_one_or_none()
    if sub is None or sub.status != "pending":
        return

    sub.status = "cancelled"
    sub.cancelled_at = datetime.now(timezone.utc)
    await session.commit()
    logger.info("YuKassa: payment %s cancelled", payment_id)


async def _handle_refund_succeeded(refund: dict, session: AsyncSession) -> None:
    """При успешном возврате — снимаем премиум немедленно."""
    payment_id = refund.get("payment_id")
    if not payment_id:
        return

    result = await session.execute(
        select(Subscription).where(Subscription.payment_id == payment_id).limit(1)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        return

    sub.status = "expired"
    sub.cancelled_at = datetime.now(timezone.utc)

    user = await session.get(User, sub.user_id)
    if user is not None:
        user.is_premium = False
        user.premium_until = None
        user.premium_plan = None

    await session.commit()
    logger.info("YuKassa: refund processed, premium revoked for user %d", sub.user_id)
