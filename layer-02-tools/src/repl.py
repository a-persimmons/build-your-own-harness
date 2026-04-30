"""Interactive REPL for the tool-enabled agent."""

from src.agent_loop import AgentLoop
from harness_l01.providers import Message


def run_tool_repl(loop: AgentLoop) -> None:
    history: list[Message] = []
    print(f"Layer 2 REPL  |  provider={loop.client.provider.value}  model={loop.client.model}")
    print(f"Tools: {[d.name for d in loop.registry.all_definitions()]}")
    print("Type 'exit' or Ctrl-C to quit.\n")

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

        response = loop.run(user_input, history=history)

        # Update history with the completed turn
        history.append(Message(role="user", content=user_input))
        history.append(Message(role="assistant", content=response))

        print(f"assistant> {response}\n")
