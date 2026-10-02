---
tags: [ai-engineering, harness, tooling, career]
sources: [raw/AI Coding/AI coding harnesses.md, Clippings/Rob Conery - I think I found a solution to crap code.md]
updated: 2026-04-29
---

# 从零构建 Agent Harness

如果你认真投入 AI 工程，原文作者认为这是最值得做的事情。另见：[[agentic-patterns]]、[[ai-engineer-roadmap]]、[[code-review-workflow]]、[[process-driven-ai-coding]]。

## 为什么值得做

> 如果你使用的是别人提供的 Agent Harness，你就没有真正拥有或掌控自己的流程与 Agent。
> — [@DionysianAgent](https://x.com/DionysianAgent)

你可以研究开源 Harness，下面列出了参考实现。但如果你希望获得充分控制和深入理解，就亲手构建一个。实现每一层都会让你学到仅靠阅读教程不容易获得的经验。

## 写代码之前

按照 [[process-driven-ai-coding]] 中 Rob Conery 的建议，先准备三份启动文档，再开始写代码。让模型通过访谈帮助你逐步补充每份文档。

| 文档 | 用途 |
|---|---|
| `SPEC.md` | 要构建什么，为什么构建 |
| `ORCHESTRATION.md` | Agent 角色、交接方式、Mermaid 流程图 |
| `CLAUDE.md` / `AGENTS.md` | 代码质量规则、流程约束、工具权限 |

在实现之前，再通过访谈补充 `PROJECT_CONTEXT.md` 和 `ARCHITECTURE.md`。

---

## 构建顺序

### 第 1 层 — API 外壳与命令行

连接模型 API，构建基础 REPL 或 CLI，让你能够与 Agent 对话。

**关键决策：**

- TypeScript 还是 Python？原文建议产品开发优先考虑 TS，研究或机器学习任务较多时考虑 Python。
- 从一开始就支持流式输出，使用 SSE 或 SDK 的流式方法；事后改造比较麻烦。

**库：**

- [Anthropic TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript) / [Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Vercel AI SDK](https://sdk.vercel.ai/)：与供应商解耦，提供便利的流式基础能力。
- [OpenRouter](https://openrouter.ai/)：通过一个 API 切换 Claude、GPT、Gemini、本地模型等。

---

### 第 2 层 — 工具与函数调用

给 Agent 第一个工具，例如读取文件或执行 shell 命令。Agent 的行动能力从这里开始。

**关键决策：**

- 使用带类型约束的数据模式定义工具：TS 使用 Zod，Python 使用 Pydantic。
- 尽早构建工具注册表，将工具名称映射到处理函数。
- 将工具的*定义*与*执行*分开，以便独立测试处理函数。

**库：**

- [Zod](https://zod.dev/)：在 TypeScript 中校验工具输入。
- [Pydantic](https://docs.pydantic.dev/)：Python 中的对应选择。
- Anthropic 原生工具调用：SDK 已内置，无需额外库。

---

### 第 3 层 — 上下文管理

上下文窗口终会填满，要提前准备处理策略。

**可选方案，先实现一种：**

- **滑动窗口**：接近上限时删除最旧的消息。
- **摘要**：将前面的对话压缩为摘要块，放在上下文顶部。
- **压缩整理（Compaction）**：研究 Claude 内置的 `/compact` 行为，再考虑自己的实现。

**关键指标：** 每轮使用的 Token 数量。从第一天起就记录。

**库与接口：**

- [tiktoken](https://github.com/openai/tiktoken)：快速计算 Token，也可用于近似估算 Claude 的用量。
- Anthropic 每次响应中的 `usage` 字段：把它利用起来。

---

### 第 4 层 — 记忆

短期记忆属于上下文，长期记忆需要跨会话保留。

**原文提出的两种 2026 年可选架构：**

| 方案 | 取舍 |
|---|---|
| **向量数据库 + RAG** | 灵活，支持语义搜索；配置更多，并有嵌入计算成本 |
| **SQLite + LLM 管理检索** | 简单、容易查看、不需要嵌入；灵活性较低 |

原文以 Google 的 “Always On Memory Agent”（2026）模式为例说明 SQLite 方案：LLM 决定存储和检索什么，信息组织为键值事实，成本较低，也更便于调试。

**向量数据库选项：**

- [Chroma](https://www.trychroma.com/)：本地优先，适合开发。
- [Qdrant](https://qdrant.tech/)：面向生产，基于 Rust，速度快。
- [Pinecone](https://www.pinecone.io/)：完全托管，便于起步。
- [pgvector](https://github.com/pgvector/pgvector)：适合已经使用 Postgres 的项目。

**值得阅读的记忆架构论文：**

- [Continuum Memory Architecture](https://arxiv.org/html/2601.09913)：跨交互的持久状态。
- [A-Mem: Agentic Memory for LLM Agents](https://arxiv.org/pdf/2502.12110)：动态组织记忆。

---

### 第 5 层 — 存储与持久化

在真正进入生产之前，先决定状态保存在哪里。

**典型数据结构：**

- 会话表：对话历史、元数据。
- 记忆表：长期事实、嵌入向量。
- 工具结果缓存：避免重复执行昂贵调用。
- 审计日志：记录每次 Agent 行为及时间戳。

**选项：**

- [SQLite](https://www.sqlite.org/) / [libsql](https://github.com/tursodatabase/libsql)（Turso）：本地优先，对无服务器场景友好。
- [PostgreSQL](https://www.postgresql.org/)：需要 pgvector 或复杂查询时可选。
- [Redis](https://redis.io/)：会话状态、短期缓存。

---

### 第 6 层 — 流式与实时输出

事后补流式输出很麻烦。从第 1 层就实现流式能力，在这一层正式整理协议与接口。

**协议：**

- **SSE（Server-Sent Events）**：Web 客户端的简单方案，单向传输。
- **WebSocket**：双向通信，适合客户端需要打断或在输出途中发送消息的场景。
- **轮询**：原文建议只作为兜底，尽量避免。

**库：**

- [Hono](https://hono.dev/)：快速的 TypeScript 服务端框架，原生支持 SSE。
- [Fastify](https://fastify.dev/)：Node.js 的另一种选择，内置流式能力。
- Vercel AI SDK 的 `streamText` / `streamObject`：原文用它们举例说明对 Claude 流式协议的处理。

---

### 第 7 层 — MCP（Model Context Protocol）

MCP 常被比喻为“AI 的 USB-C”：通过标准协议，将 Agent 连接到外部工具和数据源，减少逐一编写定制集成的工作。

**什么时候构建 MCP 服务端：**

- 你有一个工具或数据源，希望跨 Agent、跨 Harness 复用。
- 你希望把内部 API 暴露给兼容 MCP 的客户端，例如 Claude Code、Cursor。

**官方资源：**

- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)：`@modelcontextprotocol/sdk`
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [modelcontextprotocol.io — 构建服务端](https://modelcontextprotocol.io/docs/develop/build-server)
- [Vercel AI SDK 的 MCP 集成](https://ai-sdk.dev/docs/ai-sdk-core/mcp-tools)

**核心原语：**

- **Tools**：LLM 可以请求的动作，例如计算或产生副作用的操作。
- **Resources**：客户端可以呈现的只读数据。
- **Prompts**：可复用模板。

---

### 第 8 层 — 编排

将任务分派给适合的 Agent 或工具，处理多步骤工作流。

**核心模式，来自 [[agentic-patterns]]：**

- **提示词链**：顺序执行，前一步输出作为后一步输入。
- **路由**：按条件分派给专门的 Agent。
- **并行处理**：独立子任务并发执行。
- **反思**：生成者与评审者构成循环。

**值得研究的框架，不一定要直接采用：**

- [LangGraph](https://github.com/langchain-ai/langgraphjs)：基于图的有状态编排，支持 TS 与 Python。
- [Mastra](https://mastra.ai/)：TypeScript 优先、获 YC 支持；原文记载其在 2026 年 1 月发布 1.0，适合产品开发。
- [CrewAI](https://github.com/crewAIInc/crewAI)：按角色组织多 Agent，使用 Python；原文记录有 4.4 万以上 Star。
- [Microsoft Agent Framework](https://github.com/microsoft/autogen)：原文将其描述为 AutoGen 与 Semantic Kernel 合并后的企业级框架。

> [!tip] 先研究这些框架的编排模式，再实现自己的版本。亲手写一个精简的 LangGraph，可能比直接使用完整框架学得更多。

---

### 第 9 层 — 技能与子 Agent

将能力打包成可复用单元，由编排器调用。

**设计原则：** 每个技能都有明确输入、明确输出，以及清晰的“完成”定义。与 [[autonomous-dev-orgs]] 中按角色分工的 Agent 思路相同。

**参考：**

- [Hermes Agent 技能系统](https://github.com/NousResearch/hermes-agent)：研究其 `AGENTS.md`，了解 Nous Research 如何组织技能定义。
- [skills.sh / agent-skills-directory](https://skills.sh)：另见 [[agent-skills-directory]]。

---

### 第 10 层 — 钩子与执行链

在 LLM 循环之外运行的动作前后触发器。

**示例：**

- 提交之前：运行类型检查和 lint。
- 工具调用之后：写入审计记录。
- 危险操作之前：设置人工审批关口。
- 会话结束时：压缩记忆，更新长期存储。

Claude Code 在 `settings.json` 中配置的钩子系统，是原文建议研究的参考实现，体现了这一模式。

---

### 第 11 层 — 队列与并发

多个 Agent 并行运行时，需要管理资源竞争。

**关键问题：**

- 两个 Agent 同时写同一个文件。
- 缓慢的工具调用阻塞主循环。
- 多个并发 API 调用触发限流。

**库：**

- [BullMQ](https://bullmq.io/)：Node.js 中基于 Redis 的成熟任务队列。
- [p-limit](https://github.com/sindresorhus/p-limit)：用于 Promise 池的简单并发限制器。
- [Bun 原生工作线程](https://bun.sh/docs/api/workers)：使用 Bun 时可以考虑。

---

### 第 12 层 — 沙箱

隔离 Agent 能接触的资源。在运行 LLM 生成的代码之前，这一点尤其重要。

**隔离层次：**

- **进程隔离**：通过操作系统权限限制文件系统和网络访问，成本低但并不完善。
- **容器隔离**：例如 Docker，共享内核，比虚拟机启动更快。
- **MicroVM 隔离**：例如 Firecracker，每个工作负载拥有自己的内核；原文将它列为这三种方案中隔离最强的一种。

**库与服务：**

- [E2B](https://e2b.dev/)：面向 AI Agent，使用 Firecracker MicroVM；原文列出约 200ms 启动、约半数财富 500 强使用等描述，这些是原文当时的说法。
- [microsandbox](https://github.com/microsandbox/microsandbox)：原文将其描述为开源、可嵌入的 Firecracker 运行时。
- [Daytona](https://www.daytona.io/)：开发环境沙箱，可作为 E2B 的替代选项。

---

### 第 13 层 — 权限系统与人工介入

为高风险行为设置审批关口，不依赖模型自我约束。

**原文提出的实现模式：**

1. 为每个工具划分风险等级：只读、可逆写入、不可逆操作。
2. 只读自动批准，可逆操作询问用户，不可逆操作要求明确确认。
3. 记录每次批准或拒绝及其上下文。

**参考：** Claude Code 的 `settings.json` 权限系统；原文以按工具模式配置 `allow`、`deny`、`prompt` 为例。

---

### 第 14 层 — Token 预算与护栏

控制成本，并约束输出。

**关键控制项：**

- 每轮最大 Token 数。
- 每个会话的 Token 总上限。
- 通过最大迭代次数，强制停止失控循环。
- 校验输出模式，在不合法的工具调用进入处理函数之前拒绝它。

**库：**

- [Guardrails AI](https://github.com/guardrails-ai/guardrails)：Python 输出校验与修正。
- [instructor](https://github.com/instructor-ai/instructor)：通过 Pydantic 实现结构化输出；原文列出 Python 与 TS 支持。
- [zod-to-json-schema](https://github.com/StefanTerdell/zod-to-json-schema)：从 Zod 类型生成工具数据模式。

---

### 第 15 层 — 会话持久化

中断后恢复会话，这是长时间运行或后台 Agent 需要的能力。

**最小可用实现：**

- 每轮结束后，将消息历史和工具状态序列化到存储中。
- 恢复时重新载入状态，继续执行。
- 从一开始就跟踪 `session_id`，避免后期补加的麻烦。

---

### 第 16 层 — 本地模型

用小模型承担低成本、低延迟任务，把旗舰模型留给困难推理。

**适合本地模型的场景：**

- 工具调用路由决策。
- 简单摘要。
- 从已知格式中提取结构化数据。
- 生成嵌入向量。

**选项：**

- [Ollama](https://ollama.ai/)：在本地运行模型，简单易用，适合开发。
- [llama.cpp](https://github.com/ggerganov/llama.cpp)：C++ 运行时；原文评价其本地推理速度最快。
- [LM Studio](https://lmstudio.ai/)：本地模型的图形界面，便于实验。
- OpenRouter：无需本地配置，就可以切换模型。

---

### 第 17 层 — 强化学习

奖励信号、反馈闭环，以及可选的微调。这是最进阶的一层，先把其他层做稳，再考虑它。

**务实的起点：**

- 从第一天就收集人工偏好信号，例如赞、踩和纠正，即使暂时还用不上。
- 用 DPO（直接偏好优化）在自己的数据上微调小模型。
- 原文作者认为，Hermes Agent 的强化学习架构是这一层最值得研究的开源参考。

**资源：**

- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)：研究其强化学习和反馈系统。
- TRL 库（[Hugging Face](https://github.com/huggingface/trl)）：用于 RLHF/DPO 微调。

---

## 参考实现

在构建之前和构建过程中研究这些项目，目的是理解设计决策，而不只是照搬代码：

| 项目 | 语言 | 值得研究的部分 |
|---|---|---|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Python/TS | 记忆、技能、强化学习、Harness 架构 |
| [Mastra](https://github.com/mastra-ai/mastra) | TypeScript | 编排、工具连接、记忆 |
| [LangGraph](https://github.com/langchain-ai/langgraphjs) | TS + Python | 有状态的图编排 |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Python | 按角色分工的多 Agent 结构 |
| [OpenHarness](https://github.com/HKUDS/OpenHarness) | Python | 学术项目，清晰的五层架构 |

原文归纳了 Hermes 中值得理解的五个 Harness 层次：**指令 → 约束 → 反馈 → 记忆 → 编排**。

---

## 为什么重要

- 拥有自己的 Harness，就能按自己的需求设计它。
- 可以实现自己的强化学习系统，训练小模型，甚至是 0.5B 参数规模的模型。
- 原文作者认为，在当时，其他技能很难达到同样的投入产出比。
- 这是走向 [[autonomous-dev-orgs]] 的实践路径：因为每一层都是你构建的，所以你理解每一层。

> [!tip] 不要试图一次完成全部 17 层。先实现到第 4 层，让包含记忆的系统端到端跑起来，再持续迭代。能运行的 Harness，比无法运行的完美设计更有价值。

---

## 关联笔记

- [[process-driven-ai-coding]]：先用 SPEC.md 和 ORCHESTRATION.md 明确项目，再开始写代码。
- [[autonomous-dev-orgs]]：将这一架构扩展到团队规模。
- [[agentic-patterns]]：编排层将实现的模式目录。
- [[agent-skills-directory]]：可接入 Harness 的可复用技能生态。
- [[code-review-workflow]]：Harness 的实际应用示例，即 /commit 流水线。
