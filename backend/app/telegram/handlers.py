"""
Обработчики сообщений Telegram бота.
"""
import logging

from app.config import settings
from app.telegram.bot import send_message

logger = logging.getLogger(__name__)

_MINI_APP_BUTTON = {
    "inline_keyboard": [[
        {"text": "🛍 Открыть AI-шопер", "web_app": {"url": settings.telegram_mini_app_url}},
    ]]
}


async def handle_start(chat_id: int, first_name: str) -> None:
    text = (
        f"Привет, {first_name}! 👋\n\n"
        "Я AI-шопер — нахожу лучшие товары на Ozon, Wildberries и Я.Маркет "
        "и анализирую отзывы, чтобы ты не купил кота в мешке.\n\n"
        "🆓 <b>3 поиска в месяц бесплатно</b>\n"
        "💎 <b>Premium</b> — безлимит + отслеживание цен (590₽/мес)"
    )
    await send_message(
        chat_id, text,
        reply_markup=_MINI_APP_BUTTON if settings.telegram_mini_app_url else None,
    )


async def handle_help(chat_id: int) -> None:
    text = (
        "Как пользоваться:\n\n"
        "1. Нажми «Открыть приложение»\n"
        "2. Опиши что ищешь голосом или текстом\n"
        "3. Получи топ-3 варианта с анализом отзывов\n\n"
        "Бесплатно: 3 поиска в месяц\n"
        "Premium: безлимит + отслеживание цен — 590₽/мес"
    )
    await send_message(chat_id, text)


async def handle_unknown(chat_id: int) -> None:
    await send_message(
        chat_id,
        "Для поиска товаров открой мини-приложение — там удобнее.",
    )


async def process_update(update: dict) -> None:
    """Роутер входящих обновлений от Telegram."""
    message = update.get("message", {})
    if not message:
        return

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    first_name = message.get("from", {}).get("first_name", "")

    if text == "/start":
        await handle_start(chat_id, first_name)
    elif text == "/help":
        await handle_help(chat_id)
    else:
        await handle_unknown(chat_id)
