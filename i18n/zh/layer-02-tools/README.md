# 第 2 层 — 工具与函数调用

**你将构建：** 带类型约束的工具注册表，以及核心 Agent 循环。你的 Harness 将从聊天机器人开始具备 Agent 的行动能力。

**核心概念：** 工具定义与执行的分离、注册表模式、工具调用与结果回传循环。

**依赖：** `layer-01-api-shell`（`harness_l01.providers`）。

---

## 环境准备

```bash
cp ../layer-01-api-shell/.env.example .env
# Fill in OPENROUTER_API_KEY (default provider) or ANTHROPIC_API_KEY

uv sync
```

## 运行 REPL

```bash
# Default: OpenRouter
uv run python run.py

# Anthropic
uv run python run.py --provider anthropic
```

试着问：“当前目录里有哪些文件？”Agent 会调用 `run_shell` 来回答。

## 运行测试

```bash
uv run pytest tests/ -m "not integration" -v
uv run pytest tests/ -m integration -v   # requires API keys
```

---

## 文件说明

| 文件 | 用途 |
|---|---|
| `src/tools.py` | `ToolDefinition`、`ToolRegistry`、内置处理函数（`read_file`、`run_shell`） |
| `src/agent_loop.py` | `AgentLoop`：实现 Anthropic 和兼容 OpenAI 的供应商的工具调用与结果回传循环 |
| `src/repl.py` | 支持工具调用的 Agent 的交互式 REPL |
| `run.py` | 命令行入口 |
| `tests/test_tools.py` | 16 个单元测试与 2 个集成测试 |

---

## 本层的关键设计决策

**为什么将 ToolDefinition 与处理函数分开？**

LLM 看到的只有工具定义，也就是数据模式和描述。处理函数是你自己的代码。把二者分开，就可以在不调用 LLM 的情况下独立测试处理函数，也可以替换定义而不触碰执行逻辑。

**为什么使用注册表，而不是列表？**

按名称查找的时间复杂度为 O(1)，注册表也便于扩展：调用 `registry.register()` 就能添加工具，无需修改已有代码。这体现了开闭原则。

**为什么 AgentLoop 采用模板方法结构？**

`run()` 定义固定骨架：发送请求 → 检查停止原因 → 执行工具 → 重复。`_on_tool_calls()` 钩子则是扩展点：在子类中重写它，就能加入日志、审计记录或人工审批，而无需改动循环逻辑。

**为什么循环同时处理 Anthropic 和兼容 OpenAI 的两条路径？**

供应商的工具调用协议并不相同：Anthropic 使用 `tool_use` 块，OpenAI 使用 `tool_calls`。在 `_call_model()` 中将它们归一为内部通用的字典格式，上层逻辑就可以与供应商解耦。

---

## Agent 循环示意

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

## 下一步：[第 3 层 — 上下文管理](../layer-03-context/)
