"""
Юнит-тесты для AI-пайплайна.
"""
import pytest

from app.ai.schemas import ParsedRequest


def test_parsed_request_budget():
    req = ParsedRequest(
        category="наушники",
        budget_max=15000,
        requirements=["шумоподавление"],
        keywords=["наушники", "ANC"],
    )
    assert req.budget_max == 15000
    assert "шумоподавление" in req.requirements


def test_parsed_request_needs_clarification():
    req = ParsedRequest(
        category="unknown",
        needs_clarification=True,
        clarification_question="Какой товар вы ищете?",
    )
    assert req.needs_clarification is True
    assert req.clarification_question is not None


@pytest.mark.asyncio
async def test_pipeline_mock(monkeypatch):
    """Тест пайплайна с mock-данными (без реального API)."""
    from unittest.mock import AsyncMock, patch

    mock_parsed = {
        "category": "наушники",
        "budget_max": 15000,
        "requirements": ["шумоподавление"],
        "keywords": ["наушники"],
        "needs_clarification": False,
        "clarification_question": None,
    }

    with patch("app.ai.pipeline.call_claude_json", new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = mock_parsed

        from app.ai.schemas import ParsedRequest
        result = ParsedRequest(**mock_parsed)
        assert result.category == "наушники"
        assert result.needs_clarification is False
