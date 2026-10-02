# 从零构建 Agent Harness

一个循序渐进、可以实际运行的 Python 教程：从零构建大语言模型（LLM）的 Agent Harness，路线覆盖从 API 外壳到强化学习的 17 个层次。

> “如果你使用的是别人提供的 Agent Harness，你就没有真正拥有或掌控自己的流程与 Agent。”

这个仓库让你通过亲手实现来理解每一层，不把实现细节藏在黑盒里。

---

## 适合谁

希望通过动手实现来理解 Agent 架构的软件工程师。不需要机器学习背景，但需要会 Python，并至少准备一个 API Key。

## 你将构建什么

一个功能完整的 Agent Harness，包含：

| 层次 | 构建内容 |
|---|---|
| 第 1 层 — API 外壳 | 多供应商流式客户端（Anthropic、OpenRouter、OpenAI）与交互式 REPL |
| 第 2 层 — 工具 | 带类型约束的工具注册表、函数调用、核心 Agent 循环 |
| 第 3 层 — 上下文 | Token 计数、滑动窗口、摘要 |
| 第 4 层 — 记忆 | 基于 SQLite 的长期记忆，由 LLM 管理检索 ← **MVP 已完成** |
| 第 5 层 — 存储 | 会话持久化、审计日志、工具结果缓存 |
| 第 6 层 — 流式输出 | SSE 与 WebSocket 实时输出 |
| 第 7 层 — MCP | Model Context Protocol 服务端与客户端 |
| 第 8 层 — 编排 | 提示词链、路由、并行处理、反思 |
| 第 9 层 — 技能 | 可复用的能力包 |
| 第 10 层 — 钩子 | 在 LLM 循环之外执行的动作前后触发器 |
| 第 11 层 — 队列 | 并发、限流、后台任务 |
| 第 12 层 — 沙箱 | 对 LLM 生成的代码进行进程与容器隔离 |
| 第 13 层 — 权限 | 风险分类、人工介入审批 |
| 第 14 层 — 护栏 | Token 预算、输出校验、防止循环失控 |
| 第 15 层 — 会话 | 中断后恢复、从一开始就引入 session_id |
| 第 16 层 — 本地模型 | 用小模型处理低成本、低延迟的子任务 |
| 第 17 层 — 强化学习 | 反馈收集、偏好优化、微调 |

---

## 前置条件

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- 至少一个 API Key：[OpenRouter](https://openrouter.ai)（推荐：一个 Key 接入多种模型）或 [Anthropic](https://console.anthropic.com)

---

## 快速开始

每一层都可以独立运行。你可以从第 1 层按顺序学习，也可以直接进入某一层。

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

## 各层如何连接

每一层都把前一层作为本地包导入：

```
MemoryAgentLoop          (Layer 4)
  └── ContextAwareAgentLoop  (Layer 3)
        └── AgentLoop        (Layer 2)
              └── LLMClient  (Layer 1)
```

后面的层扩展前面的层，而不修改它们，这是开闭原则的实践。

---

## 运行测试

```bash
# Unit tests — no API keys needed
cd layer-04-memory
uv run pytest tests/ -m "not integration" -v

# Integration tests — requires .env with API keys
uv run pytest tests/ -m integration -v
```

目前的测试数量：第 1 层（10）+ 第 2 层（16）+ 第 3 层（22）+ 第 4 层（28）= **76 个单元测试**。

---

## 设计原则

每一层都遵循以下规则：

- **所有数据模式都使用 Pydantic**：不让未经建模的字典跨越边界。
- **函数式核心、命令式外壳**：纯逻辑与 IO 分离。
- **SOLID**：单一职责、开闭原则、依赖注入。
- **在合适的地方使用 GoF 设计模式**：注册表、策略、模板方法、观察者。
- **TDD**：先写失败的测试，再实现功能；单元测试模拟网络。

---

## 研究过的参考实现

| 项目 | 值得研究的部分 |
|---|---|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | 记忆、技能、强化学习、完整 Harness 架构 |
| [Mastra](https://github.com/mastra-ai/mastra) | TypeScript 编排与工具连接 |
| [LangGraph](https://github.com/langchain-ai/langgraphjs) | 有状态的图编排 |
| [CrewAI](https://github.com/crewAIInc/crewAI) | 按角色分工的多 Agent 结构 |

研究这些项目是为了理解它们的设计决策，而不只是使用它们。亲手构建一个精简版本，往往比直接依赖完整实现学得更多。

---

## 参与贡献

代码规范和分层目录约定见 `CLAUDE.md`。

## 许可证

MIT
