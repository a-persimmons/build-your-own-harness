"""Layer 4 entry point — memory-augmented agentic REPL."""

import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from harness_l01.providers import get_client
from src.memory import MemoryStore
from src.agent_loop import MemoryAgentLoop
from src.repl import run_memory_repl


def main() -> None:
    parser = argparse.ArgumentParser(description="Harness Layer 4 — Memory")
    parser.add_argument("--provider", default="openrouter", choices=["anthropic", "openrouter", "openai"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--db", default="memory.db", help="Path to SQLite database file")
    args = parser.parse_args()

    client = get_client(provider=args.provider, model=args.model)
    store = MemoryStore(db_path=args.db)

    print(f"Memory store: {Path(args.db).resolve()}  ({store.count()} facts stored)")

    loop = MemoryAgentLoop(client=client, store=store)
    run_memory_repl(loop)


if __name__ == "__main__":
    main()
