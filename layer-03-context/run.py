"""Layer 3 entry point — context-managed agentic REPL."""

import argparse
from dotenv import load_dotenv

load_dotenv()

from harness_l01.providers import get_client
from harness_l02.tools import build_default_registry
from src.context import ContextManager, SlidingWindow, Summarizer
from src.agent_loop import ContextAwareAgentLoop
from src.repl import run_context_repl


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness Layer 3 — Context Management")
    parser.add_argument("--provider", default="openrouter", choices=["anthropic", "openrouter", "openai"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--strategy", default="sliding", choices=["sliding", "summarize"],
                        help="Context management strategy")
    parser.add_argument("--limit", type=int, default=8000, help="Token limit before trimming kicks in")
    args = parser.parse_args()

    client = get_client(provider=args.provider, model=args.model)
    registry = build_default_registry()

    if args.strategy == "summarize":
        strategy = Summarizer(client=client)
    else:
        strategy = SlidingWindow()

    context_manager = ContextManager(strategy=strategy, token_limit=args.limit)
    loop = ContextAwareAgentLoop(client=client, registry=registry, context_manager=context_manager)
    run_context_repl(loop)


if __name__ == "__main__":
    main()
