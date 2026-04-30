"""Entry point — wire env, parse args, launch REPL."""

import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

from harness_l01.providers import get_client
from harness_l01.repl import run_repl


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness Layer 1 REPL")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openrouter", "openai"])
    parser.add_argument("--model", default=None, help="Override the default model for the provider")
    args = parser.parse_args()

    client = get_client(provider=args.provider, model=args.model)
    run_repl(client)


if __name__ == "__main__":
    main()
