# AgentLens 架构文档

本文档面向参与 AgentLens 开发的协作者，说明项目的核心模块、数据流和边界。

## 项目定位

AgentLens 是一个 Coding Agent 观测诊断工具。当前它包含两条主要链路：

- 本地 Session Log 查看：读取 Claude Code、OpenCode、Codex 等 agent 的本地历史会话。
- 网络 Request/Response 录制：通过代理录制模型 API 请求和响应，用于排查网络层行为。

这两条链路可以互相补充，但不要混为一个数据源。

## 核心模块

### CLI 入口

主要文件：

- `agentlens/cli.py`
- `agentlens/commands/run.py`
- `agentlens/commands/web_server.py`
- `agentlens/commands/setup.py`
- `agentlens/commands/export_cmd.py`
- `agentlens/commands/import_cmd.py`

职责：

- 解析用户命令。
- 启动被观察的 agent。
- 启动代理录制进程。
- 启动 Web Viewer。
- 管理导出、导入、配置等辅助功能。

重要边界：

- `agentlens -- <target>` 中的 `<target>` 是 observed agent 的启动命令。
- `<target>` 不能直接作为报告生成 analyzer command。

### Proxy Recorder

主要文件：

- `agentlens/addons/recorder.py`
- `agentlens/recording.py`
- `agentlens/commands/run.py`

职责：

- 通过 mitmproxy 记录模型 API 的 HTTP 请求和响应。
- 对敏感 header、Authorization、Cookie、API key 等内容进行脱敏。
- 将原始网络记录保存到 `~/.agentlens/raw-req-resp`。

这条链路服务 Raw Req/Resp 页面，不负责读取本地 agent session log。

### Web Viewer Server

主要文件：

- `viewer/server.py`
- `viewer/claude-log.html`

职责：

- 提供静态前端页面。
- 提供本地日志 API。
- 提供 Raw Req/Resp API。
- 提供 session 分析报告 API。

重要边界：

- `viewer/server.py` 不应直接硬编码某个 agent 的日志目录和字段结构。
- 本地日志读取应通过 Log Adapter 完成。
- 报告生成应通过 Analyzer Adapter 完成。

### Log Adapter

主要目录：

- `agentlens/adapters/`

职责：

- 读取不同 Coding Agent 的本地 session。
- 将原始日志转为前端和报告链路可消费的统一结构。
- 保留 raw JSON，避免解析失败时丢失证据。

当前实现：

- `ClaudeAdapter`
- `OpenCodeAdapter`
- `CodexAdapter`

### Analyzer Adapter

主要目录：

- `agentlens/analyzers/`
- `agentlens/analyzer.py`
- `agentlens/session_report/pipeline.py`

职责：

- 将结构化 session 上下文交给某个非交互式 AI CLI 生成报告。
- 解析 analyzer 的 stdout、JSONL 或 last-message 文件。
- 处理 timeout、命令不存在、输出为空等错误。

当前协议：

- Claude：`claude -p -`
- OpenCode：`opencode run --format json`
- Codex：`codex exec --json --ephemeral --ignore-user-config -`，experimental

### Session Report Pipeline

主要目录：

- `agentlens/session_report/`
- `agentlens/assets/session-report/`

职责：

- 将 normalized session 转成报告数据模型。
- 计算工具调用、阶段耗时、Agent 摘要、规则诊断。
- 调用 Analyzer Adapter 生成 yuanxi 或 generic 报告。
- Analyzer 失败时提供本地结构化 fallback。

## 数据流

### 本地 Session Log 查看

```text
agentlens web / agentlens -- <agent>
  -> viewer/server.py
  -> agentlens.adapters.registry
  -> AgentAdapter
  -> normalized session
  -> viewer/claude-log.html
```

返回结构需要尽量保持前端兼容：

```json
{
  "agent": "opencode",
  "projectDir": "/path/to/project",
  "sessions": []
}
```

单个 session：

```json
{
  "agent": "codex",
  "sessionId": "...",
  "projectDir": "...",
  "main": [],
  "subagents": [],
  "events": [],
  "turns": [],
  "usage": {}
}
```

### 报告生成

```text
normalized session
  -> agentlens.session_report.normalize
  -> agentlens.session_report.core
  -> diagnosis_context
  -> agentlens.analyzer.run_mc_analysis
  -> AnalyzerSpec
  -> external analyzer CLI
  -> parsed report markdown
  -> HTML report
```

关键原则：

- observed agent 和 analyzer agent 必须分离。
- observed agent 负责产生日志。
- analyzer agent 负责生成报告。
- 两者可以相同，但命令不能混用。

### Raw Req/Resp 查看

```text
mitmproxy addon
  -> agentlens/addons/recorder.py
  -> ~/.agentlens/raw-req-resp
  -> viewer/server.py
  -> Raw Req/Resp 页面
```

这条链路展示网络请求，不等同于本地 session log。

## 设计原则

- 保持 Claude Code 现有能力不回退。
- 多 Agent 支持优先抽象边界，再逐步完善具体格式。
- 不假设不同 agent 的日志格式一致。
- 保留 raw 数据，归一化失败时仍可回看原始内容。
- 前端 API 返回尽量兼容旧字段，减少 viewer 大改。
- Analyzer 失败时要给清晰错误或 fallback，而不是让页面空白。

## 当前已知状态

- Claude Code：本地日志查看和报告链路较稳定。
- OpenCode：本地日志、工具调用、时间轴、yuanxi/generic 报告已进入可用状态。
- Codex：本地日志和 analyzer 架构已接入，报告链路仍标记 experimental，需要持续人工验收和优化。

