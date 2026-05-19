from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.models.tracked import PriceHistory, TrackedItem
from app.models.user import User
from app.schemas.tracked import PriceHistoryPoint, TrackedItemCreate, TrackedItemOut

router = APIRouter(prefix="/tracked", tags=["tracked"])

FREE_TRACKED_LIMIT = 3


@router.get("", response_model=list[TrackedItemOut])
async def list_tracked(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(TrackedItem)
        .where(TrackedItem.user_id == user.id, TrackedItem.is_active == True)
        .order_by(TrackedItem.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=TrackedItemOut, status_code=status.HTTP_201_CREATED)
async def add_tracked(
    body: TrackedItemCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_premium:
        result = await session.execute(
            select(TrackedItem).where(TrackedItem.user_id == user.id, TrackedItem.is_active == True)
        )
        count = len(result.scalars().all())
        if count >= FREE_TRACKED_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"paywall": True, "message": "Premium даёт безлимит отслеживания"},
            )

    item = TrackedItem(user_id=user.id, **body.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)

    history = PriceHistory(tracked_item_id=item.id, price=item.initial_price)
    session.add(history)
    await session.commit()

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tracked(
    item_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await session.get(TrackedItem, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    item.is_active = False
    await session.commit()


@router.get("/{item_id}/history", response_model=list[PriceHistoryPoint])
async def get_price_history(
    item_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    item = await session.get(TrackedItem, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    result = await session.execute(
        select(PriceHistory)
        .where(PriceHistory.tracked_item_id == item_id)
        .order_by(PriceHistory.captured_at.asc())
    )
    return result.scalars().all()
