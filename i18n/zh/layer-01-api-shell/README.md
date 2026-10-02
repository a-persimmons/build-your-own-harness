# 第 1 层 — API 外壳与命令行

**你将构建：** 支持多个供应商的 LLM 客户端，提供流式输出和交互式 REPL。

**核心概念：** 供应商抽象、流式与阻塞式调用、消息历史。

---

## 环境准备

```bash
cp .env.example .env
# Fill in at least one API key in .env

uv sync
```

## 运行 REPL

```bash
# Anthropic (default)
uv run python run.py

# OpenRouter (any model via one API)
uv run python run.py --provider openrouter

# Specific model override
uv run python run.py --provider anthropic --model claude-haiku-4-5-20251001
```

## 运行测试

```bash
# Unit tests only (no API key needed)
uv run pytest tests/ -m "not integration" -v

# Integration tests (require API keys in .env)
uv run pytest tests/ -m integration -v
```

---

## 文件说明

| 文件 | 用途 |
|---|---|
| `src/providers.py` | `LLMClient`：通过统一的 `stream()` 接口封装 Anthropic 和兼容 OpenAI 的供应商 |
| `src/repl.py` | 交互式 REPL 与 `collect_response()` 辅助函数 |
| `run.py` | 命令行入口，支持 `--provider` / `--model` 参数 |
| `tests/test_providers.py` | 使用模拟对象的单元测试，以及调用真实 API 的集成测试 |

---

## 本层的关键设计决策

**为什么用 OpenAI SDK 接入非 Anthropic 供应商？**

OpenRouter、OpenAI、Ollama 以及许多新供应商都实现了兼容 OpenAI 的 REST API。统一使用 `openai` SDK，就能用同一套代码处理这些供应商，无需分别编写 HTTP 客户端。

**为什么从第一天就支持流式输出？**

给阻塞式架构补上流式输出很麻烦。一开始就把 `stream()` 作为基础接口，上层就可以直接获得流式能力。

**为什么将 `Message` 定义为 Pydantic 模型？**

它在边界处约束 `role` / `content` 的结构。后续层会为消息增加元数据，例如 Token 数量、工具调用。从一开始就明确类型，有助于防止数据模式悄悄发生偏移。

---

## 下一步：[第 2 层 — 工具与函数调用](../layer-02-tools/)
