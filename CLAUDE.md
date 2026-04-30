# Build Your Own Harness — Claude Instructions

## What this repo is
A step-by-step tutorial for building an LLM agent harness from scratch in Python. Each numbered layer is a self-contained `uv` project that extends the previous one.

## Layer structure
- Each layer lives in `layer-NN-name/`
- Source code: `layer-NN-name/src/` — local imports use `from src.X`
- Installable package: `layer-NN-name/harness_lNN/` — cross-layer imports use `from harness_lNN.X`
- Entry point: `layer-NN-name/run.py`
- Tests: `layer-NN-name/tests/`

## Adding a new layer
1. `uv init layer-NN-name --python 3.12`
2. Add prior layers as path dependencies in `pyproject.toml`
3. Create `src/`, `harness_lNN/`, `tests/` directories
4. Add `[build-system]` + `[tool.hatch.build.targets.wheel]` to `pyproject.toml`
5. Mirror `src/` into `harness_lNN/` with corrected imports (so it's installable)
6. Write failing tests first (Red), then implement (Green)

## Cross-layer imports
| From | Import as |
|---|---|
| Layer 1 providers/repl | `from harness_l01.providers import ...` |
| Layer 2 tools/agent_loop | `from harness_l02.tools import ...` |
| Layer 3 context/agent_loop | `from harness_l03.context import ...` |
| Layer 4 memory | `from harness_l04.memory import ...` |

## Code standards
- Python 3.12+, `uv` only (never `pip` directly)
- Pydantic for all schemas at layer boundaries — never raw dicts
- Functional core, imperative shell: pure logic separate from IO
- SOLID principles throughout; GoF patterns where they add clarity (not everywhere)
- Red/Green TDD: failing test before implementation
- Unit tests mock the network; integration tests hit real APIs and are marked `@pytest.mark.integration`
- Default provider is OpenRouter (lower barrier to entry); Anthropic is an option

## Running tests
```bash
# Unit tests (no API keys needed)
uv run pytest tests/ -m "not integration" -v

# Integration tests (requires .env with API keys)
uv run pytest tests/ -m integration -v
```

## Never commit
- `.env` files
- `*.db` / `*.sqlite` files
- `.venv/` directories
