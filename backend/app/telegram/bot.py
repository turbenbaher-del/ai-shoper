"""
Telegram Bot — обработка команд и Wizard of Oz режим.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)
TG_API_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def set_webhook(webhook_url: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TG_API_URL}/setWebhook",
            json={
                "url": webhook_url,
                "secret_token": settings.telegram_webhook_secret,
                "allowed_updates": ["message", "callback_query"],
            },
        )
        return resp.is_success


async def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> bool:
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{TG_API_URL}/sendMessage", json=payload)
        return resp.is_success


async def notify_owner(message: str) -> None:
    """Уведомление владельца о событии (Wizard of Oz, алерты и т.д.)."""
    if not settings.owner_chat_id:
        return
    await send_message(settings.owner_chat_id, message)
