"""
Tests for Layer 4: MemoryStore, memory tools, memory-augmented agent loop.

All unit tests use an in-memory SQLite DB (:memory:) — no files created.
Integration tests require API keys.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.memory import MemoryRecord, MemoryStore
from src.memory_tools import (
    build_memory_registry,
    memory_system_prompt,
    REMEMBER_DEFINITION,
    RECALL_DEFINITION,
    FORGET_DEFINITION,
)
from src.agent_loop import MemoryAgentLoop
from harness_l01.providers import Message, get_client


# ---------------------------------------------------------------------------
# MemoryStore tests (pure SQLite — no network)
# ---------------------------------------------------------------------------


class TestMemoryStore:
    def setup_method(self):
        self.store = MemoryStore(":memory:")

    def teardown_method(self):
        self.store.close()

    def test_save_and_get(self):
        self.store.save("name", "Alice")
        record = self.store.get("name")
        assert record is not None
        assert record.value == "Alice"

    def test_save_upserts(self):
        self.store.save("name", "Alice")
        self.store.save("name", "Bob")
        assert self.store.get("name").value == "Bob"
        assert self.store.count() == 1

    def test_get_missing_key_returns_none(self):
        assert self.store.get("nonexistent") is None

    def test_delete_existing(self):
        self.store.save("key", "val")
        deleted = self.store.delete("key")
        assert deleted is True
        assert self.store.get("key") is None

    def test_delete_missing_returns_false(self):
        assert self.store.delete("ghost") is False

    def test_search_by_key(self):
        self.store.save("user_name", "Alice")
        self.store.save("project_goal", "Build a harness")
        results = self.store.search("user")
        assert len(results) == 1
        assert results[0].key == "user_name"

    def test_search_by_value(self):
        self.store.save("goal", "learn agents")
        results = self.store.search("agents")
        assert len(results) == 1

    def test_search_no_match(self):
        self.store.save("key", "value")
        results = self.store.search("zzznomatch")
        assert results == []

    def test_all_returns_all(self):
        self.store.save("a", "1")
        self.store.save("b", "2")
        assert len(self.store.all()) == 2

    def test_count(self):
        assert self.store.count() == 0
        self.store.save("x", "y")
        assert self.store.count() == 1

    def test_format_all_empty(self):
        assert "no memories" in self.store.format_all()

    def test_format_all_nonempty(self):
        self.store.save("name", "Alice")
        formatted = self.store.format_all()
        assert "name" in formatted
        assert "Alice" in formatted

    def test_format_search_no_match(self):
        result = self.store.format_search("missing")
        assert "no memories" in result

    def test_record_is_pydantic_model(self):
        self.store.save("k", "v")
        record = self.store.get("k")
        assert isinstance(record, MemoryRecord)
        assert record.id is not None
        assert record.created_at is not None


# ---------------------------------------------------------------------------
# Memory tools tests
# ---------------------------------------------------------------------------


class TestMemoryTools:
    def setup_method(self):
        self.store = MemoryStore(":memory:")
        self.registry = build_memory_registry(self.store)

    def teardown_method(self):
        self.store.close()

    def test_registry_has_three_tools(self):
        names = {d.name for d in self.registry.all_definitions()}
        assert names == {"remember", "recall", "forget"}

    def test_remember_tool_stores(self):
        result = self.registry.execute("remember", "id-1", {"key": "color", "value": "blue"})
        assert not result.is_error
        assert self.store.get("color").value == "blue"

    def test_recall_tool_returns_match(self):
        self.store.save("color", "blue")
        result = self.registry.execute("recall", "id-2", {"query": "color"})
        assert "blue" in result.content

    def test_recall_tool_no_match(self):
        result = self.registry.execute("recall", "id-3", {"query": "zzz"})
        assert "no memories" in result.content

    def test_forget_tool_deletes(self):
        self.store.save("temp", "delete me")
        result = self.registry.execute("forget", "id-4", {"key": "temp"})
        assert not result.is_error
        assert self.store.get("temp") is None

    def test_forget_tool_missing_key(self):
        result = self.registry.execute("forget", "id-5", {"key": "ghost"})
        assert "Not found" in result.content

    def test_tool_definitions_have_schemas(self):
        for defn in [REMEMBER_DEFINITION, RECALL_DEFINITION, FORGET_DEFINITION]:
            schema = defn.to_anthropic()
            assert "input_schema" in schema
            assert "name" in schema

    def test_memory_system_prompt_includes_memories(self):
        self.store.save("user", "Alice")
        prompt = memory_system_prompt(self.store)
        assert "Alice" in prompt

    def test_memory_system_prompt_empty_store(self):
        prompt = memory_system_prompt(self.store)
        assert "no memories" in prompt

    def test_memory_system_prompt_prepends_to_base(self):
        prompt = memory_system_prompt(self.store, base_system="Be helpful.")
        assert "Be helpful." in prompt
        assert "What you remember" in prompt


# ---------------------------------------------------------------------------
# MemoryAgentLoop tests (mocked LLM)
# ---------------------------------------------------------------------------


def _make_memory_loop(stop_reason: str = "end_turn", response_text: str = "Done.") -> MemoryAgentLoop:
    with patch("harness_l01.providers.anthropic.Anthropic"), patch.dict(
        os.environ, {"ANTHROPIC_API_KEY": "test"}
    ):
        client = get_client("anthropic")

    store = MemoryStore(":memory:")
    loop = MemoryAgentLoop(client=client, store=store)

    mock_response = MagicMock()
    mock_response.stop_reason = stop_reason
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = response_text
    mock_response.content = [text_block]
    client._anthropic.messages.create = MagicMock(return_value=mock_response)
    return loop


class TestMemoryAgentLoop:
    def test_returns_response(self):
        loop = _make_memory_loop()
        assert loop.run("hello") == "Done."

    def test_system_prompt_refreshed_each_turn(self):
        loop = _make_memory_loop()
        loop.store.save("fact", "important")
        loop.run("hello")
        call_kwargs = loop.client._anthropic.messages.create.call_args[1]
        assert "important" in call_kwargs.get("system", "")

    def test_memory_and_default_tools_both_present(self):
        loop = _make_memory_loop()
        names = {d.name for d in loop.registry.all_definitions()}
        assert "remember" in names
        assert "recall" in names
        assert "forget" in names
        assert "read_file" in names
        assert "run_shell" in names

    def test_store_persists_across_turns(self):
        loop = _make_memory_loop()
        loop.store.save("session", "active")
        loop.run("turn 1")
        loop.run("turn 2")
        assert loop.store.get("session").value == "active"


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMemoryIntegration:
    def test_remember_and_recall(self):
        client = get_client("openrouter")
        store = MemoryStore(":memory:")
        loop = MemoryAgentLoop(client=client, store=store)

        loop.run("My name is Alex. Please remember this.")
        assert store.search("name") or store.search("Alex"), "Expected agent to call remember"

    def test_recall_injected_in_response(self):
        client = get_client("openrouter")
        store = MemoryStore(":memory:")
        store.save("user_name", "Alex")
        loop = MemoryAgentLoop(client=client, store=store)

        response = loop.run("What is my name? Use the recall tool.")
        assert "Alex" in response
