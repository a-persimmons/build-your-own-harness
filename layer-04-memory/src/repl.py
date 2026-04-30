"""Interactive REPL for the memory-augmented agent."""

from harness_l01.providers import Message
from src.agent_loop import MemoryAgentLoop


def run_memory_repl(loop: MemoryAgentLoop) -> None:
    history: list[Message] = []
    print(f"Layer 4 REPL  |  provider={loop.client.provider.value}  model={loop.client.model}")
    print("Memory tools: remember, recall, forget")
    print("Commands: 'memories' = show all stored, 'exit' = quit\n")

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
        if user_input.lower() == "memories":
            print(loop.store.format_all())
            print()
            continue

        response = loop.run(user_input, history=history)
        history.append(Message(role="user", content=user_input))
        history.append(Message(role="assistant", content=response))
        print(f"assistant> {response}\n")
