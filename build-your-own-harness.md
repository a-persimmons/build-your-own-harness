---
tags: [ai-engineering, harness, tooling, career]
sources: [raw/AI Coding/AI coding harnesses.md, Clippings/Rob Conery - I think I found a solution to crap code.md]
updated: 2026-04-29
---

# Build Your Own Agent Harness

The highest-value thing you can do if you're serious about AI engineering. See also: [[agentic-patterns]], [[ai-engineer-roadmap]], [[code-review-workflow]], [[process-driven-ai-coding]].

## The Argument

> If you're using other people's agent harnesses, you don't really own or control your own processes or agents.
> — [@DionysianAgent](https://x.com/DionysianAgent)

You can study an open-source harness (see Reference Implementations below), but if you truly want full control and deep understanding — build your own. Every layer you implement teaches you something no tutorial covers.

## Before You Write Code

Per [[process-driven-ai-coding]] (Rob Conery): don't touch code until you have three bootstrap documents. Have the model interview you to expand each.

| Document | Purpose |
|---|---|
| `SPEC.md` | What you're building and why |
| `ORCHESTRATION.md` | Agent roles, handoffs, flow diagrams (mermaid) |
| `CLAUDE.md` / `AGENTS.md` | Code quality rules, process constraints, tool permissions |

Add `PROJECT_CONTEXT.md` and `ARCHITECTURE.md` via interview sessions before implementing anything.

---

## The Build Sequence

### Layer 1 — API Shell + CLI

Wire up the model API and build a basic REPL or CLI so you can talk to your agent.

**Key decisions:**
- TypeScript or Python? (TS recommended if you're building a product; Python if research/ML heavy)
- Streaming from the start — SSE or streaming SDK methods; retrofitting is painful

**Libraries:**
- [Anthropic TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript) / [Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Vercel AI SDK](https://sdk.vercel.ai/) — provider-agnostic, great streaming primitives
- [OpenRouter](https://openrouter.ai/) — single API for switching models (Claude, GPT, Gemini, local)

---

### Layer 2 — Tools / Function Calling

Give the agent its first tool (e.g. read a file, run a shell command). This is where agentic behavior begins.

**Key decisions:**
- Define tools as typed schemas (Zod in TS, Pydantic in Python)
- Build a tool registry early — a map from tool name → handler function
- Separate tool *definition* from tool *execution* so you can test handlers in isolation

**Libraries:**
- [Zod](https://zod.dev/) — TypeScript schema validation for tool inputs
- [Pydantic](https://docs.pydantic.dev/) — Python equivalent
- Anthropic's native tool use (no extra lib needed — built into the SDK)

---

### Layer 3 — Context Management

The context window fills up. You need a strategy before it becomes a crisis.

**Approaches (pick one to start):**
- **Sliding window** — drop oldest messages when you approach the limit
- **Summarization** — compress prior turns into a summary block; inject at top of context
- **Compaction** — Claude's built-in `/compact` behavior; study it before rolling your own

**Key metric to track:** tokens used per turn. Log it from day one.

**Libraries:**
- [tiktoken](https://github.com/openai/tiktoken) — fast token counting (works for Claude approximations)
- Anthropic's `usage` field on every response — use it

---

### Layer 4 — Memory

Short-term is context. Long-term survives across sessions.

**Two viable architectures in 2026:**

| Approach | Tradeoffs |
|---|---|
| **Vector DB + RAG** | Flexible, semantic search; more setup, embedding cost |
| **SQLite + LLM-managed retrieval** | Simpler, inspectable, no embeddings; less flexible |

Google's "Always On Memory Agent" pattern (2026) uses the SQLite approach — the LLM decides what to store and retrieve, structured as key-value facts. Lower cost, easier to debug.

**Vector DB options:**
- [Chroma](https://www.trychroma.com/) — local-first, great for dev
- [Qdrant](https://qdrant.tech/) — production-ready, Rust-based, fast
- [Pinecone](https://www.pinecone.io/) — fully managed, easiest to start
- [pgvector](https://github.com/pgvector/pgvector) — if you're already on Postgres

**Memory architecture papers worth reading:**
- [Continuum Memory Architecture](https://arxiv.org/html/2601.09913) — persistent state across interactions
- [A-Mem: Agentic Memory for LLM Agents](https://arxiv.org/pdf/2502.12110) — dynamic memory organization

---

### Layer 5 — Storage + Persistence

Decide where state lives before you need it in production.

**Typical schema:**
- Sessions table — conversation history, metadata
- Memory table — long-term facts, embeddings
- Tool results cache — avoid redundant expensive calls
- Audit log — every agent action with timestamp

**Options:**
- [SQLite](https://www.sqlite.org/) / [libsql](https://github.com/tursodatabase/libsql) (Turso) — local-first, serverless-friendly
- [PostgreSQL](https://www.postgresql.org/) — if you need pgvector or complex queries
- [Redis](https://redis.io/) — session state, short-term cache

---

### Layer 6 — Streaming + Real-Time Output

Retrofitting streaming is painful. Build it in from Layer 1 but formalize it here.

**Protocols:**
- **SSE (Server-Sent Events)** — simplest for web clients; one-directional
- **WebSockets** — bidirectional; use when the client needs to interrupt or send mid-stream
- **Polling** — fallback only; avoid

**Libraries:**
- [Hono](https://hono.dev/) — fast TypeScript server with first-class SSE support
- [Fastify](https://fastify.dev/) — Node.js alternative with streaming built in
- Vercel AI SDK's `streamText` / `streamObject` — handles the Claude streaming protocol

---

### Layer 7 — MCPs (Model Context Protocol)

MCP is the "USB-C for AI" — a standard protocol for connecting agents to external tools and data sources without custom integrations.

**When to build an MCP server:**
- You have a data source or tool you want reusable across agents and harnesses
- You want to expose internal APIs to any MCP-compatible client (Claude Code, Cursor, etc.)

**Official resources:**
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) — `@modelcontextprotocol/sdk`
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [modelcontextprotocol.io — Build a Server](https://modelcontextprotocol.io/docs/develop/build-server)
- [Vercel AI SDK MCP integration](https://ai-sdk.dev/docs/ai-sdk-core/mcp-tools)

**Core primitives:**
- **Tools** — actions the LLM can request (computation, side effects)
- **Resources** — read-only data the client can surface
- **Prompts** — reusable templates

---

### Layer 8 — Orchestration

Route tasks to the right agent or tool. Handle multi-step workflows.

**Core patterns (from [[agentic-patterns]]):**
- **Prompt chaining** — sequential steps, output feeds next
- **Routing** — conditional dispatch to specialized agents
- **Parallelization** — independent subtasks run concurrently
- **Reflection** — producer + critic loop

**Frameworks to study (don't necessarily use):**
- [LangGraph](https://github.com/langchain-ai/langgraphjs) — graph-based stateful orchestration; TS + Python
- [Mastra](https://mastra.ai/) — TypeScript-first, YC-backed, 1.0 in Jan 2026; good for products
- [CrewAI](https://github.com/crewAIInc/crewAI) — role-playing multi-agent; Python; 44k+ stars
- [Microsoft Agent Framework](https://github.com/microsoft/autogen) — AutoGen + Semantic Kernel merged; enterprise-grade

> [!tip] Study these frameworks to understand their orchestration patterns, then implement your own version. You'll learn more from building a stripped-down LangGraph than from using the real one.

---

### Layer 9 — Skills and Sub-Agents

Package capabilities as reusable units that the orchestrator can invoke.

**Design principle:** each skill has explicit inputs, explicit outputs, and a clear definition of "done." (Same as [[autonomous-dev-orgs]] role-specialized agents.)

**Reference:**
- [Hermes Agent skills system](https://github.com/NousResearch/hermes-agent) — study `AGENTS.md` for how Nous Research structures skill definitions
- [skills.sh / agent-skills-directory](https://skills.sh) — see [[agent-skills-directory]]

---

### Layer 10 — Hooks and Execution Chains

Pre/post-action triggers that run outside the LLM loop.

**Examples:**
- Before commit: run type-checker, lint
- After tool call: log to audit trail
- Before dangerous action: human-in-the-loop gate
- On session end: compress memory, update long-term store

Claude Code's hooks system (in `settings.json`) is a good reference implementation to study — it's exactly this pattern.

---

### Layer 11 — Queues and Concurrency

When agents run in parallel, you need to manage contention.

**Key problems:**
- Two agents writing to the same file simultaneously
- A slow tool call blocking the main loop
- Rate limits across concurrent API calls

**Libraries:**
- [BullMQ](https://bullmq.io/) — Redis-backed job queue for Node.js; battle-tested
- [p-limit](https://github.com/sindresorhus/p-limit) — simple concurrency limiter for Promise pools
- [Bun's native worker threads](https://bun.sh/docs/api/workers) — if you're on Bun

---

### Layer 12 — Sandboxing

Isolate what the agent can touch. Critical before running LLM-generated code.

**Isolation hierarchy:**
- **Process isolation** — restrict filesystem/network access via OS permissions (cheap, imperfect)
- **Container isolation** — Docker; shared kernel, faster than VMs
- **MicroVM isolation** — Firecracker; each workload gets its own kernel; strongest isolation

**Libraries and services:**
- [E2B](https://e2b.dev/) — purpose-built for AI agents; Firecracker microVMs; ~200ms boot; used by ~half of Fortune 500
- [microsandbox](https://github.com/microsandbox/microsandbox) — open-source embeddable Firecracker runtime
- [Daytona](https://www.daytona.io/) — dev environment sandboxing; E2B alternative

---

### Layer 13 — Permission Systems and Human-in-the-Loop

Gate risky actions. Don't trust the model to self-police.

**Implementation pattern:**
1. Classify every tool by risk level (read-only / reversible write / irreversible)
2. Auto-approve read-only; prompt for reversible; require explicit confirmation for irreversible
3. Log every approval/denial with context

**Reference:** Claude Code's permission system in `settings.json` — `allow`, `deny`, `prompt` per tool pattern.

---

### Layer 14 — Token Budgets and Guardrails

Cost controls and output constraints.

**Key controls:**
- Max tokens per turn
- Max total tokens per session
- Hard stop on runaway loops (max iterations)
- Output schema validation (reject malformed tool calls before they hit the handler)

**Libraries:**
- [Guardrails AI](https://github.com/guardrails-ai/guardrails) — Python; output validation and correction
- [instructor](https://github.com/instructor-ai/instructor) — structured outputs via Pydantic; Python + TS
- [zod-to-json-schema](https://github.com/StefanTerdell/zod-to-json-schema) — generate tool schemas from Zod types

---

### Layer 15 — Session Persistence

Resume a session after interruption. Required for any long-running or background agent.

**Minimum viable implementation:**
- Serialize the message history + tool state to storage after every turn
- On resume, rehydrate and continue
- Track a `session_id` from the start; retrofitting is painful

---

### Layer 16 — Local Models

Swap in a small model for cheap/fast tasks. Reserve the flagship model for hard reasoning.

**Use cases for local:**
- Tool call routing decisions
- Simple summarization
- Extracting structured data from known formats
- Generating embedding vectors

**Options:**
- [Ollama](https://ollama.ai/) — run models locally; dead simple; great for dev
- [llama.cpp](https://github.com/ggerganov/llama.cpp) — C++ runtime; fastest local inference
- [LM Studio](https://lmstudio.ai/) — GUI for local models; good for experimentation
- OpenRouter for model switching without local setup

---

### Layer 17 — Reinforcement Learning

Reward signal, feedback loop, optional fine-tuning. The most advanced layer — skip until the rest is solid.

**Practical starting point:**
- Collect human preference signals (thumbs up/down, corrections) from day one — even before you use them
- Use DPO (Direct Preference Optimization) to fine-tune a small model on your data
- Hermes Agent's RL architecture is the best open-source reference for this layer

**Resources:**
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — study their RL and feedback systems
- TRL library ([Hugging Face](https://github.com/huggingface/trl)) — fine-tuning with RLHF/DPO

---

## Reference Implementations

Study these before and during your build — not to copy, but to understand design decisions:

| Project | Language | What to study |
|---|---|---|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Python/TS | Memory, skills, RL, harness architecture |
| [Mastra](https://github.com/mastra-ai/mastra) | TypeScript | Orchestration, tool wiring, memory |
| [LangGraph](https://github.com/langchain-ai/langgraphjs) | TS + Python | Stateful graph orchestration |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Python | Role-specialized multi-agent structure |
| [OpenHarness](https://github.com/HKUDS/OpenHarness) | Python | Academic; clean five-layer architecture |

Hermes defines five harness layers worth internalizing: **Instruction → Constraint → Feedback → Memory → Orchestration**.

---

## Why It Matters

- When you own your harness, you design it exactly how you want
- You can implement your own RL system and train small models (even 0.5B)
- No other skill has as high a value-to-effort ratio right now
- It is the practical path to [[autonomous-dev-orgs]] — you understand every layer because you built it

> [!tip] Don't try to build all 17 layers at once. Get to Layer 4 (memory) with something working end-to-end, then iterate. A harness that runs is more valuable than a perfect design that doesn't.

---

## Cross-Links

- [[process-driven-ai-coding]] — bootstrap with SPEC.md + ORCHESTRATION.md before touching code
- [[autonomous-dev-orgs]] — the team-scale version of this architecture
- [[agentic-patterns]] — pattern catalog your orchestration layer will implement
- [[agent-skills-directory]] — reusable skill ecosystem to plug into your harness
- [[code-review-workflow]] — example of a harness in practice (the /commit pipeline)
