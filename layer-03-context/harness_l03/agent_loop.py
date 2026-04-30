"""
Context-aware agent loop.

Extends Layer 2's AgentLoop (Template Method inheritance) with one addition:
history is trimmed by a ContextManager before every LLM call.

This is the Open/Closed Principle in action: AgentLoop is open for extension
(subclass it) and closed for modification (we don't touch Layer 2's code).
"""

from harness_l01.providers import LLMClient, Message
from harness_l02.agent_loop import AgentLoop
from harness_l02.tools import ToolRegistry
from harness_l03.context import ContextManager


class ContextAwareAgentLoop(AgentLoop):
    def __init__(
        self,
        client: LLMClient,
        registry: ToolRegistry,
        context_manager: ContextManager,
        system: str = "You are a helpful assistant. Use tools when they help answer the question.",
        max_iterations: int = 10,
    ) -> None:
        super().__init__(client=client, registry=registry, system=system, max_iterations=max_iterations)
        self.context_manager = context_manager

    def run(self, user_input: str, history: list[Message] | None = None) -> str:
        messages = list(history or [])
        messages.append(Message(role="user", content=user_input))
        trimmed = self.context_manager.trim(messages, self.system)

        usage = self.context_manager.last_usage
        if usage:
            print(f"  [context] {usage.total} tokens ({usage.messages} msg + {usage.system} sys) — {len(messages) - len(trimmed)} messages dropped")

        # Run the parent loop with the trimmed history (minus the appended user msg,
        # since parent.run() will append it again)
        trimmed_history = trimmed[:-1] if trimmed and trimmed[-1].role == "user" and trimmed[-1].content == user_input else trimmed
        return super().run(user_input, history=trimmed_history)
