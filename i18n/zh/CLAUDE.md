# 从零构建 Harness — Claude 开发指引

## 仓库说明

一个用 Python 从零构建 LLM Agent Harness 的分步教程。每个编号层都是独立的 `uv` 项目，并扩展前一层。

## 分层结构

- 每一层放在 `layer-NN-name/` 中。
- 源代码：`layer-NN-name/src/`，层内导入使用 `from src.X`。
- 可安装包：`layer-NN-name/harness_lNN/`，跨层导入使用 `from harness_lNN.X`。
- 入口：`layer-NN-name/run.py`。
- 测试：`layer-NN-name/tests/`。

## 添加新层

1. 执行 `uv init layer-NN-name --python 3.12`。
2. 在 `pyproject.toml` 中把前面层添加为路径依赖。
3. 创建 `src/`、`harness_lNN/`、`tests/` 目录。
4. 在 `pyproject.toml` 中添加 `[build-system]` 和 `[tool.hatch.build.targets.wheel]`。
5. 将 `src/` 镜像到 `harness_lNN/`，修正导入路径，使其可安装。
6. 先写失败测试（红），再实现功能让测试通过（绿）。

## 跨层导入

| 来源 | 导入写法 |
|---|---|
| 第 1 层 providers/repl | `from harness_l01.providers import ...` |
| 第 2 层 tools/agent_loop | `from harness_l02.tools import ...` |
| 第 3 层 context/agent_loop | `from harness_l03.context import ...` |
| 第 4 层 memory | `from harness_l04.memory import ...` |

## 代码规范

- Python 3.12+；只使用 `uv`，不直接调用 `pip`。
- 层间边界的所有数据模式都使用 Pydantic，不传递未经建模的字典。
- 函数式核心、命令式外壳：纯逻辑与 IO 分离。
- 全程遵循 SOLID；GoF 模式只用在能让结构更清楚的地方，不到处套用。
- 红/绿 TDD：先写失败测试，再实现功能。
- 单元测试模拟网络；集成测试调用真实 API，标注 `@pytest.mark.integration`。
- 默认供应商是 OpenRouter，以降低入门门槛；Anthropic 也是可选项。

## 运行测试

```bash
# Unit tests (no API keys needed)
uv run pytest tests/ -m "not integration" -v

# Integration tests (requires .env with API keys)
uv run pytest tests/ -m integration -v
```

## 禁止提交

- `.env` 文件。
- `*.db` / `*.sqlite` 文件。
- `.venv/` 目录。
