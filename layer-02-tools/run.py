"""Layer 2 entry point — agentic REPL with tool use."""

import argparse
from dotenv import load_dotenv

load_dotenv()

from harness_l01.providers import get_client
from src.tools import build_default_registry
from src.agent_loop import AgentLoop
from src.repl import run_tool_repl


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness Layer 2 — Tools")
    parser.add_argument("--provider", default="openrouter", choices=["anthropic", "openrouter", "openai"])
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    client = get_client(provider=args.provider, model=args.model)
    registry = build_default_registry()
    loop = AgentLoop(client=client, registry=registry)
    run_tool_repl(loop)


if __name__ == "__main__":
    main()
