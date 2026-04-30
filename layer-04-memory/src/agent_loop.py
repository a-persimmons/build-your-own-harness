"""
Memory-augmented agent loop.

Extends Layer 3's ContextAwareAgentLoop with:
1. Memory tools registered alongside domain tools
2. System prompt refreshed with current memories before every call
3. Persistent MemoryStore injected at construction

Inheritance chain: MemoryAgentLoop → ContextAwareAgentLoop → AgentLoop
Each layer adds one concern without modifying the layers below it.
"""

from harness_l01.providers import LLMClient, Message
from harness_l02.tools import ToolRegistry, build_default_registry
from harness_l03.context import ContextManager, SlidingWindow
from harness_l03.agent_loop import ContextAwareAgentLoop
from src.memory import MemoryStore
from src.memory_tools import build_memory_registry, memory_system_prompt

_BASE_SYSTEM = (
    "You are a helpful assistant with long-term memory. "
    "Use the remember tool to store important facts the user shares. "
    "Use the recall tool when you need to look something up. "
    "Use your tools to answer questions accurately."
)


class MemoryAgentLoop(ContextAwareAgentLoop):
    def __init__(
        self,
        client: LLMClient,
        store: MemoryStore,
        extra_registry: ToolRegistry | None = None,
        context_manager: ContextManager | None = None,
        max_iterations: int = 10,
    ) -> None:
        memory_registry = build_memory_registry(store)

        # Merge memory tools + any extra domain tools into one registry
        combined = ToolRegistry()
        for defn in memory_registry.all_definitions():
            combined.register(defn, memory_registry.get_handler(defn.name))

        domain = extra_registry or build_default_registry()
        for defn in domain.all_definitions():
            combined.register(defn, domain.get_handler(defn.name))

        cm = context_manager or ContextManager(strategy=SlidingWindow(), token_limit=8_000)

        super().__init__(
            client=client,
            registry=combined,
            context_manager=cm,
            system=_BASE_SYSTEM,
            max_iterations=max_iterations,
        )
        self.store = store

    def run(self, user_input: str, history: list[Message] | None = None) -> str:
        # Refresh system prompt with latest memories before every turn
        self.system = memory_system_prompt(self.store, _BASE_SYSTEM)
        return super().run(user_input, history=history)
