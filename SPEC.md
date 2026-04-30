# Build Your Own Harness — Spec

## Purpose
A step-by-step, runnable Python tutorial that teaches any engineer how to build an LLM agent harness from scratch, covering all 17 layers from API shell to reinforcement learning.

## Problem
Engineers using other people's agent frameworks (LangChain, CrewAI, Mastra) don't understand what's happening under the hood — and can't control or debug it when things go wrong. The alternative today is either black-box frameworks or scattered blog posts with no runnable code.

## Users
Any software engineer who wants to understand agent architecture by building it themselves. No ML background required. Target reader can write Python and has used an LLM API at least once.

## MVP
Layers 1–4 complete and runnable, with a root README that explains the full arc:

- **Layer 1** — API shell: multi-provider client (Anthropic + OpenRouter), streaming, interactive REPL
- **Layer 2** — Tools: typed tool registry, function calling, tool execution loop
- **Layer 3** — Context management: token tracking, sliding window, summarization
- **Layer 4** — Memory: short-term (context) + long-term (SQLite), LLM-managed retrieval

Each layer has: runnable `run.py`, passing tests, and a `README.md` that explains the key decisions.

## Out of Scope (v1)
- Hosted/deployed version (local only)
- Web UI or frontend
- Layers 5–17 (shipped iteratively after MVP is validated)
- Fine-tuning or RL (Layer 17 — last)
- Multi-language parity (Python only)

## Constraints
- Python 3.12+ with `uv` for package management
- Anthropic SDK + OpenRouter for multi-provider support
- Each layer must run independently with `uv run python run.py`
- No deadline
- Public GitHub repo under `djscruggs` account

## Quality Priorities
1. **Clarity** — code teaches, not just works; minimal abstractions; no clever one-liners
2. **Correctness** — every layer has unit tests (mocked) + integration tests (live API)
3. **Maintainability** — layers extend cleanly; later layers import from earlier ones without circular deps
4. **Performance** — not a priority

## Design Principles
- **Functional core, imperative shell** — pure business logic separate from IO at every layer
- **Pydantic for all schemas** — tool inputs, messages, memory records; enforced at boundaries
- **SOLID** — single responsibility per class, open/closed for new providers/tools, dependency injection at composition root
- **Gang of Four patterns where appropriate** — e.g. Registry (tool registry), Strategy (provider selection), Observer (hooks in later layers)
- **Red/Green TDD** — failing test before implementation; unit tests mock network; integration tests hit real APIs

## Open Questions
_None for MVP. Resolved decisions:_
- Layers import from previous `src/` directories (real composition, not copy-paste)
- Default provider is OpenRouter from Layer 2 onward (lower barrier — one key covers all models)
