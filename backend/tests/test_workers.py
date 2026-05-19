"""
Тесты логики price_tracker._process_item:
  - корректное обновление цены и истории
  - alert не дублируется в течение cooldown
  - obsolete алерты не отправляются
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.tracked import PriceHistory, TrackedItem
from app.models.user import User


@pytest.fixture
def patched_session_maker(db_engine, monkeypatch):
    """Подменяем _session_maker в workers, чтобы тесты использовали in-memory БД."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr("app.workers.price_tracker._session_maker", maker)
    return maker


async def _make_user_and_item(maker, current_price: int = 10000, alert_pct: int = 5) -> tuple[int, int]:
    async with maker() as s:
        user = User(tg_user_id=42, tg_first_name="Test", push_consent=True)
        s.add(user)
        await s.commit()
        await s.refresh(user)

        item = TrackedItem(
            user_id=user.id,
            marketplace="wildberries",
            sku="12345",
            name="Тестовый товар",
            url="https://wb.ru/12345",
            initial_price=current_price,
            current_price=current_price,
            alert_threshold_pct=alert_pct,
        )
        s.add(item)
        await s.commit()
        await s.refresh(item)
        return user.id, item.id


@pytest.mark.asyncio
async def test_price_drop_triggers_alert(patched_session_maker):
    """При снижении цены > threshold создаётся алерт и обновляется last_alert_sent_at."""
    from app.workers import price_tracker

    user_id, item_id = await _make_user_and_item(patched_session_maker, current_price=10000, alert_pct=5)

    async with patched_session_maker() as s:
        item = await s.get(TrackedItem, item_id)

    # Цена упала на 10% — должен сработать alert (threshold 5%)
    with patch("app.workers.price_tracker.get_price_by_marketplace", new=AsyncMock(return_value=9000)), \
         patch("app.workers.alerts.send_price_alert.delay") as mock_send:
        outcome = await price_tracker._process_item(item)

    assert outcome == "alert"
    mock_send.assert_called_once()

    async with patched_session_maker() as s:
        updated = await s.get(TrackedItem, item_id)
        assert updated.current_price == 9000
        assert updated.last_alert_sent_at is not None

        history = (await s.execute(
            select(PriceHistory).where(PriceHistory.tracked_item_id == item_id)
        )).scalars().all()
        assert len(history) == 1
        assert history[0].price == 9000


@pytest.mark.asyncio
async def test_alert_cooldown_prevents_duplicate(patched_session_maker):
    """Если last_alert_sent_at недавно — второй alert не отправляется."""
    from app.workers import price_tracker

    user_id, item_id = await _make_user_and_item(patched_session_maker, current_price=10000)

    # Помечаем что недавно отправили alert
    async with patched_session_maker() as s:
        item = await s.get(TrackedItem, item_id)
        item.last_alert_sent_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await s.commit()
        await s.refresh(item)

    with patch("app.workers.price_tracker.get_price_by_marketplace", new=AsyncMock(return_value=8000)), \
         patch("app.workers.alerts.send_price_alert.delay") as mock_send:
        outcome = await price_tracker._process_item(item)

    assert outcome == "skip"
    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_price_unchanged_no_alert(patched_session_maker):
    """Если цена не изменилась — history пишется, alert не отправляется."""
    from app.workers import price_tracker

    user_id, item_id = await _make_user_and_item(patched_session_maker, current_price=10000)

    async with patched_session_maker() as s:
        item = await s.get(TrackedItem, item_id)

    with patch("app.workers.price_tracker.get_price_by_marketplace", new=AsyncMock(return_value=10000)), \
         patch("app.workers.alerts.send_price_alert.delay") as mock_send:
        outcome = await price_tracker._process_item(item)

    assert outcome == "skip"
    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_marketplace_unavailable_no_changes(patched_session_maker):
    """Если маркетплейс вернул None (недоступен) — ничего не меняем."""
    from app.workers import price_tracker

    user_id, item_id = await _make_user_and_item(patched_session_maker, current_price=10000)

    async with patched_session_maker() as s:
        item = await s.get(TrackedItem, item_id)
        original_last_checked = item.last_checked_at

    with patch("app.workers.price_tracker.get_price_by_marketplace", new=AsyncMock(return_value=None)):
        outcome = await price_tracker._process_item(item)

    assert outcome is None

    async with patched_session_maker() as s:
        updated = await s.get(TrackedItem, item_id)
        # Цена не изменилась, last_checked_at тоже не должен обновиться
        assert updated.current_price == 10000


@pytest.mark.asyncio
async def test_expire_premium(patched_session_maker):
    """expire_premium снимает is_premium у пользователей с истёкшим premium_until."""
    from app.workers import price_tracker

    past = datetime.now(timezone.utc) - timedelta(days=1)
    future = datetime.now(timezone.utc) + timedelta(days=30)

    async with patched_session_maker() as s:
        expired_user = User(tg_user_id=100, is_premium=True, premium_until=past, premium_plan="month")
        active_user = User(tg_user_id=101, is_premium=True, premium_until=future, premium_plan="year")
        s.add_all([expired_user, active_user])
        await s.commit()
        expired_id = expired_user.id
        active_id = active_user.id

    await price_tracker._expire_premium_async()

    async with patched_session_maker() as s:
        e = await s.get(User, expired_id)
        a = await s.get(User, active_id)
        assert e.is_premium is False
        assert a.is_premium is True
