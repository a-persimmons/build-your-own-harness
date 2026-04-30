"""
Memory as tools the LLM can call.

The LLM-managed memory pattern: instead of automatically injecting all memories
into every prompt (expensive, noisy), we give the model three tools:
  - remember       : store a key-value fact
  - recall         : search memories by keyword
  - forget         : delete a memory by key

The model decides when to call them based on the conversation.
We also inject a compact memory summary at the top of every system prompt
so the model always knows what it already knows.

This keeps the MemoryStore as the single source of truth and avoids
polluting the context window with irrelevant facts.
"""

from src.memory import MemoryStore
from harness_l02.tools import ToolDefinition, ToolRegistry


REMEMBER_DEFINITION = ToolDefinition(
    name="remember",
    description=(
        "Store a fact in long-term memory. Use a short, descriptive key "
        "(e.g. 'user_name', 'project_goal'). Overwrites any existing value for that key."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Short label for the fact"},
            "value": {"type": "string", "description": "The fact to remember"},
        },
        "required": ["key", "value"],
    },
)

RECALL_DEFINITION = ToolDefinition(
    name="recall",
    description="Search long-term memory by keyword. Returns matching key-value pairs.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keyword to search for"},
        },
        "required": ["query"],
    },
)

FORGET_DEFINITION = ToolDefinition(
    name="forget",
    description="Delete a memory by its key.",
    input_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "The key to delete"},
        },
        "required": ["key"],
    },
)


def build_memory_registry(store: MemoryStore) -> ToolRegistry:
    """Return a ToolRegistry pre-loaded with memory tools bound to a store."""
    registry = ToolRegistry()

    registry.register(
        REMEMBER_DEFINITION,
        lambda inputs: (
            lambda r: f"Stored: {r.key} = {r.value}"
        )(store.save(inputs["key"], inputs["value"])),
    )

    registry.register(
        RECALL_DEFINITION,
        lambda inputs: store.format_search(inputs["query"]),
    )

    registry.register(
        FORGET_DEFINITION,
        lambda inputs: (
            f"Deleted: {inputs['key']}"
            if store.delete(inputs["key"])
            else f"Not found: {inputs['key']}"
        ),
    )

    return registry


def memory_system_prompt(store: MemoryStore, base_system: str = "") -> str:
    """Prepend a memory summary to the system prompt."""
    memories = store.format_all()
    memory_block = f"## What you remember\n{memories}\n\n"
    return memory_block + (base_system or "You are a helpful assistant.")
