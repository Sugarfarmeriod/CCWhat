## Why

CCWhat 已经有多 Agent Log Adapter，可以读取 Claude Code、Codex、OpenCode 的本地 session，但报告生成链路仍把“被观察的 agent”和“负责生成报告的 analyzer”混在一起，导致 `ccwhat -- opencode` 或 `ccwhat -- codex` 时可能把启动目标命令直接当成报告分析命令。

这会让 OpenCode 误跑裸 `opencode` 进入 TUI 并超时，也让 Codex 缺少正式的 experimental analyzer 协议。现在需要把 Analyzer 协议独立抽象出来，让报告生成真正支持多 agent。

## What Changes

- 新增 Multi-Agent Analyzer Adapter 能力。
- 明确区分：
  - Observed Agent：被 CCWhat 启动、代理和读取日志的 agent。
  - Log Adapter：负责读取 observed agent 的本地日志。
  - Analyzer Adapter：负责把 normalized session/report context 交给某个 agent 或外部分析器生成报告。
- 修正 `ccwhat -- <target>` 的调用链：
  - `target_args` 只能用于启动 observed agent。
  - `target_args` 不得直接作为 `analyzer_cmd` 传入 Viewer Server。
- 支持 analyzer 默认协议：
  - Claude：稳定 analyzer，默认命令 `claude -p -`，输出模式 `stdout`。
  - OpenCode：稳定 analyzer，默认命令 `opencode run --format json`，输出模式 `jsonl_text`。
  - Codex：experimental analyzer，默认候选命令 `codex exec --json --ephemeral --ignore-user-config -`，输出模式 `jsonl_text`。
  - Codex 备用候选：`codex exec --output-last-message <tmpfile> --ephemeral --ignore-user-config -`，输出模式 `last_message_file`。
- 支持环境变量或显式配置覆盖 analyzer agent、命令和 timeout。
- 暂不实现复杂重试、自动降级、多 analyzer 竞速或外部 API provider。

## Capabilities

### New Capabilities

- `multi-agent-analyzer-adapters`: 定义报告生成 analyzer 的协议、默认命令、输出解析、配置优先级、错误边界和测试要求。

### Modified Capabilities

- `multi-agent-log-adapters`: Run 模式必须继续推断 observed agent 并选择对应 Log Adapter，但不得把 observed agent 的启动命令 `target_args` 直接作为 analyzer command。

## Impact

- 主要影响：
  - `ccwhat/commands/run.py`
  - `viewer/server.py`
  - `ccwhat/analyzer.py`
  - `ccwhat/session_report/pipeline.py`
  - `tests/test_current_session_analysis.py`
- 可能新增：
  - `ccwhat/analyzers/` 或 `ccwhat/analyzer_adapters/`
  - analyzer 协议模型、registry 和输出解析测试
- 不应影响：
  - Claude/Codex/OpenCode Log Adapter 读取本地日志的能力
  - export/import 相关链路
  - Raw Req/Resp 页面
