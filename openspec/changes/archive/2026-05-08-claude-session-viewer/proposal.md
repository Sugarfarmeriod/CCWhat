## Why

Claude Code 产生的会话日志（JSONL 格式）包含用户消息、助手文本、工具调用和工具结果，原始格式难以直观阅读。需要一个前端页面 + 轻量后端服务，将主会话和 subagent 日志渲染为可交互的对话流视图，便于回顾和分析 AI 的处理过程。

## What Changes

- 新增 `viewer/server.py`：轻量 Python HTTP 服务逻辑，提供 REST API 读取本地 Claude Code 日志文件（主会话 + subagents），不上传文件，通过 sessionId 定位
- 新增 `web-server` CLI 子命令：通过 `deep-ai-analysis web-server` 启动 viewer 服务，支持 `--port` 和 `--projects-dir` 选项
- 新增 `viewer/index.html`：前端单页应用，通过 API 加载并渲染会话日志
- 主会话与各 subagent 分标签页展示，subagent 显示 description 和 agentType
- 每个 assistant 轮次展示：纯文本回复 + 工具调用（工具名、输入摘要、输出结果折叠）
- 工具调用与对应结果通过 `tool_use_id` 关联并内联展示

## Capabilities

### New Capabilities

- `session-viewer`: 前端 + Python 后端的会话日志可视化工具，支持主会话和 subagent 日志展示

### Modified Capabilities

（无）

## Impact

- 新增 `viewer/server.py`（Python 标准库，无额外依赖，默认端口 7789）
- 新增 `viewer/index.html`（Vanilla JS，调用后端 API）
- 新增 `deep_ai_analysis/commands/web_server.py`：`web-server` click 子命令，注册到主 CLI
- `deep_ai_analysis/cli.py`：注册 `web-server` 命令
