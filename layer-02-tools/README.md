# Layer 2 — Tools / Function Calling

**What you'll build:** A typed tool registry and the core agentic loop — the moment your harness stops being a chatbot and starts being an agent.

**Key concepts:** Tool definition vs. execution, Registry pattern, the tool-call/result cycle.

**Imports from:** `layer-01-api-shell` (`harness_l01.providers`)

---

## Setup

```bash
cp ../layer-01-api-shell/.env.example .env
# Fill in OPENROUTER_API_KEY (default provider) or ANTHROPIC_API_KEY

uv sync
```

## Run the REPL

```bash
# Default: OpenRouter
uv run python run.py

# Anthropic
uv run python run.py --provider anthropic
```

Try asking: *"What files are in the current directory?"* — the agent will call `run_shell` to answer.

## Run tests

```bash
uv run pytest tests/ -m "not integration" -v
uv run pytest tests/ -m integration -v   # requires API keys
```

---

## What's in here

| File | Purpose |
|---|---|
| `src/tools.py` | `ToolDefinition`, `ToolRegistry`, built-in handlers (`read_file`, `run_shell`) |
| `src/agent_loop.py` | `AgentLoop` — the tool-call/result cycle for Anthropic and OpenAI-compatible providers |
| `src/repl.py` | Interactive REPL for the tool-enabled agent |
| `run.py` | CLI entry point |
| `tests/test_tools.py` | 16 unit tests + 2 integration tests |

---

## Key decisions made here

**Why separate ToolDefinition from the handler?**
The LLM only ever sees the definition (schema + description). The handler is your code. Keeping them separate means you can test handlers in pure isolation — no LLM involved — and swap definitions without touching execution logic.

**Why a Registry instead of a list?**
Name-based lookup is O(1) and the registry is open for extension: you add a tool by calling `registry.register()` without modifying any existing code. This is the Open/Closed Principle in practice.

**Why does AgentLoop use a Template Method structure?**
`run()` defines the fixed skeleton (send → check stop reason → execute tools → repeat). The `_on_tool_calls()` hook is the extension point — override it in a subclass to add logging, audit trails, or human-in-the-loop gates without touching the loop logic.

**Why does the loop own both Anthropic and OpenAI-compatible paths?**
The tool-call protocol differs between providers (Anthropic uses `tool_use` blocks; OpenAI uses `tool_calls`). Normalising to a shared internal dict format in `_call_model()` means everything above it is provider-agnostic.

---

## The agentic loop, visualised

```
user input
    │
    ▼
┌─────────────┐     tool_use      ┌──────────────┐
│  LLM call   │ ────────────────► │ ToolRegistry │
│             │                   │  .execute()  │
│             │ ◄──────────────── │              │
└─────────────┘    tool_result    └──────────────┘
    │ end_turn
    ▼
final text response
```

---

## Next: [Layer 3 — Context Management](../layer-03-context/)
