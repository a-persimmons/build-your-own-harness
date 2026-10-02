# 第 4 层 — 记忆

**你将构建：** 可以跨会话保留的长期记忆，底层使用 SQLite，由 LLM 自己管理。Agent 决定存储什么、检索什么，以及遗忘什么。

**核心概念：** 仓储模式、由 LLM 管理记忆、把记忆封装为工具、向系统提示词注入记忆。

**依赖：** `layer-01`（`harness_l01`）、`layer-02`（`harness_l02`）、`layer-03`（`harness_l03`）。

---

## 环境准备

```bash
cp ../layer-01-api-shell/.env.example .env
uv sync
```

## 运行 REPL

```bash
# Default: OpenRouter, persists to memory.db
uv run python run.py

# Custom DB path (resume a previous session)
uv run python run.py --db sessions/alice.db

# Type 'memories' at the prompt to inspect what's stored
```

尝试以下步骤：

1. 告诉 Agent：“我叫 Alex，我正在构建一个 Agent Harness。”
2. 输入 `exit` 退出。
3. 重新运行，问：“你知道关于我的哪些事情？”

Agent 会回忆它在上一次会话中存储的内容。

## 运行测试

```bash
uv run pytest tests/ -m "not integration" -v
uv run pytest tests/ -m integration -v
```

---

## 文件说明

| 文件 | 用途 |
|---|---|
| `src/memory.py` | `MemoryRecord`（Pydantic 模型）、`MemoryStore`（SQLite 仓储） |
| `src/memory_tools.py` | `remember`、`recall`、`forget` 工具，以及 `memory_system_prompt()` |
| `src/agent_loop.py` | `MemoryAgentLoop`：在第 3 层基础上增加记忆工具与提示词注入 |
| `src/repl.py` | 带 `memories` 命令的 REPL |
| `run.py` | 命令行入口，使用 `--db` 指定持久化数据库 |
| `tests/test_memory.py` | 28 个单元测试与 2 个集成测试 |

---

## 本层的关键设计决策

**为什么由 LLM 管理检索，而不是自动注入所有记忆？**

每次都向提示词注入所有记忆，成本高、噪声也大：1000 条事实就可能塞满上下文窗口。因此，我们把 `recall` 作为工具交给模型，只检索与当前轮次相关的内容。原文将它与 Google 2026 年的 “Always On Memory Agent” 架构作类比。

**为什么选择 SQLite，而不是向量数据库？**

它无需生成嵌入向量，也不需要外部服务，任何 SQLite 客户端都能查看数据。本教程认为，对文本做子串匹配已能覆盖多数检索需求。第 4 层的设计支持替换：后续可以在保持接口不变的前提下，把 `MemoryStore` 换成基于 pgvector 的实现。

**为什么把记忆作为工具，而不是单独设计一条处理流水线？**

这样可以让架构保持简单。Agent 循环已经知道如何调用工具、处理结果，再增加三个记忆工具就能复用现有机制。它与业务工具遵循同一个思路：由 LLM 决定何时调用。

**既然有 recall，为什么仍要向系统提示词注入记忆摘要？**

`recall` 负责按需检索，系统提示词中的摘要则提供快捷路径：模型无需先调用工具，就能看到最近存储的事实。它是一份紧凑快照，而不是整个记忆库。

---

## 架构：完成第 4 层后的完整结构

```
MemoryAgentLoop          (Layer 4) — memory tools + prompt injection
    └── ContextAwareAgentLoop  (Layer 3) — token counting + window strategy
            └── AgentLoop      (Layer 2) — tool-call/result loop
                    └── LLMClient  (Layer 1) — streaming, multi-provider
```

每一层增加一个关注点，都不修改下面的层。

---

## MVP 已完成 ✓

现在你已经有一个可以工作的 Agent Harness，包含：

- 多供应商流式调用（第 1 层）。
- 带类型约束的工具注册表与 Agent 循环（第 2 层）。
- 滑动窗口和摘要两种上下文管理策略（第 3 层）。
- 由 LLM 管理检索的持久化长期记忆（第 4 层）。

第 5–17 层计划补充生产场景需要的能力：存储结构、流式协议、MCP、编排、沙箱与强化学习。

## 下一步：[第 5 层 — 存储与持久化](../layer-05-storage/)
