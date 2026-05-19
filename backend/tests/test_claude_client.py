"""Тесты JSON-extraction и retry-логики Claude клиента."""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.claude_client import _extract_json, call_claude_json


def test_extract_json_plain():
    assert _extract_json('{"a": 1}') == '{"a": 1}'


def test_extract_json_with_markdown_fence():
    text = '```json\n{"a": 1}\n```'
    assert _extract_json(text) == '{"a": 1}'


def test_extract_json_with_preamble():
    text = 'Вот результат:\n{"a": 1, "b": 2}\nКонец.'
    result = _extract_json(text)
    parsed = json.loads(result)
    assert parsed == {"a": 1, "b": 2}


def test_extract_json_array():
    text = '[{"a": 1}, {"b": 2}]'
    assert _extract_json(text) == '[{"a": 1}, {"b": 2}]'


def test_extract_json_nested_braces():
    text = '{"outer": {"inner": "value"}}'
    parsed = json.loads(_extract_json(text))
    assert parsed["outer"]["inner"] == "value"


@pytest.mark.asyncio
async def test_call_claude_json_retries_on_invalid():
    """Если первый ответ — невалидный JSON, делается retry."""
    bad = "not a valid json at all"
    good = '{"category": "наушники"}'

    with patch("app.ai.claude_client.call_claude", new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = [bad, good]
        result = await call_claude_json("system", "user")

    assert mock_call.call_count == 2
    assert result == {"category": "наушники"}
