# 更新日志 / Changelog

这里记录 codelenagent / ccwhat 的重要版本变化。版本号以 `pyproject.toml` 和 `ccwhat.__version__` 为准，发布标签使用 `v<version>`，例如 `v0.1.2`。

## v1.0.0 - 2026-06-11

### 新增

- 发布 V1：新增 Task Trace Workbench。
- 新增第一版规则任务切分能力，可从长 Session 中识别多个 Coding Task。
- Viewer 新增任务列表、任务详情、边界原因、Evidence、命令/错误、Raw JSON 等任务切分展示。
- 左侧导航升级为 App Shell 工作台，包含 Session、Tasks、Overview、Timeline、Req / Resp、Diff、Diagnostics、Export、Settings。

### 改进

- 默认仍进入 Session 页面，Tasks 由用户手动触发任务切分。
- 修复 Viewer 初始化递归问题，避免页面打开时栈溢出。
- 保留 Claude Code、Codex、OpenCode 三类 Agent 的日志查看、报告、时间线和任务切分入口。
- 改进 task 起止事件到原始日志 turn/event 的定位。

---

## v0.1.3 - 2026-06-09

### 新增

- 完成 Codex 报告生成链路的完整适配，元析报告和通用报告在 Codex 会话上均可正常生成。
- 至此，codelenagent 已全面支持三大主流 AI Coding Agent：**Claude Code（VS Code）**、**Codex** 和 **OpenCode**，日志查看、分析报告、时间轴、工具耗时、Agent 摘要等核心功能对三者均可用。

### 改进

- Codex 报告生成的协议解析和超时问题已修复。
- 三大 Agent 的 Analyzer 适配器统一收归 `ccwhat/analyzers/` 模块，结构更清晰。

---

## v0.1.2 - 2026-06-09

### 新增

- 完成 OpenCode 报告生成链路的第一版适配。
- OpenCode Analyzer 默认使用 `opencode run --format json`，并支持真实 JSONL 输出中的 `part.text`。
- OpenCode 本地 DB 日志接入元析报告和通用报告的数据管线。

### 改进

- 修复 OpenCode 数字时间戳归一化，工具事件可正确进入时间轴、阶段统计、柱状图和饼图。
- 修复通用报告 Mermaid 渲染失败时的 fallback 展示，保留原始 Mermaid 源码并区分语法失败和库未加载。
- 收紧通用报告 prompt 中的 Mermaid 输出约束，降低 OpenCode 生成非法 Mermaid 的概率。
- 增加 OpenCode 报告链路和 Mermaid fallback 的回归测试。

### 已知问题

- Codex 已接入多 Agent 日志/Analyzer 架构，但报告生成仍存在耗时和协议解析问题，下一步会继续适配 Codex。

## v0.1.1 - 2026-06-06

### 新增

- 新增多 Coding Agent 会话查看架构。
- 新增 Claude Code、Codex、OpenCode 本地日志 Adapter。
- 新增 `ccwhat web --agent <agent>`，支持按 agent 选择默认日志来源。
- 新增统一的 normalized events / turns / usage 数据结构，为后续跨 agent 展示做准备。

### 改进

- Web Viewer 保持 Claude Code 原有展示能力，同时可显示当前 agent 类型。
- `ccwhat -- <target>` 会根据启动目标推断 agent 类型，并把类型传给 Viewer。
- Codex 和 OpenCode 先按各自本地日志结构适配，不假设它们和 Claude Code JSONL 相同。

## v0.1.0 - 初始版本

### 新增

- Claude Code 本地会话日志查看。
- 请求 / 响应抓包记录。
- Web Viewer、导出、导入和基础诊断流程。
