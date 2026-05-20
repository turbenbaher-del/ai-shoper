"""
Обработчики сообщений Telegram бота.
"""
import logging

from app.config import settings
from app.telegram.bot import send_message

logger = logging.getLogger(__name__)

def _mini_app_button(url: str) -> dict:
    versioned = url.rstrip("/") + "/?v=2"
    return {
        "inline_keyboard": [[
            {"text": "Открыть AI-шопер", "web_app": {"url": versioned}},
        ]]
    }


async def handle_start(chat_id: int, first_name: str) -> None:
    text = (
        f"Привет, {first_name}! 👋\n\n"
        "Я <b>AI-шопер</b> — нахожу лучшие товары на Ozon, Wildberries и Я.Маркет "
        "и анализирую отзывы, чтобы ты не переплатил и не купил кота в мешке.\n\n"
        "<b>Как пользоваться:</b>\n"
        "1️⃣ Нажми кнопку <b>«Открыть AI-шопер»</b> ниже\n"
        "2️⃣ Пройди короткий квиз (30 сек) — укажи город и предпочтения\n"
        "3️⃣ Нажми <b>«Поиск»</b> и опиши товар — голосом или текстом\n"
        "    Например: <i>«наушники до 5000»</i> или <i>«робот-пылесос для шерсти»</i>\n"
        "4️⃣ Получи топ-3 варианта с анализом отзывов и сравнением цен\n\n"
        "Нажми /help если нужна помощь."
    )
    url = settings.telegram_mini_app_url
    await send_message(
        chat_id, text,
        reply_markup=_mini_app_button(url) if url else None,
    )


async def handle_help(chat_id: int) -> None:
    text = (
        "<b>Помощь по AI-шоперу</b>\n\n"
        "<b>Как искать товар:</b>\n"
        "• Открой приложение кнопкой ниже\n"
        "• Нажми большую кнопку <b>«Поиск»</b> в центре экрана\n"
        "• Введи запрос в поле — например:\n"
        "  <i>«iPhone 15 до 80000»</i>\n"
        "  <i>«кофемашина для офиса»</i>\n"
        "  <i>«зимние ботинки до 10000 мужские»</i>\n"
        "• Нажми <b>«Найти»</b> — через 20–30 сек получишь результат\n\n"
        "<b>Советы:</b>\n"
        "• Укажи бюджет — «до 5000», «от 3000 до 8000»\n"
        "• Укажи для кого — «для ребёнка», «в подарок маме»\n"
        "• Говори как другу — «хочу тихий пылесос чтобы не будить детей»\n\n"
        "<b>Иконка 🔔</b> в карточке товара — следить за снижением цены\n"
        "<b>Иконка ↗</b> — открыть и купить на маркетплейсе"
    )
    url = settings.telegram_mini_app_url
    await send_message(
        chat_id, text,
        reply_markup=_mini_app_button(url) if url else None,
    )


async def handle_unknown(chat_id: int) -> None:
    text = (
        "Чтобы найти товар — открой приложение и нажми <b>«Поиск»</b>.\n\n"
        "Нажми /help если не знаешь как пользоваться."
    )
    url = settings.telegram_mini_app_url
    await send_message(
        chat_id, text,
        reply_markup=_mini_app_button(url) if url else None,
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
