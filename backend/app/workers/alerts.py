"""
Celery: отправляет push-уведомления в TG при снижении цены.

Идемпотентность реализована в price_tracker._process_item — он атомарно
помечает last_alert_sent_at до постановки задачи. Здесь же добавляем второй
эшелон защиты: при отправке проверяем, что цена в БД совпадает с той,
для которой генерировался алерт. Если за время в очереди цена откатилась
вверх — алерт уже неактуален, не отправляем.

Telegram имеет 429 rate limiting + временные сбои. Используем retry с
exponential backoff. На постоянные ошибки (chat блокирован, bot заблокирован)
помечаем push_consent=False.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.config import settings
from app.models.tracked import TrackedItem
from app.workers._db import worker_session_maker as _session_maker
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

TG_API_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


@celery_app.task(bind=True, max_retries=5, default_retry_delay=30)
def send_price_alert(
    self,
    user_tg_id: int,
    tracked_item_id: int,
    item_name: str,
    old_price: int,
    new_price: int,
    url: str,
) -> None:
    """Отправляет alert в Telegram. Retry-ит при transient ошибках."""
    try:
        asyncio.run(_send_alert_async(
            user_tg_id=user_tg_id,
            tracked_item_id=tracked_item_id,
            item_name=item_name,
            old_price=old_price,
            new_price=new_price,
            url=url,
        ))
    except _AlertObsolete:
        # Цена уже не та, ничего не делаем
        logger.info("Alert obsolete for item %d, skipping", tracked_item_id)
    except _UserBlocked:
        # Пользователь заблокировал бота — отключаем уведомления
        asyncio.run(_disable_push_for_user(user_tg_id))
    except _TransientTelegramError as e:
        logger.warning("Transient TG error for item %d: %s", tracked_item_id, e)
        raise self.retry(exc=e)


class _AlertObsolete(Exception):
    pass


class _UserBlocked(Exception):
    pass


class _TransientTelegramError(Exception):
    pass


async def _send_alert_async(
    user_tg_id: int,
    tracked_item_id: int,
    item_name: str,
    old_price: int,
    new_price: int,
    url: str,
) -> None:
    # Двойная проверка: убеждаемся что текущая цена в БД соответствует new_price.
    # Если price_tracker уже записал новую цену, но за время в очереди появилась
    # ещё одна, более свежая — наш alert устарел.
    async with _session_maker() as session:
        item = await session.get(TrackedItem, tracked_item_id)
        if item is None or not item.is_active:
            raise _AlertObsolete()
        if item.current_price != new_price:
            raise _AlertObsolete()

    pct = round((old_price - new_price) / old_price * 100)
    savings = old_price - new_price
    text = (
        f"💰 Цена упала на {pct}%\n\n"
        f"{item_name}\n\n"
        f"Было: {old_price:,} ₽\n"
        f"Сейчас: {new_price:,} ₽\n"
        f"Экономия: {savings:,} ₽"
    )

    payload = {
        "chat_id": user_tg_id,
        "text": text,
        "reply_markup": {"inline_keyboard": [[{"text": "Купить", "url": url}]]},
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{TG_API_URL}/sendMessage", json=payload)

    if resp.is_success:
        return

    # Разбираем ошибки TG
    try:
        body = resp.json()
    except Exception:
        body = {}

    description = (body.get("description") or "").lower()
    if resp.status_code == 403 or "bot was blocked" in description or "user is deactivated" in description:
        raise _UserBlocked()

    if resp.status_code == 429:
        # У TG в "parameters.retry_after" указано сколько ждать
        retry_after = (body.get("parameters") or {}).get("retry_after", 30)
        await asyncio.sleep(min(int(retry_after), 60))
        raise _TransientTelegramError(f"429 rate limited, retry after {retry_after}")

    if 500 <= resp.status_code < 600:
        raise _TransientTelegramError(f"TG {resp.status_code}: {body}")

    # Прочие 4xx — постоянные, нет смысла ретраить
    logger.error("TG error %d for user %d: %s", resp.status_code, user_tg_id, body)


async def _disable_push_for_user(tg_user_id: int) -> None:
    """Отключает push для пользователя, заблокировавшего бота."""
    from sqlalchemy import update
    from app.models.user import User

    async with _session_maker() as session:
        await session.execute(
            update(User).where(User.tg_user_id == tg_user_id).values(push_consent=False)
        )
        await session.commit()
    logger.info("Disabled push for tg_user_id=%d (bot blocked)", tg_user_id)
