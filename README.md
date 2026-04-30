# Build Your Own Agent Harness

A step-by-step, runnable Python tutorial for building an LLM agent harness from scratch — 17 layers from API shell to reinforcement learning.

> "If you're using other people's agent harnesses, you don't really own or control your own processes or agents."

This repo teaches you every layer by making you build it. No black boxes.

---

## Who this is for

Any software engineer who wants to understand agent architecture by building it. No ML background required. You need Python and at least one API key.

## What you'll build

A fully functional agent harness with:

| Layer | What you build |
|---|---|
| 1 — API Shell | Multi-provider streaming client (Anthropic, OpenRouter, OpenAI) + REPL |
| 2 — Tools | Typed tool registry, function calling, core agentic loop |
| 3 — Context | Token counting, sliding window, summarization |
| 4 — Memory | SQLite long-term memory with LLM-managed retrieval ← **MVP complete** |
| 5 — Storage | Session persistence, audit log, tool result cache |
| 6 — Streaming | SSE and WebSocket real-time output |
| 7 — MCPs | Model Context Protocol server + client |
| 8 — Orchestration | Prompt chaining, routing, parallelization, reflection |
| 9 — Skills | Reusable capability packages |
| 10 — Hooks | Pre/post-action triggers outside the LLM loop |
| 11 — Queues | Concurrency, rate limiting, background jobs |
| 12 — Sandboxing | Process and container isolation for LLM-generated code |
| 13 — Permissions | Risk classification, human-in-the-loop gates |
| 14 — Guardrails | Token budgets, output validation, runaway loop protection |
| 15 — Session | Resume after interruption, session_id from the start |
| 16 — Local Models | Swap in small models for cheap/fast subtasks |
| 17 — RL | Feedback collection, preference optimization, fine-tuning |

---

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- At least one API key: [OpenRouter](https://openrouter.ai) (recommended — one key, any model) or [Anthropic](https://console.anthropic.com)

---

## Quickstart

Each layer is independent. Start at Layer 1 and progress in order, or jump to any layer.

```bash
# Layer 1 — talk to a model
cd layer-01-api-shell
cp .env.example .env      # add your API key
uv sync
uv run python run.py

# Layer 4 — agent with memory (MVP)
cd layer-04-memory
cp .env.example .env
uv sync
uv run python run.py
```

---

## How layers connect

Each layer imports from the previous one as a local package:

```
MemoryAgentLoop          (Layer 4)
  └── ContextAwareAgentLoop  (Layer 3)
        └── AgentLoop        (Layer 2)
              └── LLMClient  (Layer 1)
```

Later layers extend earlier ones without modifying them — Open/Closed Principle in practice.

---

## Running tests

```bash
# Unit tests — no API keys needed
cd layer-04-memory
uv run pytest tests/ -m "not integration" -v

# Integration tests — requires .env with API keys
uv run pytest tests/ -m integration -v
```

Test counts so far: Layer 1 (10) + Layer 2 (16) + Layer 3 (22) + Layer 4 (28) = **76 unit tests**.

---

## Design principles

Every layer follows these rules:

- **Pydantic for all schemas** — no raw dicts across boundaries
- **Functional core, imperative shell** — pure logic separate from IO
- **SOLID** — single responsibility, open/closed, dependency injection
- **GoF patterns where appropriate** — Registry, Strategy, Template Method, Observer
- **TDD** — failing test before implementation; unit tests mock the network

---

## Reference implementations studied

| Project | What to study |
|---|---|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Memory, skills, RL, full harness architecture |
| [Mastra](https://github.com/mastra-ai/mastra) | TypeScript orchestration and tool wiring |
| [LangGraph](https://github.com/langchain-ai/langgraphjs) | Stateful graph orchestration |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Role-specialized multi-agent structure |

Study these to understand their design decisions — don't just use them. You'll learn more from building a stripped-down version than from depending on the real one.

---

## Contributing

See `CLAUDE.md` for code standards and the layer structure convention.

## License

MIT
