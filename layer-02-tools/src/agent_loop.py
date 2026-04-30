"""
The core agentic loop.

This is the heart of any agent harness: send messages → model responds →
if the model wants to call a tool, execute it and feed the result back →
repeat until the model returns a plain text response.

Design patterns:
- Template Method: run() defines the fixed skeleton; subclasses can override
  _on_tool_call() and _on_response() to add logging, hooks, etc.
- Single Responsibility: AgentLoop handles flow only; LLMClient handles API;
  ToolRegistry handles execution.
"""

import json
from typing import Any

import anthropic

from harness_l01.providers import LLMClient, Message, Provider
from src.tools import ToolRegistry, ToolResult


class AgentLoop:
    def __init__(
        self,
        client: LLMClient,
        registry: ToolRegistry,
        system: str = "You are a helpful assistant. Use tools when they help answer the question.",
        max_iterations: int = 10,
    ) -> None:
        self.client = client
        self.registry = registry
        self.system = system
        self.max_iterations = max_iterations

    def run(self, user_input: str, history: list[Message] | None = None) -> str:
        """Run the agentic loop for a single user turn. Returns the final text response."""
        messages = list(history or [])
        messages.append(Message(role="user", content=user_input))

        for _ in range(self.max_iterations):
            response = self._call_model(messages)

            if response["stop_reason"] in ("end_turn", "stop"):
                # Plain text response — we're done
                text = self._extract_text(response)
                messages.append(Message(role="assistant", content=text))
                return text

            if response["stop_reason"] == "tool_use":
                # Model wants to call tools — execute them all, feed results back
                tool_calls = [b for b in response["content"] if b["type"] == "tool_use"]
                tool_results = [self._execute_tool(tc) for tc in tool_calls]

                self._on_tool_calls(tool_calls, tool_results)

                # Append assistant turn (with tool_use blocks) then user turn (with results)
                messages.append(Message(role="assistant", content=json.dumps(response["content"])))
                messages.append(Message(role="user", content=json.dumps([
                    {"type": "tool_result", "tool_use_id": r.tool_use_id, "content": r.content}
                    for r in tool_results
                ])))
                continue

            # Unexpected stop reason — surface it
            break

        return "[max iterations reached]"

    def _call_model(self, messages: list[Message]) -> dict[str, Any]:
        """Call the model with tool definitions. Returns the raw response dict."""
        tool_schemas = [t.to_anthropic() for t in self.registry.all_definitions()]

        if self.client.provider == Provider.ANTHROPIC:
            return self._call_anthropic(messages, tool_schemas)
        return self._call_openai_compatible(messages, tool_schemas)

    def _call_anthropic(self, messages: list[Message], tool_schemas: list[dict]) -> dict[str, Any]:
        assert self.client._anthropic is not None
        raw_messages = self._to_anthropic_messages(messages)
        response = self.client._anthropic.messages.create(
            model=self.client.model,
            system=self.system,
            messages=raw_messages,
            tools=tool_schemas,  # type: ignore[arg-type]
            max_tokens=4096,
        )
        content_blocks = []
        for block in response.content:
            if block.type == "text":
                content_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return {"stop_reason": response.stop_reason, "content": content_blocks}

    def _call_openai_compatible(self, messages: list[Message], tool_schemas: list[dict]) -> dict[str, Any]:
        assert self.client._openai is not None
        openai_tools = [t.to_openai() for t in self.registry.all_definitions()]
        raw_messages: list[dict] = [{"role": "system", "content": self.system}]

        for msg in messages:
            # Tool results are stored as JSON strings in our Message model
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, list) and parsed and parsed[0].get("type") == "tool_result":
                    for result in parsed:
                        raw_messages.append({
                            "role": "tool",
                            "tool_call_id": result["tool_use_id"],
                            "content": result["content"],
                        })
                    continue
                if isinstance(parsed, list) and parsed and parsed[0].get("type") in ("text", "tool_use"):
                    # Assistant turn with mixed content
                    text_parts = [b["text"] for b in parsed if b["type"] == "text"]
                    tool_calls = [
                        {
                            "id": b["id"],
                            "type": "function",
                            "function": {"name": b["name"], "arguments": json.dumps(b["input"])},
                        }
                        for b in parsed if b["type"] == "tool_use"
                    ]
                    entry: dict = {"role": msg.role}
                    if text_parts:
                        entry["content"] = " ".join(text_parts)
                    if tool_calls:
                        entry["tool_calls"] = tool_calls
                    raw_messages.append(entry)
                    continue
            except (json.JSONDecodeError, KeyError):
                pass
            raw_messages.append({"role": msg.role, "content": msg.content})

        response = self.client._openai.chat.completions.create(
            model=self.client.model,
            messages=raw_messages,  # type: ignore[arg-type]
            tools=openai_tools,  # type: ignore[arg-type]
            max_tokens=4096,
        )
        choice = response.choices[0]
        content_blocks = []
        if choice.message.content:
            content_blocks.append({"type": "text", "text": choice.message.content})
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments),
                })

        finish = choice.finish_reason
        stop_reason = "tool_use" if finish == "tool_calls" else "end_turn"
        return {"stop_reason": stop_reason, "content": content_blocks}

    def _execute_tool(self, tool_call: dict[str, Any]) -> ToolResult:
        return self.registry.execute(
            name=tool_call["name"],
            tool_use_id=tool_call["id"],
            inputs=tool_call["input"],
        )

    def _extract_text(self, response: dict[str, Any]) -> str:
        return " ".join(
            b["text"] for b in response["content"] if b["type"] == "text"
        )

    def _to_anthropic_messages(self, messages: list[Message]) -> list[dict]:
        result = []
        for msg in messages:
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, list):
                    result.append({"role": msg.role, "content": parsed})
                    continue
            except (json.JSONDecodeError, TypeError):
                pass
            result.append({"role": msg.role, "content": msg.content})
        return result

    # Template Method hooks — override in subclasses to add logging, audit trails, etc.
    def _on_tool_calls(self, tool_calls: list[dict], results: list[ToolResult]) -> None:
        for call, result in zip(tool_calls, results):
            status = "ERROR" if result.is_error else "OK"
            print(f"  [tool] {call['name']}({call['input']}) → {status}")
