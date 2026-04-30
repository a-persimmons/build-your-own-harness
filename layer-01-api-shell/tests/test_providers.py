"""
Tests for Layer 1: provider abstraction and streaming.

Unit tests mock the network; integration tests hit real APIs.
Run unit tests only:      uv run pytest tests/ -m "not integration"
Run integration tests:    uv run pytest tests/ -m integration
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from harness_l01.providers import DEFAULT_MODELS, LLMClient, Message, Provider, get_client
from harness_l01.repl import collect_response


# ---------------------------------------------------------------------------
# Unit tests (no network)
# ---------------------------------------------------------------------------


class TestProvider:
    def test_enum_values(self):
        assert Provider("anthropic") == Provider.ANTHROPIC
        assert Provider("openrouter") == Provider.OPENROUTER
        assert Provider("openai") == Provider.OPENAI

    def test_invalid_provider_raises(self):
        with pytest.raises(ValueError):
            Provider("unknown")


class TestGetClient:
    def test_returns_llm_client(self):
        with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "test-key"}
        ):
            client = get_client("anthropic")
        assert isinstance(client, LLMClient)

    def test_default_model_assigned(self):
        with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "test-key"}
        ):
            client = get_client("anthropic")
        assert client.model == DEFAULT_MODELS[Provider.ANTHROPIC]

    def test_model_override(self):
        with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "test-key"}
        ):
            client = get_client("anthropic", model="claude-haiku-4-5-20251001")
        assert client.model == "claude-haiku-4-5-20251001"


class TestStreamingMocked:
    def _make_anthropic_client(self) -> LLMClient:
        with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "test-key"}
        ):
            return get_client("anthropic")

    def test_stream_yields_chunks(self):
        client = self._make_anthropic_client()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["Hello", ", ", "world", "!"])

        with patch.object(client._anthropic, "messages") as mock_messages:
            mock_messages.stream.return_value = mock_stream_ctx
            messages = [Message(role="user", content="Hi")]
            result = "".join(client.stream(messages))

        assert result == "Hello, world!"

    def test_history_preserved_across_turns(self):
        """Messages passed to stream are unchanged by the call."""
        client = self._make_anthropic_client()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["ok"])

        messages = [
            Message(role="user", content="turn 1"),
            Message(role="assistant", content="response 1"),
            Message(role="user", content="turn 2"),
        ]
        with patch.object(client._anthropic, "messages") as mock_messages:
            mock_messages.stream.return_value = mock_stream_ctx
            list(client.stream(messages))
            call_kwargs = mock_messages.stream.call_args[1]

        assert len(call_kwargs["messages"]) == 3

    def test_system_prompt_included(self):
        client = self._make_anthropic_client()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["ok"])

        with patch.object(client._anthropic, "messages") as mock_messages:
            mock_messages.stream.return_value = mock_stream_ctx
            list(client.stream([Message(role="user", content="hi")], system="Be terse."))
            call_kwargs = mock_messages.stream.call_args[1]

        assert call_kwargs.get("system") == "Be terse."

    def test_empty_system_omitted(self):
        client = self._make_anthropic_client()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["ok"])

        with patch.object(client._anthropic, "messages") as mock_messages:
            mock_messages.stream.return_value = mock_stream_ctx
            list(client.stream([Message(role="user", content="hi")], system=""))
            call_kwargs = mock_messages.stream.call_args[1]

        assert "system" not in call_kwargs


class TestCollectResponse:
    def test_collects_full_response(self):
        with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "test-key"}
        ):
            client = get_client("anthropic")

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["The", " answer", " is", " 42."])

        with patch.object(client._anthropic, "messages") as mock_messages:
            mock_messages.stream.return_value = mock_stream_ctx
            result = collect_response(client, "What is the answer?")

        assert result == "The answer is 42."


# ---------------------------------------------------------------------------
# Integration tests (require real API keys)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAnthropicIntegration:
    def test_stream_returns_nonempty_response(self):
        client = get_client("anthropic")
        messages = [Message(role="user", content="Reply with exactly: OK")]
        response = "".join(client.stream(messages))
        assert len(response) > 0

    def test_multi_turn_works(self):
        client = get_client("anthropic")
        history = [
            Message(role="user", content="My name is Alex."),
            Message(role="assistant", content="Hello Alex!"),
            Message(role="user", content="What is my name? One word only."),
        ]
        response = "".join(client.stream(history))
        assert "Alex" in response


@pytest.mark.integration
class TestOpenRouterIntegration:
    def test_stream_returns_nonempty_response(self):
        client = get_client("openrouter")
        messages = [Message(role="user", content="Reply with exactly: OK")]
        response = "".join(client.stream(messages))
        assert len(response) > 0
