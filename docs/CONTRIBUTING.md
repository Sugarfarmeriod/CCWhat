# AgentLens 开发贡献指南

欢迎参与 AgentLens 开发。本文档说明如何设置环境、理解工作流、运行测试和提交改动。

## 开发环境

推荐环境：

- macOS / Linux / WSL
- Python 3.10+
- `uv`
- `mitmproxy`

克隆仓库：

```bash
git clone git@github.com:PacemakerG/AgentLens.git
cd AgentLens
```

安装依赖：

```bash
uv sync
```

运行 CLI：

```bash
uv run agentlens --help
```

启动 Web Viewer：

```bash
uv run agentlens web
```

## 常用开发命令

运行全部测试：

```bash
uv run python -m unittest
```

运行指定测试：

```bash
uv run python -m unittest tests.test_adapters
uv run python -m unittest tests.test_current_session_analysis
```

查看 OpenSpec change：

```bash
openspec list
openspec validate <change-name> --strict
```

## 项目工作流

AgentLens 使用 OpenSpec 驱动较大的功能改动。

建议流程：

1. 先讨论边界和目标。
2. 新建或更新 OpenSpec change。
3. 写中文 proposal/design/spec/tasks。
4. 实现代码。
5. 勾选完成的 task。
6. 跑测试。
7. 手动验收。
8. commit / push / PR。
9. change 完成后归档。

小修小补可以直接改代码，但涉及架构、协议、字段模型、前端大改时，建议走 OpenSpec。

## 文档语言

OpenSpec 文档默认使用中文。

开发文档也优先使用中文。如果需要英文文档，可以后续在 `docs/` 下补英文版本。

## 重要架构边界

### 不要混用 observed agent 和 analyzer command

错误方向：

```text
agentlens -- opencode
-> 把 ("opencode",) 当作 analyzer command
```

正确方向：

```text
agentlens -- opencode
-> observed agent = opencode
-> Log Adapter = OpenCodeAdapter
-> Analyzer Adapter = opencode run --format json
```

### 不要混用本地日志和网络抓包

本地日志：

- 来自 Claude/OpenCode/Codex 的本地 session。
- 用于 Session Log 页面和报告生成。

网络抓包：

- 来自 mitmproxy 录制的 Request/Response。
- 用于 Raw Req/Resp 页面。

二者可以关联，但不能假设字段一致。

### 不要假设所有 agent 格式一致

Claude Code、OpenCode、Codex 的日志格式差异很大。

新增字段时优先进入 normalized model，而不是把某个 agent 的原始字段直接暴露给所有代码。

## 如何新增 Log Adapter

参考：

- `docs/ADAPTERS.md`
- `agentlens/adapters/base.py`
- `agentlens/adapters/registry.py`

最小要求：

- 实现 adapter 接口。
- 注册 agent 名称和别名。
- 保留 raw。
- 写 list/load/normalize 测试。
- 手动验证 `agentlens web --agent <agent>`。

## 如何新增 Analyzer

参考：

- `docs/ANALYZER.md`
- `agentlens/analyzers/base.py`
- `agentlens/analyzers/registry.py`
- `agentlens/analyzer.py`

最小要求：

- 明确非交互命令。
- prompt 必须走 stdin 或明确说明协议。
- 明确输出模式。
- 写 parser 测试。
- 写 timeout / empty output 测试。
- 手动验证 yuanxi/generic 报告。

## 测试要求

改 Log Adapter 时至少覆盖：

- `list_projects()`
- `load_session()`
- normalized events
- usage 映射
- raw 保留
- 缺字段或坏 JSON 不崩溃

改 Analyzer 时至少覆盖：

- 默认命令
- parser 正常输出
- parser 空输出
- timeout
- explicit command override
- env override

改 Web Viewer API 时至少覆盖：

- API status code
- response payload 关键字段
- 旧字段兼容

## 手动验收建议

Claude：

```bash
uv run agentlens web --agent claude
uv run agentlens -- claude
```

OpenCode：

```bash
uv run agentlens web --agent opencode
uv run agentlens -- opencode
```

Codex：

```bash
uv run agentlens web --agent codex
uv run agentlens -- codex
```

报告链路：

- 打开 session。
- 点击 yuanxi 报告。
- 点击 generic 报告。
- 检查图表是否有数据。
- 检查 Mermaid 是否正常或 fallback 文案是否准确。
- 检查 analyzer 失败时页面是否仍有可读内容。

## 版本号规则

当前项目使用语义化版本的早期形式：

```text
v0.1.x
```

建议：

- bugfix、小功能、适配增强：第三位递增，例如 `v0.1.2 -> v0.1.3`
- 较大的功能阶段：第二位递增，例如 `v0.1.x -> v0.2.0`
- 重大破坏性变化：未来进入 `v1.0.0` 后再严格处理

版本更新时建议同步修改：

- `README.md`
- `README.zh.md`
- `README.en.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `uv.lock`

## 提交建议

提交前：

```bash
git status
uv run python -m unittest
openspec validate <change-name> --strict
```

Commit message 尽量短而明确：

```text
Fix Codex report analyzer fallback
Add OpenCode log adapter docs
```

如果是较大功能，PR 描述中写清楚：

- 改了什么
- 为什么改
- 如何测试
- 哪些需要手动验收

