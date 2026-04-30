# Build Your Own Harness — Architecture

## Deployment Target
Local only. Each layer runs on the developer's machine with `uv run python run.py`. No server, no cloud deployment.

## External Dependencies
| Service | Purpose | Required from |
|---|---|---|
| Anthropic API | Primary LLM provider | Layer 1 |
| OpenRouter | Multi-provider gateway (OpenAI-compatible) | Layer 1 |
| OpenAI API | Optional third provider | Layer 1 |
| SQLite | Long-term memory storage | Layer 4 |

## Structure
**Layered monorepo.** Each layer is a self-contained folder that extends the previous:

```
build-your-own-harness/
├── SPEC.md
├── ARCHITECTURE.md
├── CLAUDE.md
├── README.md
├── layer-01-api-shell/
│   ├── src/
│   ├── tests/
│   ├── run.py
│   └── README.md
├── layer-02-tools/
│   ├── src/        ← imports from layer-01 src/
│   ├── tests/
│   ├── run.py
│   └── README.md
└── ...
```

Each layer directory is a standalone `uv` project with its own `pyproject.toml` and `.venv`. Later layers import from earlier layers' `src/` directories via relative path or installed as local packages.

## Key Principles

- **Functional core, imperative shell** — pure functions handle all logic; IO (API calls, file reads, DB writes) lives at the shell boundary
- **Pydantic for all schemas** — `Message`, tool input/output, memory records; never pass raw dicts across layer boundaries
- **Dependency injection at composition root** — `LLMClient`, storage backends, and tool registries are constructed in `run.py` and injected down; nothing instantiates its own dependencies internally
- **SOLID throughout:**
  - *Single Responsibility* — one class per concern (client, registry, memory store)
  - *Open/Closed* — add providers and tools without modifying existing classes
  - *Liskov* — all providers satisfy the same `stream()` interface
  - *Interface Segregation* — clients only depend on the interface they use
  - *Dependency Inversion* — high-level orchestration depends on abstractions, not concrete providers
- **GoF patterns applied deliberately:**
  - *Strategy* — provider selection (`LLMClient` wraps interchangeable backends)
  - *Registry* — tool registry (Layer 2): name → handler map
  - *Observer* — hooks system (Layer 10): pre/post action triggers
  - *Template Method* — base agent loop with overridable steps (Layer 8+)

## Critical Paths
- **Streaming pipeline** — must work end-to-end from Layer 1; retrofitting is expensive
- **Tool execution loop** — the core agentic loop introduced in Layer 2; all later layers extend it
- **Message schema** — `Message` model is the data contract between every layer; changes here are breaking

## Boundaries

| Boundary | What crosses it |
|---|---|
| Layer → LLM API | `LLMClient.stream()` — only `list[Message]` and `system: str` |
| Layer → Storage | Repository interface — only domain models (never raw SQL outside the repo) |
| Tool definition → Tool execution | Tool registry — only `ToolInput` Pydantic models |
| Layers → each other | `src/` imports — only stable public interfaces, never internal helpers |

## Decisions Log
| Decision | Rationale | Date |
|---|---|---|
| Python over TypeScript | Tutorial audience; easier onboarding; ML ecosystem parity | 2026-04-29 |
| OpenAI SDK for non-Anthropic providers | OpenRouter + OpenAI share the same REST interface; one code path covers both | 2026-04-29 |
| uv over pip/poetry | Fast, modern, reproducible; aligns with current Python best practices | 2026-04-29 |
| Stream-first from Layer 1 | Retrofitting streaming into blocking architecture is costly | 2026-04-29 |
| Pydantic for all schemas | Enforces contracts at boundaries; enables IDE autocomplete; catches bugs early | 2026-04-29 |
| SQLite for long-term memory (Layer 4) | Local-first, zero infrastructure, inspectable; matches Google's 2026 "Always On Memory" pattern | 2026-04-29 |
| Layers import from previous src/ | Teaches real composition; mirrors how a production harness grows; readers follow the full arc | 2026-04-29 |
| Default provider is OpenRouter | Lowers barrier to entry — readers need one key instead of per-provider keys | 2026-04-29 |
