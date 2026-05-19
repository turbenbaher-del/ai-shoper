import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pipeline import run_search_pipeline
from app.api.deps import get_current_user
from app.db import get_session
from app.models.query import Query
from app.models.user import User
from app.schemas.search import QueryHistoryItem, SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])

FREE_SEARCH_LIMIT = 3
RATE_LIMIT_MAX = 10       # запросов
RATE_LIMIT_WINDOW = 60.0  # секунд

# Простой in-process rate limiter. В продакшене — Redis INCR + EXPIRE.
_rate_counters: dict[int, list[float]] = defaultdict(list)


def _check_rate_limit(user_id: int) -> None:
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW
    timestamps = _rate_counters[user_id]
    # Убираем устаревшие
    _rate_counters[user_id] = [t for t in timestamps if t > window_start]
    if len(_rate_counters[user_id]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много запросов. Подожди минуту.",
        )
    _rate_counters[user_id].append(now)


def _reset_if_needed(user: User) -> None:
    """Сбрасывает счётчик бесплатных запросов 1-го числа каждого месяца."""
    now = datetime.now(timezone.utc)
    if user.free_searches_reset_at is None or user.free_searches_reset_at.month != now.month:
        user.free_searches_used = 0
        user.free_searches_reset_at = now


@router.post("", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    _check_rate_limit(user.id)
    _reset_if_needed(user)

    if not user.is_premium and user.free_searches_used >= FREE_SEARCH_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"paywall": True, "message": "Исчерпан лимит бесплатных запросов"},
        )

    start = time.monotonic()
    result = await run_search_pipeline(body.query, user)
    elapsed = round(time.monotonic() - start, 1)

    if result.get("needs_clarification"):
        return SearchResponse(
            query_id=0,
            query=body.query,
            title="Уточни запрос",
            subtitle="",
            products=[],
            share_text=result.get("clarification", ""),
            processing_time_seconds=elapsed,
            needs_clarification=True,
        )

    query_record = Query(
        user_id=user.id,
        raw_text=body.query,
        parsed_request=result.get("parsed_request", {}),
        products=result.get("products", []),
        processing_time_seconds=elapsed,
    )
    session.add(query_record)
    user.free_searches_used += 1
    await session.commit()
    await session.refresh(query_record)

    products = result.get("products", [])
    reviews_count = sum(p.get("reviews_analyzed", 0) for p in products)
    fake_count = sum(p.get("fake_reviews_removed", 0) for p in products)

    return SearchResponse(
        query_id=query_record.id,
        query=body.query,
        title=f"Нашёл {len(products)} варианта",
        subtitle=f"Прочитал {reviews_count} отзывов · сравнил 3 маркетплейса · отсёк {fake_count} накруток",
        products=products,
        share_text=result.get("share_text", ""),
        processing_time_seconds=elapsed,
    )


@router.get("/history", response_model=list[QueryHistoryItem])
async def get_history(
    limit: int = 20,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Query).where(Query.user_id == user.id).order_by(Query.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/{query_id}", response_model=QueryHistoryItem)
async def get_query(
    query_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    q = await session.get(Query, query_id)
    if not q or q.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    return q


@router.get("/{query_id}/{product_idx}/click")
async def track_click(
    query_id: int,
    product_idx: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Логирует клик и редиректит на маркетплейс с CPA-тегом."""
    q = await session.get(Query, query_id)
    if not q or q.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")

    products = q.products or []
    if product_idx >= len(products):
        raise HTTPException(status_code=404, detail="Product not found")

    q.clicked_buy = True
    await session.commit()

    product = products[product_idx]
    best_price = next((p for p in product.get("prices", []) if p.get("is_best")), None)
    url = best_price["url"] if best_price else "/"

    return RedirectResponse(url=url)


@router.post("/{query_id}/share")
async def track_share(
    query_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Фиксирует нажатие «Поделиться» для аналитики CPA-конверсии."""
    q = await session.get(Query, query_id)
    if not q or q.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    q.clicked_share = True
    await session.commit()
    return {"ok": True}
