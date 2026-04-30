"""
Tests for Layer 3: token counting, sliding window, summarizer, context manager.

Unit tests are pure — no network calls.
Integration tests require API keys and are marked accordingly.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from harness_l01.providers import Message, get_client
from src.context import (
    ContextManager,
    SlidingWindow,
    Summarizer,
    TokenUsage,
    count_message_tokens,
    count_tokens,
    measure_usage,
)
from src.agent_loop import ContextAwareAgentLoop
from harness_l02.tools import build_default_registry


# ---------------------------------------------------------------------------
# Token counting tests (pure)
# ---------------------------------------------------------------------------


class TestTokenCounting:
    def test_count_tokens_nonempty(self):
        assert count_tokens("hello world") > 0

    def test_count_tokens_empty(self):
        assert count_tokens("") == 0

    def test_count_tokens_longer_text_is_more(self):
        assert count_tokens("hello world foo bar baz") > count_tokens("hi")

    def test_count_message_tokens_includes_overhead(self):
        messages = [Message(role="user", content="hi")]
        # 4 overhead + tokens for "hi"
        assert count_message_tokens(messages) >= 4

    def test_count_message_tokens_scales_with_messages(self):
        one = [Message(role="user", content="hello")]
        two = one + [Message(role="assistant", content="world")]
        assert count_message_tokens(two) > count_message_tokens(one)

    def test_measure_usage_sums_correctly(self):
        messages = [Message(role="user", content="test")]
        usage = measure_usage(messages, system="be helpful")
        assert usage.total == usage.messages + usage.system
        assert usage.system > 0

    def test_measure_usage_no_system(self):
        messages = [Message(role="user", content="test")]
        usage = measure_usage(messages)
        assert usage.system == 0
        assert usage.total == usage.messages

    def test_token_usage_remaining(self):
        usage = TokenUsage(messages=1000, system=500, total=1500)
        assert usage.remaining == 200_000 - 1500


# ---------------------------------------------------------------------------
# SlidingWindow tests
# ---------------------------------------------------------------------------


class TestSlidingWindow:
    def _make_history(self, n_pairs: int) -> list[Message]:
        msgs = []
        for i in range(n_pairs):
            msgs.append(Message(role="user", content=f"user message {i} " * 20))
            msgs.append(Message(role="assistant", content=f"assistant reply {i} " * 20))
        return msgs

    def test_no_trim_when_under_limit(self):
        window = SlidingWindow()
        messages = [Message(role="user", content="hi")]
        result = window.apply(messages, system="", limit=10_000)
        assert result == messages

    def test_trims_to_fit_limit(self):
        window = SlidingWindow()
        messages = self._make_history(10)
        limit = 500
        result = window.apply(messages, system="", limit=limit)
        assert count_message_tokens(result) <= limit

    def test_preserves_most_recent_message(self):
        window = SlidingWindow()
        messages = self._make_history(5)
        last = messages[-1]
        result = window.apply(messages, system="", limit=200)
        assert result[-1].content == last.content

    def test_result_never_starts_with_assistant(self):
        window = SlidingWindow()
        messages = self._make_history(5)
        result = window.apply(messages, system="", limit=200)
        if result:
            assert result[0].role != "assistant"

    def test_returns_copy_not_mutation(self):
        window = SlidingWindow()
        messages = [Message(role="user", content="hi")]
        result = window.apply(messages, system="", limit=10_000)
        assert result is not messages


# ---------------------------------------------------------------------------
# Summarizer tests (mocked LLM)
# ---------------------------------------------------------------------------


def _mock_client(summary_text: str = "This is a summary."):
    with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "test"}
    ):
        client = get_client("anthropic")

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    mock_ctx.text_stream = iter([summary_text])
    client._anthropic.messages.stream = MagicMock(return_value=mock_ctx)
    return client


class TestSummarizer:
    def _make_history(self, n_pairs: int) -> list[Message]:
        msgs = []
        for i in range(n_pairs):
            msgs.append(Message(role="user", content=f"question {i} " * 30))
            msgs.append(Message(role="assistant", content=f"answer {i} " * 30))
        return msgs

    def test_no_trim_when_under_limit(self):
        client = _mock_client()
        summarizer = Summarizer(client=client)
        messages = [Message(role="user", content="hi")]
        result = summarizer.apply(messages, system="", limit=10_000)
        assert result == messages
        client._anthropic.messages.stream.assert_not_called()

    def test_trims_and_injects_summary(self):
        client = _mock_client("Summarized history here.")
        summarizer = Summarizer(client=client)
        messages = self._make_history(6)
        result = summarizer.apply(messages, system="", limit=500)
        assert len(result) < len(messages)
        assert result[0].content.startswith("[Earlier conversation summary]")
        assert "Summarized history here." in result[0].content

    def test_summary_message_is_user_role(self):
        client = _mock_client("A summary.")
        summarizer = Summarizer(client=client)
        messages = self._make_history(6)
        result = summarizer.apply(messages, system="", limit=500)
        assert result[0].role == "user"


# ---------------------------------------------------------------------------
# ContextManager tests
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_records_usage_after_trim(self):
        cm = ContextManager(strategy=SlidingWindow(), token_limit=10_000)
        messages = [Message(role="user", content="hello")]
        cm.trim(messages, system="be helpful")
        assert cm.last_usage is not None
        assert cm.last_usage.total > 0

    def test_usage_log_grows_per_call(self):
        cm = ContextManager(strategy=SlidingWindow(), token_limit=10_000)
        messages = [Message(role="user", content="hi")]
        cm.trim(messages)
        cm.trim(messages)
        assert len(cm.usage_log) == 2

    def test_trim_delegates_to_strategy(self):
        mock_strategy = MagicMock()
        mock_strategy.apply.return_value = [Message(role="user", content="trimmed")]
        cm = ContextManager(strategy=mock_strategy, token_limit=500)
        messages = [Message(role="user", content="original")]
        result = cm.trim(messages, system="sys")
        mock_strategy.apply.assert_called_once_with(messages, "sys", 500)
        assert result[0].content == "trimmed"


# ---------------------------------------------------------------------------
# ContextAwareAgentLoop tests
# ---------------------------------------------------------------------------


def _make_context_loop(token_limit: int = 10_000) -> ContextAwareAgentLoop:
    with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "test"}
    ):
        client = get_client("anthropic")

    registry = build_default_registry()
    cm = ContextManager(strategy=SlidingWindow(), token_limit=token_limit)
    loop = ContextAwareAgentLoop(client=client, registry=registry, context_manager=cm)

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "response"
    mock_response.content = [text_block]
    client._anthropic.messages.create = MagicMock(return_value=mock_response)
    return loop


class TestContextAwareAgentLoop:
    def test_runs_and_returns_response(self):
        loop = _make_context_loop()
        result = loop.run("hello")
        assert result == "response"

    def test_usage_recorded_per_turn(self):
        loop = _make_context_loop()
        loop.run("first turn")
        loop.run("second turn")
        assert len(loop.context_manager.usage_log) == 2

    def test_tight_limit_still_completes(self):
        loop = _make_context_loop(token_limit=50)
        result = loop.run("hi")
        assert result == "response"


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestContextIntegration:
    def test_sliding_window_live(self):
        client = get_client("openrouter")
        registry = build_default_registry()
        cm = ContextManager(strategy=SlidingWindow(), token_limit=2000)
        loop = ContextAwareAgentLoop(client=client, registry=registry, context_manager=cm)
        result = loop.run("Reply with exactly: OK")
        assert len(result) > 0
        assert cm.last_usage is not None

    def test_summarizer_live(self):
        client = get_client("openrouter")
        registry = build_default_registry()
        history = [
            Message(role="user", content="My favourite color is blue. " * 50),
            Message(role="assistant", content="Noted. " * 50),
            Message(role="user", content="What is 2+2? " * 50),
            Message(role="assistant", content="Four. " * 50),
        ]
        cm = ContextManager(strategy=Summarizer(client=client), token_limit=500)
        loop = ContextAwareAgentLoop(client=client, registry=registry, context_manager=cm)
        result = loop.run("Reply with exactly: OK", history=history)
        assert len(result) > 0
