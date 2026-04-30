# Layer 4 — Memory

**What you'll build:** Long-term memory that survives across sessions — backed by SQLite, managed by the LLM itself. The agent decides what to store, what to retrieve, and what to forget.

**Key concepts:** Repository pattern, LLM-managed memory, memory as tools, system prompt injection.

**Imports from:** `layer-01` (`harness_l01`), `layer-02` (`harness_l02`), `layer-03` (`harness_l03`)

---

## Setup

```bash
cp ../layer-01-api-shell/.env.example .env
uv sync
```

## Run the REPL

```bash
# Default: OpenRouter, persists to memory.db
uv run python run.py

# Custom DB path (resume a previous session)
uv run python run.py --db sessions/alice.db

# Type 'memories' at the prompt to inspect what's stored
```

Try this sequence:
1. *"My name is Alex and I'm building an agent harness."*
2. Exit with `exit`
3. Run again — ask *"What do you know about me?"*

The agent will recall what it stored in the previous session.

## Run tests

```bash
uv run pytest tests/ -m "not integration" -v
uv run pytest tests/ -m integration -v
```

---

## What's in here

| File | Purpose |
|---|---|
| `src/memory.py` | `MemoryRecord` (Pydantic), `MemoryStore` (SQLite repository) |
| `src/memory_tools.py` | `remember`, `recall`, `forget` tools + `memory_system_prompt()` |
| `src/agent_loop.py` | `MemoryAgentLoop` — extends Layer 3 with memory tools + prompt injection |
| `src/repl.py` | REPL with `memories` command |
| `run.py` | CLI with `--db` flag for persistent sessions |
| `tests/test_memory.py` | 28 unit tests + 2 integration tests |

---

## Key decisions made here

**Why LLM-managed retrieval instead of auto-injection?**
Automatically injecting all memories into every prompt is expensive and noisy — 1000 stored facts would flood the context window. Instead, we give the model `recall` as a tool: it only fetches what's relevant to the current turn. This matches Google's 2026 "Always On Memory Agent" architecture.

**Why SQLite over a vector database?**
No embeddings, no external service, fully inspectable with any SQLite client. Full-text substring search covers most retrieval needs. Layer 4 is designed to be swappable — a future layer could replace `MemoryStore` with a pgvector-backed implementation behind the same interface.

**Why expose memory as tools rather than a separate pipeline?**
It keeps the architecture simple: the agent loop already knows how to call tools and handle results. Adding memory as three more tools costs nothing architecturally and teaches the same lesson as domain tools — the LLM drives everything.

**Why inject a memory summary into the system prompt anyway?**
The `recall` tool handles on-demand retrieval. The system prompt summary is a fast-path: the model sees recently-stored facts without having to call a tool first. It's a compact snapshot, not the full store.

---

## Architecture: the full stack after Layer 4

```
MemoryAgentLoop          (Layer 4) — memory tools + prompt injection
    └── ContextAwareAgentLoop  (Layer 3) — token counting + window strategy
            └── AgentLoop      (Layer 2) — tool-call/result loop
                    └── LLMClient  (Layer 1) — streaming, multi-provider
```

Each layer adds one concern. None modifies the layer below it.

---

## MVP complete ✓

You now have a working agent harness with:
- Multi-provider streaming (Layer 1)
- Typed tool registry + agentic loop (Layer 2)
- Context management with sliding window and summarization (Layer 3)
- Persistent long-term memory with LLM-managed retrieval (Layer 4)

Layers 5–17 add production concerns: storage schemas, streaming protocols, MCPs, orchestration, sandboxing, and RL.

## Next: [Layer 5 — Storage + Persistence](../layer-05-storage/)
