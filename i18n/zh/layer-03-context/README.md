# 第 3 层 — 上下文管理

**你将构建：** 每轮对话的 Token 计数，以及上下文空间不足时的两种处理策略：丢弃最旧的消息（滑动窗口），或将这些消息压缩为摘要（摘要策略）。

**核心概念：** 策略模式、Token 预算、将上下文窗口作为需要管理的资源。

**依赖：** `layer-01-api-shell`（`harness_l01`）、`layer-02-tools`（`harness_l02`）。

---

## 环境准备

```bash
cp ../layer-01-api-shell/.env.example .env
uv sync
```

## 运行 REPL

```bash
# Default: OpenRouter + sliding window
uv run python run.py

# Summarization strategy
uv run python run.py --strategy summarize

# Tight limit to see trimming in action
uv run python run.py --limit 500

# Type 'usage' at the prompt to see token counts per turn
```

## 运行测试

```bash
uv run pytest tests/ -m "not integration" -v
uv run pytest tests/ -m integration -v
```

---

## 文件说明

| 文件 | 用途 |
|---|---|
| `src/context.py` | `count_tokens`、`SlidingWindow`、`Summarizer`、`ContextManager` |
| `src/agent_loop.py` | `ContextAwareAgentLoop`：扩展第 2 层循环，在调用模型之前裁剪上下文 |
| `src/repl.py` | 带 `usage` 命令的 REPL，用于检查 Token 日志 |
| `run.py` | 命令行入口，支持 `--strategy` 与 `--limit` 参数 |
| `tests/test_context.py` | 22 个单元测试与 2 个集成测试 |

---

## 本层的关键设计决策

**为什么使用 tiktoken，而不是 Anthropic 的 usage 字段？**

Anthropic 的 `usage` 字段提供权威用量，但只有在 API 调用之后才能得到。tiktoken 能在发送请求之前快速估算 Token 数，使我们可以提前裁剪历史，避免上下文溢出引发 400 错误。这里可以接受近似值，因为设置的上限本来就比较保守。

**为什么提供两种策略，而不是一种？**

滑动窗口的时间复杂度为 O(n)，只需丢弃消息，不产生额外模型调用费用。摘要策略能保留较久之前的上下文，但要付出一次额外 LLM 调用的成本。没有一种策略在所有场景下都更好，选择取决于历史信息对任务有多重要。策略模式使替换策略、添加第三种方法很方便，例如原文设想在第 4 层引入向量检索。

**为什么 ContextAwareAgentLoop 继承 AgentLoop，而不是包装它？**

上下文裁剪是同一调用流程中的预处理步骤。在本教程的设计中，它不需要单独包装为另一个对象。通过继承和模板方法，我们重写 `run()`、调用 `super()`，就能复用循环逻辑而不复制代码。

---

## 上下文管理如何接入循环

```
run(user_input, history)
    │
    ▼
ContextManager.trim(messages)   ← token count, apply strategy if over limit
    │
    ▼
AgentLoop.run(trimmed_history)  ← inherited from Layer 2
    │
    ▼
[tool-call/result cycle]
    │
    ▼
final response + updated usage_log
```

---

## 下一步：[第 4 层 — 记忆](../layer-04-memory/)
