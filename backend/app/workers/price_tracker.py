"""
Celery: проверка цен tracked_items каждый час, генерация алертов.

Ключевые требования:
1. Один зависший товар не должен ронять весь батч → ошибки изолированы на уровне товара.
2. Rate limit на маркетплейс → используется per-host limiter из _http.py.
3. Идемпотентность → алерт не должен прилететь дважды для одного снижения.
   Защита: проверяем last_alert_sent_at внутри SQL-транзакции и обновляем
   ту же строку атомарно.
4. Параллельность → товары обрабатываются батчами по 20 одновременно.
5. Premium-подписки → отдельная задача `expire_premium` ставит is_premium=False
   при premium_until < now.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, select, update

from app.marketplaces.base import get_price_by_marketplace
from app.models.subscription import Subscription
from app.models.tracked import PriceHistory, TrackedItem
from app.models.user import User
from app.workers._db import worker_session_maker
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

BATCH_SIZE = 100        # сколько items загружаем из БД одним запросом
CONCURRENCY = 20        # сколько товаров обрабатываем параллельно
ALERT_COOLDOWN_HOURS = 24  # не шлём один и тот же алерт чаще раза в сутки

# Алиас для совместимости с alerts.py и тестами
_session_maker = worker_session_maker


# ── Celery entry points ──────────────────────────────────────────────────────


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def check_all_prices(self) -> None:
    """Запускается по расписанию из celery_app.beat_schedule (раз в час)."""
    try:
        asyncio.run(_check_all_prices_async())
    except Exception as e:
        logger.exception("check_all_prices failed: %s", e)
        raise self.retry(exc=e)


@celery_app.task
def cleanup_expired() -> None:
    """Раз в сутки: чистим истекшие pending-подписки и старую историю цен."""
    asyncio.run(_cleanup_async())


@celery_app.task
def expire_premium() -> None:
    """Раз в час: снимаем is_premium с пользователей, у которых истекла подписка."""
    asyncio.run(_expire_premium_async())


# ── Main loop ────────────────────────────────────────────────────────────────


async def _check_all_prices_async() -> None:
    started = datetime.now(timezone.utc)
    logger.info("Price check started at %s", started.isoformat())

    processed = 0
    alerts_sent = 0
    errors = 0

    async with _session_maker() as session:
        offset = 0
        while True:
            result = await session.execute(
                select(TrackedItem)
                .where(TrackedItem.is_active.is_(True))
                .order_by(TrackedItem.id)
                .offset(offset)
                .limit(BATCH_SIZE)
            )
            batch = list(result.scalars().all())
            if not batch:
                break

            # Параллельная обработка батча с ограничением concurrency
            semaphore = asyncio.Semaphore(CONCURRENCY)

            async def _bounded(item: TrackedItem):
                async with semaphore:
                    return await _process_item(item)

            results = await asyncio.gather(
                *[_bounded(it) for it in batch], return_exceptions=True
            )
            for r in results:
                processed += 1
                if isinstance(r, Exception):
                    errors += 1
                    logger.warning("Item processing error: %s", r)
                elif r == "alert":
                    alerts_sent += 1

            offset += BATCH_SIZE

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    logger.info(
        "Price check done: processed=%d alerts=%d errors=%d in %.1fs",
        processed, alerts_sent, errors, elapsed,
    )


async def _process_item(item: TrackedItem) -> str | None:
    """
    Обрабатывает один tracked_item. Возвращает:
      - "alert" если был отправлен alert
      - "skip" если цена не изменилась
      - None если ошибка / без обновления
    """
    # Берём цену через адаптер. Если None — маркетплейс недоступен, пропускаем.
    new_price = await get_price_by_marketplace(item.marketplace, item.sku)
    if new_price is None:
        return None

    now = datetime.now(timezone.utc)
    threshold = item.current_price * (100 - item.alert_threshold_pct) / 100
    should_alert = new_price <= threshold

    # Записываем историю и обновляем текущую цену в одной транзакции.
    # Идемпотентность алертов: UPDATE условный по last_alert_sent_at.
    async with _session_maker() as session:
        # Сохраняем точку истории — даже если цена не менялась (нужно для графика)
        session.add(PriceHistory(tracked_item_id=item.id, price=new_price))

        if not should_alert:
            await session.execute(
                update(TrackedItem)
                .where(TrackedItem.id == item.id)
                .values(current_price=new_price, last_checked_at=now)
            )
            await session.commit()
            return "skip"

        # Атомарно: обновляем last_alert_sent_at только если предыдущий алерт
        # был >= COOLDOWN часов назад (или не было вообще). Так избегаем двух
        # алертов даже если воркер запустился дважды (например, после сбоя).
        cooldown_cutoff = now - timedelta(hours=ALERT_COOLDOWN_HOURS)
        res = await session.execute(
            update(TrackedItem)
            .where(
                and_(
                    TrackedItem.id == item.id,
                    (TrackedItem.last_alert_sent_at.is_(None))
                    | (TrackedItem.last_alert_sent_at < cooldown_cutoff),
                )
            )
            .values(
                current_price=new_price,
                last_checked_at=now,
                last_alert_sent_at=now,
            )
        )
        await session.commit()

        if res.rowcount == 0:
            # Кто-то другой уже отметил алерт отправленным, либо cooldown не прошёл
            return "skip"

        # Достаём данные пользователя для уведомления
        user = await session.get(User, item.user_id)
        if not user or not user.push_consent:
            return None

    # Постановка задачи на отправку. Если задача упадёт, БД уже отметила
    # last_alert_sent_at — мы не зашлём дубль, но и пользователь не получит уведомление
    # пока не сбросится cooldown. Это приемлемый trade-off, в проде можно через
    # outbox pattern или retry с компенсацией.
    from app.workers.alerts import send_price_alert
    send_price_alert.delay(
        user_tg_id=user.tg_user_id,
        tracked_item_id=item.id,
        item_name=item.name,
        old_price=int(item.current_price),
        new_price=int(new_price),
        url=item.url,
    )
    return "alert"


# ── Cleanup ──────────────────────────────────────────────────────────────────


async def _cleanup_async() -> None:
    started = datetime.now(timezone.utc)
    cutoff_pending = started - timedelta(hours=24)
    cutoff_history = started - timedelta(days=90)

    async with _session_maker() as session:
        # 1. Pending-подписки старше 24ч → cancelled
        pending = await session.execute(
            update(Subscription)
            .where(
                and_(
                    Subscription.status == "pending",
                    Subscription.started_at < cutoff_pending,
                )
            )
            .values(status="cancelled", cancelled_at=started)
        )

        # 2. Старая история цен (>90 дней)
        old_history = await session.execute(
            delete(PriceHistory).where(PriceHistory.captured_at < cutoff_history)
        )

        await session.commit()

    logger.info(
        "Cleanup done: pending_cancelled=%d history_deleted=%d",
        pending.rowcount, old_history.rowcount,
    )


async def _expire_premium_async() -> None:
    """Снимает is_premium у пользователей с истёкшим premium_until."""
    now = datetime.now(timezone.utc)
    async with _session_maker() as session:
        # Деактивируем подписки
        await session.execute(
            update(Subscription)
            .where(
                and_(
                    Subscription.status == "active",
                    Subscription.expires_at < now,
                )
            )
            .values(status="expired")
        )

        # Снимаем флаг premium с пользователей
        res = await session.execute(
            update(User)
            .where(
                and_(
                    User.is_premium.is_(True),
                    User.premium_until < now,
                )
            )
            .values(is_premium=False, premium_plan=None)
        )
        await session.commit()
    logger.info("Premium expired for %d users", res.rowcount)
