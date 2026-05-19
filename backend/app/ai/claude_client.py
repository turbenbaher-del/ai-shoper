"""
Claude API клиент:
  - Поддержка прокси для РФ (vsegpt.ru / mws.ru) через ANTHROPIC_BASE_URL.
  - Автоматический retry на rate-limit (429) и transient ошибки.
  - Извлечение JSON из ответа с защитой от лишних markdown-обёрток.
  - Опциональный prompt caching (anthropic ephemeral, экономия до 90% на больших system).

Модели согласно ТЗ раздел 7:
  MODEL_SONNET — для простых задач (парсинг, форматирование, фильтрация)
  MODEL_OPUS   — для сложных (анализ отзывов, ранжирование)
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS = "claude-opus-4-7"

_RETRY_ON_TYPES = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)


def _make_client() -> anthropic.AsyncAnthropic:
    kwargs: dict[str, Any] = {"api_key": settings.anthropic_api_key, "timeout": 60.0, "max_retries": 0}
    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
    return anthropic.AsyncAnthropic(**kwargs)


_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = _make_client()
    return _client


async def call_claude(
    system: str,
    user_message: str,
    *,
    model: str = MODEL_SONNET,
    max_tokens: int = 2048,
    temperature: float = 0.2,
    cache_system: bool = False,
    max_attempts: int = 3,
) -> str:
    """
    Базовый вызов Claude с retry-логикой. Возвращает текст ответа.

    cache_system=True пометит system-промпт для кеширования. Anthropic
    выставляет TTL ~5 минут; повторные вызовы с тем же system дешевле в 10×.
    """
    client = get_client()

    # System может быть строкой или массивом блоков. Для caching нужен массив.
    if cache_system:
        system_param: Any = [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ]
    else:
        system_param = system

    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_param,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except _RETRY_ON_TYPES as e:
            last_err = e
            if attempt < max_attempts - 1:
                delay = (2 ** attempt) * 1.5 + random.uniform(0, 0.5)
                logger.warning("Claude API error (attempt %d): %s, retrying in %.1fs",
                               attempt + 1, e, delay)
                await asyncio.sleep(delay)
            else:
                logger.error("Claude API failed after %d attempts: %s", max_attempts, e)

    raise last_err  # type: ignore[misc]


_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _extract_json(text: str) -> str:
    """Срезает markdown-обёртки и достаёт JSON из ответа."""
    stripped = text.strip()
    # Убираем markdown fences
    stripped = _JSON_FENCE_RE.sub("", stripped).strip()
    # Если перед/после JSON есть текст — пробуем найти первый {…} или […]
    if not (stripped.startswith("{") or stripped.startswith("[")):
        start = min(
            (i for i in (stripped.find("{"), stripped.find("[")) if i >= 0),
            default=-1,
        )
        if start >= 0:
            stripped = stripped[start:]
            # Найти соответствующую закрывающую скобку
            opener = stripped[0]
            closer = "}" if opener == "{" else "]"
            depth = 0
            for i, ch in enumerate(stripped):
                if ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        stripped = stripped[: i + 1]
                        break
    return stripped


async def call_claude_json(
    system: str,
    user_message: str,
    *,
    model: str = MODEL_SONNET,
    max_tokens: int = 2048,
    cache_system: bool = False,
    max_attempts: int = 3,
) -> dict | list:
    """
    Вызов Claude с гарантированным JSON-ответом.
    Если модель вернула невалидный JSON — делаем дополнительный retry с
    подсказкой "верни валидный JSON".
    """
    text = await call_claude(
        system=system,
        user_message=user_message,
        model=model,
        max_tokens=max_tokens,
        cache_system=cache_system,
        max_attempts=max_attempts,
    )

    try:
        return json.loads(_extract_json(text))
    except json.JSONDecodeError:
        logger.warning("Invalid JSON from Claude, retrying with correction hint. Got: %s", text[:200])

    # Второй заход с корректирующим сообщением
    correction = (
        f"{user_message}\n\n"
        f"⚠️ В предыдущем ответе был невалидный JSON: {text[:500]}\n"
        f"Верни ТОЛЬКО валидный JSON без markdown и комментариев."
    )
    text = await call_claude(
        system=system,
        user_message=correction,
        model=model,
        max_tokens=max_tokens,
        cache_system=cache_system,
        max_attempts=max_attempts,
    )
    return json.loads(_extract_json(text))
