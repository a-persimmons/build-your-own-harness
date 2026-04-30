# Layer 1 — API Shell + CLI

**What you'll build:** A multi-provider LLM client with streaming output and an interactive REPL.

**Key concepts:** Provider abstraction, streaming vs. blocking, message history.

---

## Setup

```bash
cp .env.example .env
# Fill in at least one API key in .env

uv sync
```

## Run the REPL

```bash
# Anthropic (default)
uv run python run.py

# OpenRouter (any model via one API)
uv run python run.py --provider openrouter

# Specific model override
uv run python run.py --provider anthropic --model claude-haiku-4-5-20251001
```

## Run tests

```bash
# Unit tests only (no API key needed)
uv run pytest tests/ -m "not integration" -v

# Integration tests (require API keys in .env)
uv run pytest tests/ -m integration -v
```

---

## What's in here

| File | Purpose |
|---|---|
| `src/providers.py` | `LLMClient` — wraps Anthropic + OpenAI-compatible providers behind one `stream()` interface |
| `src/repl.py` | Interactive REPL and `collect_response()` helper |
| `run.py` | CLI entry point with `--provider` / `--model` flags |
| `tests/test_providers.py` | Unit tests (mocked) + integration tests (live API) |

---

## Key decisions made here

**Why OpenAI SDK for non-Anthropic providers?**
OpenRouter, OpenAI, Ollama, and most new providers implement the OpenAI-compatible REST API. Using the `openai` SDK for all of them means one code path handles everything — no custom HTTP clients.

**Why stream from day 1?**
Retrofitting streaming into a blocking architecture is painful. Starting with `stream()` as the primitive means every layer above gets streaming for free.

**Why `Message` as a Pydantic model?**
It enforces the `role` / `content` shape at the boundary. Later layers will extend this model with metadata (token counts, tool calls) — having it typed from the start prevents silent schema drift.

---

## Next: [Layer 2 — Tools / Function Calling](../layer-02-tools/)
