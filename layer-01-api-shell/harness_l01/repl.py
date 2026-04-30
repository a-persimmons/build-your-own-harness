"""
Interactive REPL for the harness.

Run:  python run.py [--provider anthropic|openrouter|openai] [--model MODEL]
"""

import sys
from harness_l01.providers import LLMClient, Message

SYSTEM_PROMPT = "You are a helpful assistant. Be concise."


def run_repl(client: LLMClient) -> None:
    history: list[Message] = []
    print(f"Harness REPL  |  provider={client.provider.value}  model={client.model}")
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

        history.append(Message(role="user", content=user_input))

        print("assistant> ", end="", flush=True)
        full_response = ""
        for chunk in client.stream(history, system=SYSTEM_PROMPT):
            print(chunk, end="", flush=True)
            full_response += chunk
        print()

        history.append(Message(role="assistant", content=full_response))


def collect_response(client: LLMClient, user_input: str, system: str = SYSTEM_PROMPT) -> str:
    """Non-interactive helper: send one message, return full response string."""
    messages = [Message(role="user", content=user_input)]
    return "".join(client.stream(messages, system=system))
