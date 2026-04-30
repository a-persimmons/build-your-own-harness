"""
Tool system: definition, registry, and execution.

Design patterns used:
- Registry: maps tool names to handlers; open for extension, closed for modification
- Strategy: each tool handler is an interchangeable callable
- Single Responsibility: ToolDefinition describes a tool; ToolRegistry manages lookup;
  handlers contain execution logic

A tool has three parts kept deliberately separate:
1. ToolDefinition  — the JSON schema the LLM sees (input_schema, description)
2. Handler         — a pure function that executes the tool given validated input
3. ToolRegistry    — binds name → (definition, handler); the only place that knows both
"""

import subprocess
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Tool schema models
# ---------------------------------------------------------------------------


class ToolParameter(BaseModel):
    type: str
    description: str
    enum: list[str] | None = None


class ToolDefinition(BaseModel):
    """The schema passed to the LLM so it knows how to call a tool."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_anthropic(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class ToolResult(BaseModel):
    tool_use_id: str
    content: str
    is_error: bool = False


# ---------------------------------------------------------------------------
# Registry (GoF Registry pattern)
# ---------------------------------------------------------------------------

Handler = Callable[[dict[str, Any]], str]


class ToolRegistry:
    """Maps tool names to their definitions and handlers.

    Open for extension (register new tools) without modifying existing ones.
    """

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolDefinition, Handler]] = {}

    def register(self, definition: ToolDefinition, handler: Handler) -> None:
        self._tools[definition.name] = (definition, handler)

    def get_definition(self, name: str) -> ToolDefinition:
        return self._tools[name][0]

    def get_handler(self, name: str) -> Handler:
        return self._tools[name][1]

    def all_definitions(self) -> list[ToolDefinition]:
        return [defn for defn, _ in self._tools.values()]

    def execute(self, name: str, tool_use_id: str, inputs: dict[str, Any]) -> ToolResult:
        if name not in self._tools:
            return ToolResult(
                tool_use_id=tool_use_id,
                content=f"Unknown tool: {name}",
                is_error=True,
            )
        try:
            result = self._tools[name][1](inputs)
            return ToolResult(tool_use_id=tool_use_id, content=result)
        except Exception as exc:
            return ToolResult(tool_use_id=tool_use_id, content=str(exc), is_error=True)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


# ---------------------------------------------------------------------------
# Built-in tool handlers (pure functions — no side effects beyond their stated purpose)
# ---------------------------------------------------------------------------


def _handle_read_file(inputs: dict[str, Any]) -> str:
    path = Path(inputs["path"])
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def _handle_run_shell(inputs: dict[str, Any]) -> str:
    command: str = inputs["command"]
    timeout: int = inputs.get("timeout", 30)
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = result.stdout
    if result.stderr:
        output += f"\n[stderr]\n{result.stderr}"
    if result.returncode != 0:
        output += f"\n[exit code: {result.returncode}]"
    return output or "(no output)"


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

READ_FILE_DEFINITION = ToolDefinition(
    name="read_file",
    description="Read the contents of a file from the local filesystem.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative path to the file"},
        },
        "required": ["path"],
    },
)

RUN_SHELL_DEFINITION = ToolDefinition(
    name="run_shell",
    description="Run a shell command and return its output. Use for listing files, running scripts, checking system state.",
    input_schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
        },
        "required": ["command"],
    },
)


def build_default_registry() -> ToolRegistry:
    """Return a registry pre-loaded with the built-in tools."""
    registry = ToolRegistry()
    registry.register(READ_FILE_DEFINITION, _handle_read_file)
    registry.register(RUN_SHELL_DEFINITION, _handle_run_shell)
    return registry
