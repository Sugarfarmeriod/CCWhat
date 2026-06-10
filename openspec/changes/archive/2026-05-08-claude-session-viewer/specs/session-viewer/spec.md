### Requirement: Backend API — list projects and sessions
`server.py` SHALL 提供 `GET /api/projects` 接口，返回 `~/.claude/projects`（或 `--projects-dir` 指定目录）下所有项目及其会话 ID 列表。

#### Scenario: List projects
- **WHEN** 前端调用 `GET /api/projects`
- **THEN** 返回 JSON 数组，每项包含 `projectDir`（目录名）和 `sessions`（该项目下的 sessionId 列表）

### Requirement: Backend API — load session
`server.py` SHALL 提供 `GET /api/session/<sessionId>` 接口，在所有项目目录中查找对应的主会话 JSONL 文件和 subagent 目录，返回解析后的数据。

#### Scenario: Session found
- **WHEN** 前端调用 `GET /api/session/<sessionId>`，对应 `.jsonl` 文件存在
- **THEN** 返回 `{"main": [...entries], "subagents": [{"agentId": "...", "meta": {...}, "entries": [...]}]}`

#### Scenario: Session not found
- **WHEN** 指定 sessionId 在所有项目目录中均不存在
- **THEN** 返回 HTTP 404 和 `{"error": "session not found"}`

#### Scenario: CORS headers
- **WHEN** 任意 API 请求到达
- **THEN** 响应包含 `Access-Control-Allow-Origin: *`，允许前端从 file:// 或其他来源访问

### Requirement: Frontend — session selector
前端 SHALL 在加载时调用 `/api/projects` 展示项目和会话选择器，用户选择后加载对应会话。

#### Scenario: Project and session selection
- **WHEN** 页面加载完成
- **THEN** 显示项目列表和每个项目下的会话 ID 下拉选择器；用户选择会话后渲染对话

#### Scenario: Load session
- **WHEN** 用户选择一个 sessionId 并点击加载
- **THEN** 前端调用 `/api/session/<sessionId>`，渲染主会话和 subagent 标签页

### Requirement: Render main session
前端 SHALL 渲染主会话中 `isSidechain: false` 的 `user` 和 `assistant` 条目。

#### Scenario: User message
- **WHEN** 条目 `type` 为 `user`，`isSidechain` 为 false，`message.content` 为字符串
- **THEN** 渲染为右侧用户气泡，显示文本和时间戳

#### Scenario: Assistant message with tool calls
- **WHEN** 条目 `type` 为 `assistant`，`message.content` 包含 `text` 和/或 `tool_use` 块
- **THEN** 渲染助手气泡：文本块直接显示，每个 tool_use 渲染为工具卡片（工具名 + 输入摘要 + 配对结果）

### Requirement: Render subagent sessions
前端 SHALL 为每个 subagent 渲染独立标签页，显示其完整对话（所有 user/assistant 条目）。

#### Scenario: Subagent tab
- **WHEN** 会话包含 subagents
- **THEN** 每个 subagent 显示为独立标签，标签名为 `meta.description`（截断至 20 字符）+ agentType

#### Scenario: Subagent conversation
- **WHEN** 用户切换到 subagent 标签
- **THEN** 渲染该 subagent 的所有 user/assistant 条目（同主会话渲染规则）

### Requirement: Tool call inline display
工具调用 SHALL 内联展示在对应 assistant 气泡内，与 tool_result 配对。

#### Scenario: Tool call card
- **WHEN** assistant 消息包含 `tool_use` 块
- **THEN** 显示工具名称和输入摘要（超 200 字符截断，提供展开按钮）

#### Scenario: Tool result paired
- **WHEN** 后续 user 消息包含匹配 `tool_use_id` 的 `tool_result`
- **THEN** 结果显示在工具卡片内，默认折叠（超 300 字符），点击展开

#### Scenario: Tool error
- **WHEN** `tool_result.is_error` 为 `true`
- **THEN** 工具卡片以红色背景标识错误

### Requirement: Session statistics
前端 SHALL 在每个标签顶部展示该会话/subagent 的统计信息。

#### Scenario: Stats display
- **WHEN** 会话加载完成
- **THEN** 显示：用户消息数、助手消息数、工具调用数、input_tokens、output_tokens、cache_read_input_tokens

### Requirement: CLI web-server subcommand
`deep-ai-analysis web-server` 子命令 SHALL 启动 viewer HTTP 服务，与直接运行 `viewer/server.py` 等效。

#### Scenario: Start with defaults
- **WHEN** 用户执行 `deep-ai-analysis web-server`
- **THEN** 在默认端口 7789 启动服务，打印监听地址和 viewer 访问 URL

#### Scenario: Custom port and projects dir
- **WHEN** 用户执行 `deep-ai-analysis web-server --port 8080 --projects-dir ~/my-projects`
- **THEN** 在指定端口和目录启动服务
