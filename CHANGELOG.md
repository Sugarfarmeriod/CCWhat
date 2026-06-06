# 更新日志 / Changelog

这里记录 codelenagent / ccwhat 的重要版本变化。版本号以 `pyproject.toml` 和 `ccwhat.__version__` 为准，发布标签使用 `v<version>`，例如 `v0.2.0`。

## v0.2.0 - 2026-06-06

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
