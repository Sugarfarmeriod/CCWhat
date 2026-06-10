## MODIFIED Requirements

### Requirement: Backend API — load session
`server.py` SHALL 提供 `GET /api/session/<sessionId>` 接口，在所有项目目录中查找对应的主会话 JSONL 文件和 subagent 目录，返回解析后的数据。返回的 user 条目 SHALL 包含 `uuid` 字段，供前端用于 message-http 查询。

#### Scenario: Session found
- **WHEN** 前端调用 `GET /api/session/<sessionId>`，对应 `.jsonl` 文件存在
- **THEN** 返回 `{"main": [...entries], "subagents": [{"agentId": "...", "meta": {...}, "entries": [...]}]}`；每个 user 条目保留原始 `uuid` 字段

#### Scenario: Session not found
- **WHEN** 指定 sessionId 在所有项目目录中均不存在
- **THEN** 返回 HTTP 404 和 `{"error": "session not found"}`

#### Scenario: CORS headers
- **WHEN** 任意 API 请求到达
- **THEN** 响应包含 `Access-Control-Allow-Origin: *`，允许前端从 file:// 或其他来源访问

## ADDED Requirements

### Requirement: Backend API — message HTTP lookup
`server.py` SHALL 提供 `GET /api/message-http/<sessionId>/<messageId>` 接口，根据 sessionId 和 messageId（user 条目的 uuid）在 logs 目录下的 `*_parsed.jsonl` 文件中查找对应的 HTTP 请求/响应记录。

#### Scenario: Records found
- **WHEN** 调用 `GET /api/message-http/<sessionId>/<messageId>`，能在 parsed JSONL 中找到匹配记录
- **THEN** 返回 `{"records": [...]}` 数组，每条记录包含 `timestamp`、`url`、`request_json`、`response_json` 字段，按 timestamp 升序排列

#### Scenario: No records found
- **WHEN** logs 目录为空或无匹配记录
- **THEN** 返回 `{"records": []}` 和 HTTP 200

#### Scenario: messageId not found in session
- **WHEN** 指定 messageId 在会话 JSONL 中不存在
- **THEN** 返回 HTTP 404 和 `{"error": "message not found"}`

#### Scenario: Time window matching
- **WHEN** 匹配 parsed 记录时
- **THEN** 筛选条件为 `claude_session_id == sessionId` 且记录 timestamp 在 user 条目 timestamp 的 [-5s, +60s] 窗口内

### Requirement: CLI web-server logs-dir option
`deep-ai-analysis web-server` 子命令 SHALL 支持 `--logs-dir` 选项，指定 parsed JSONL 文件所在目录，默认为 `./logs`。

#### Scenario: Custom logs dir
- **WHEN** 用户执行 `deep-ai-analysis web-server --logs-dir ~/ai-logs`
- **THEN** 服务启动后使用指定目录查找 parsed JSONL 文件

### Requirement: User message HTTP lookup button
前端用户消息气泡 SHALL 在主会话（非 subagent）的用户消息右上角显示「查看请求」按钮。

#### Scenario: Button visible on user message
- **WHEN** 渲染主会话的 user 气泡（非纯 tool_result 消息）
- **THEN** 气泡右上角显示「查看请求」按钮

#### Scenario: Button click triggers lookup
- **WHEN** 用户点击「查看请求」按钮
- **THEN** 前端调用 `/api/message-http/<sessionId>/<messageId>`，显示加载状态

#### Scenario: Results displayed in modal
- **WHEN** 后端返回匹配记录
- **THEN** 弹窗展示所有匹配记录，每条显示：timestamp、model（来自 request_json）、用户最后一条消息摘要、response content.text（截断）、token usage

#### Scenario: No results
- **WHEN** 后端返回空 records 数组
- **THEN** 弹窗显示"未找到对应的 HTTP 请求记录"
