from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.tracked import SubscriptionStartRequest, SubscriptionStatus

router = APIRouter(prefix="/subscription", tags=["subscription"])

PLAN_PRICES = {
    "month": 590,
    "year": 4900,
    "trial": 0,
}

PLAN_DAYS = {
    "month": 30,
    "year": 365,
    "trial": 7,
}


@router.get("", response_model=SubscriptionStatus)
async def get_subscription(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status == "active")
        .order_by(Subscription.started_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    return SubscriptionStatus(
        is_premium=user.is_premium,
        plan=sub.plan if sub else None,
        expires_at=sub.expires_at if sub else None,
        status=sub.status if sub else None,
    )


@router.post("/start")
async def start_subscription(
    body: SubscriptionStartRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if body.plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan")

    expires_at = datetime.now(timezone.utc) + timedelta(days=PLAN_DAYS[body.plan])

    if body.plan == "trial":
        sub = Subscription(
            user_id=user.id,
            plan="trial",
            status="active",
            expires_at=expires_at,
            payment_provider=None,
            amount_rub=0,
        )
        session.add(sub)
        user.is_premium = True
        user.premium_until = expires_at
        user.premium_plan = "trial"
        await session.commit()
        return {"ok": True}

    # Для платных тарифов — создаём платёж в ЮKassa
    from app.api.webhook import create_yukassa_payment
    redirect_url = await create_yukassa_payment(user, body.plan, PLAN_PRICES[body.plan], expires_at, session)
    return {"redirect_url": redirect_url}


@router.post("/cancel")
async def cancel_subscription(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status == "active")
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.status = "cancelled"
        sub.cancelled_at = datetime.now(timezone.utc)
        sub.auto_renew = False
        await session.commit()
    return {"ok": True}
