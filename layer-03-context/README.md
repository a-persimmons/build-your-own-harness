# Layer 3 — Context Management

**What you'll build:** Token counting on every turn, and two strategies for what to do when you're running out of context: drop the oldest messages (sliding window) or compress them into a summary (summarization).

**Key concepts:** Strategy pattern, token budgeting, context window as a managed resource.

**Imports from:** `layer-01-api-shell` (`harness_l01`), `layer-02-tools` (`harness_l02`)

---

## Setup

```bash
cp ../layer-01-api-shell/.env.example .env
uv sync
```

## Run the REPL

```bash
# Default: OpenRouter + sliding window
uv run python run.py

# Summarization strategy
uv run python run.py --strategy summarize

# Tight limit to see trimming in action
uv run python run.py --limit 500

# Type 'usage' at the prompt to see token counts per turn
```

## Run tests

```bash
uv run pytest tests/ -m "not integration" -v
uv run pytest tests/ -m integration -v
```

---

## What's in here

| File | Purpose |
|---|---|
| `src/context.py` | `count_tokens`, `SlidingWindow`, `Summarizer`, `ContextManager` |
| `src/agent_loop.py` | `ContextAwareAgentLoop` — extends Layer 2's loop with pre-call trimming |
| `src/repl.py` | REPL with `usage` command to inspect token log |
| `run.py` | CLI with `--strategy` and `--limit` flags |
| `tests/test_context.py` | 22 unit tests + 2 integration tests |

---

## Key decisions made here

**Why tiktoken instead of Anthropic's usage field?**
Anthropic's `usage` field is authoritative but only available *after* the API call. tiktoken gives a fast pre-flight estimate so we can trim the history *before* sending — avoiding a 400 error from context overflow. Approximation is fine here; we're setting a conservative limit anyway.

**Why two strategies instead of one?**
Sliding window is O(n) and free — it just drops messages. Summarization preserves long-range context at the cost of an extra LLM call. Neither is universally better; the right choice depends on how much history matters for the task. The Strategy pattern makes it trivial to swap or add a third approach (e.g., vector retrieval in Layer 4).

**Why does `ContextAwareAgentLoop` extend `AgentLoop` rather than wrap it?**
The context trimming is a pre-processing step in the same call flow — it's not a separate concern that warrants a separate object. Inheritance (Template Method) is the right tool: we override `run()`, call `super()`, and add zero duplication.

---

## How context management fits into the loop

```
run(user_input, history)
    │
    ▼
ContextManager.trim(messages)   ← token count, apply strategy if over limit
    │
    ▼
AgentLoop.run(trimmed_history)  ← inherited from Layer 2
    │
    ▼
[tool-call/result cycle]
    │
    ▼
final response + updated usage_log
```

---

## Next: [Layer 4 — Memory](../layer-04-memory/)
