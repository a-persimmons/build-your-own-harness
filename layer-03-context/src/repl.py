"""Interactive REPL for the context-managed agent."""

from harness_l01.providers import Message
from src.agent_loop import ContextAwareAgentLoop


def run_context_repl(loop: ContextAwareAgentLoop) -> None:
    history: list[Message] = []
    print(f"Layer 3 REPL  |  provider={loop.client.provider.value}  model={loop.client.model}")
    print(f"Strategy: {type(loop.context_manager.strategy).__name__}  limit={loop.context_manager.token_limit} tokens")
    print("Type 'exit' or Ctrl-C to quit. Type 'usage' to see token log.\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Bye.")
            break
        if user_input.lower() == "usage":
            for i, u in enumerate(loop.context_manager.usage_log, 1):
                print(f"  turn {i}: {u.total} tokens total")
            continue

        response = loop.run(user_input, history=history)
        history.append(Message(role="user", content=user_input))
        history.append(Message(role="assistant", content=response))
        print(f"assistant> {response}\n")
