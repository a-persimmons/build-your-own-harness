"""
Tests for Layer 2: tool registry, built-in handlers, and agent loop.

Unit tests mock the LLM; integration tests hit real APIs.
Run unit tests:        uv run pytest tests/ -m "not integration" -v
Run integration tests: uv run pytest tests/ -m integration -v
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.tools import (
    ToolDefinition,
    ToolRegistry,
    ToolResult,
    _handle_read_file,
    _handle_run_shell,
    build_default_registry,
)
from src.agent_loop import AgentLoop
from harness_l01.providers import Message, get_client


# ---------------------------------------------------------------------------
# ToolRegistry tests
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_register_and_lookup(self):
        registry = ToolRegistry()
        defn = ToolDefinition(
            name="echo",
            description="Echo input",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        )
        registry.register(defn, lambda inputs: inputs["text"])
        assert "echo" in registry
        assert registry.get_definition("echo").name == "echo"

    def test_execute_success(self):
        registry = ToolRegistry()
        defn = ToolDefinition(name="add", description="Add two numbers",
            input_schema={"type": "object", "properties": {}, "required": []})
        registry.register(defn, lambda inputs: str(inputs["a"] + inputs["b"]))
        result = registry.execute("add", "id-1", {"a": 2, "b": 3})
        assert result.content == "5"
        assert not result.is_error

    def test_execute_unknown_tool_returns_error(self):
        registry = ToolRegistry()
        result = registry.execute("nonexistent", "id-1", {})
        assert result.is_error
        assert "Unknown tool" in result.content

    def test_execute_handler_exception_returns_error(self):
        registry = ToolRegistry()
        defn = ToolDefinition(name="boom", description="Always fails",
            input_schema={"type": "object", "properties": {}, "required": []})
        registry.register(defn, lambda _: (_ for _ in ()).throw(ValueError("kaboom")))
        result = registry.execute("boom", "id-1", {})
        assert result.is_error

    def test_all_definitions_returns_all(self):
        registry = build_default_registry()
        names = {d.name for d in registry.all_definitions()}
        assert "read_file" in names
        assert "run_shell" in names

    def test_len(self):
        registry = build_default_registry()
        assert len(registry) == 2

    def test_to_anthropic_schema(self):
        defn = ToolDefinition(
            name="test", description="A test tool",
            input_schema={"type": "object", "properties": {}, "required": []},
        )
        schema = defn.to_anthropic()
        assert schema["name"] == "test"
        assert "input_schema" in schema

    def test_to_openai_schema(self):
        defn = ToolDefinition(
            name="test", description="A test tool",
            input_schema={"type": "object", "properties": {}, "required": []},
        )
        schema = defn.to_openai()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test"


# ---------------------------------------------------------------------------
# Built-in handler tests
# ---------------------------------------------------------------------------


class TestReadFileHandler:
    def test_reads_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name
        assert _handle_read_file({"path": path}) == "hello world"

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            _handle_read_file({"path": "/nonexistent/path/file.txt"})


class TestRunShellHandler:
    def test_captures_stdout(self):
        result = _handle_run_shell({"command": "echo hello"})
        assert "hello" in result

    def test_captures_stderr(self):
        result = _handle_run_shell({"command": "echo err >&2"})
        assert "err" in result

    def test_nonzero_exit_code_noted(self):
        result = _handle_run_shell({"command": "exit 1"})
        assert "exit code" in result


# ---------------------------------------------------------------------------
# AgentLoop tests (mocked LLM)
# ---------------------------------------------------------------------------


def _make_loop(stop_reason: str = "end_turn", content: list | None = None) -> AgentLoop:
    """Build an AgentLoop with a mocked Anthropic client."""
    with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
        client = get_client("anthropic")

    registry = build_default_registry()
    loop = AgentLoop(client=client, registry=registry)

    mock_response = MagicMock()
    mock_response.stop_reason = stop_reason
    mock_response.content = []
    if content:
        for block in content:
            mock_block = MagicMock()
            mock_block.type = block["type"]
            if block["type"] == "text":
                mock_block.text = block["text"]
            elif block["type"] == "tool_use":
                mock_block.id = block["id"]
                mock_block.name = block["name"]
                mock_block.input = block["input"]
            mock_response.content.append(mock_block)
    else:
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "I am the answer."
        mock_response.content = [text_block]

    client._anthropic.messages.create = MagicMock(return_value=mock_response)
    return loop


class TestAgentLoop:
    def test_plain_response_returned(self):
        loop = _make_loop()
        result = loop.run("Hello")
        assert result == "I am the answer."

    def test_tool_call_then_response(self):
        """Loop calls a tool, then gets a plain text response on the second turn."""
        with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            client = get_client("anthropic")
        registry = build_default_registry()
        loop = AgentLoop(client=client, registry=registry)

        tool_response = MagicMock()
        tool_response.stop_reason = "tool_use"
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "call-1"
        tool_block.name = "run_shell"
        tool_block.input = {"command": "echo hi"}
        tool_response.content = [tool_block]

        final_response = MagicMock()
        final_response.stop_reason = "end_turn"
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Done."
        final_response.content = [text_block]

        client._anthropic.messages.create = MagicMock(side_effect=[tool_response, final_response])
        result = loop.run("Run echo hi")
        assert result == "Done."
        assert client._anthropic.messages.create.call_count == 2

    def test_max_iterations_guard(self):
        """If the model keeps calling tools, loop terminates after max_iterations."""
        with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            client = get_client("anthropic")
        registry = build_default_registry()
        loop = AgentLoop(client=client, registry=registry, max_iterations=3)

        tool_response = MagicMock()
        tool_response.stop_reason = "tool_use"
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "call-1"
        tool_block.name = "run_shell"
        tool_block.input = {"command": "echo loop"}
        tool_response.content = [tool_block]

        client._anthropic.messages.create = MagicMock(return_value=tool_response)
        result = loop.run("Loop forever")
        assert "max iterations" in result
        assert client._anthropic.messages.create.call_count == 3


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAgentLoopIntegration:
    def test_shell_tool_called(self):
        client = get_client("openrouter")
        registry = build_default_registry()
        loop = AgentLoop(client=client, registry=registry)
        result = loop.run("Use the run_shell tool to run: echo integration_test_ok")
        assert "integration_test_ok" in result

    def test_read_file_tool_called(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("the secret content")
            path = f.name
        client = get_client("openrouter")
        registry = build_default_registry()
        loop = AgentLoop(client=client, registry=registry)
        result = loop.run(f"Use the read_file tool to read: {path}")
        assert "secret content" in result
