### Requirement: Backend API — list projects and sessions
`server.py` SHALL 提供 `GET /api/projects` 接口，返回 `~/.claude/projects`（或 `--projects-dir` 指定目录）下所有项目及其会话 ID 列表。

#### Scenario: List projects
- **WHEN** 前端调用 `GET /api/projects`
- **THEN** 返回 JSON 数组，每项包含 `projectDir`（目录名）和 `sessions`（该项目下的 sessionId 列表）

### Requirement: Backend API — load session
`server.py` SHALL 提供 `GET /api/session/<sessionId>` 接口，在所有项目目录中查找对应的主会话 JSONL 文件和 subagent 目录，返回解析后的数据。返回的 user 条目 SHALL 包含 `uuid` 字段，供前端用于 message-http 查询。

#### Scenario: Session found
- **WHEN** 前端调用 `GET /api/session/<sessionId>`，对应 `.jsonl` 文件存在
- **THEN** 返回 `{"main": [...entries], "subagents": [{"agentId": "...", "meta": {...}, "entries": [...]}]}`，每个 user 条目保留原始 `uuid` 字段

#### Scenario: Session not found
- **WHEN** 指定 sessionId 在所有项目目录中均不存在
- **THEN** 返回 HTTP 404 和 `{"error": "session not found"}`

#### Scenario: CORS headers
- **WHEN** 任意 API 请求到达
- **THEN** 响应包含 `Access-Control-Allow-Origin: *`，允许前端从 file:// 或其他来源访问

### Requirement: Backend API — message HTTP lookup
`server.py` SHALL 提供 `GET /api/message-http/<sessionId>/<messageId>` 接口，根据 sessionId 和 messageId（assistant entry 的 message.id，格式为 msg_bdrk_xxx）在 logs 目录下的 `*_parsed.jsonl` 文件中查找对应的 HTTP 请求/响应记录，通过 response_json.message.id 精确匹配。

#### Scenario: Records found
- **WHEN** 调用 `GET /api/message-http/<sessionId>/<messageId>`，能在 parsed JSONL 中找到匹配记录
- **THEN** 返回 `{"records": [...]}` 数组，每条记录包含 `timestamp`、`url`、`request_json`、`response_json` 字段，按 timestamp 升序排列

#### Scenario: No records found
- **WHEN** logs 目录为空或无匹配记录
- **THEN** 返回 `{"records": []}` 和 HTTP 200

#### Scenario: messageId not found in session
- **WHEN** 指定 messageId 在会话 JSONL 中不存在
- **THEN** 返回 HTTP 404 和 `{"error": "message not found"}`

#### Scenario: Exact message.id matching
- **WHEN** 匹配 parsed 记录时
- **THEN** 筛选条件为 `claude_session_id == sessionId` 且 `response_json.message.id == messageId`

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

### Requirement: CLI web-server req-resp-dir option
`deep-ai-analysis web-server` 子命令 SHALL 支持 `--req-resp-dir` 选项，指定 parsed JSONL 文件所在目录，默认为 `~/.deep-ai-analysis/raw-req-resp`。

#### Scenario: Custom req-resp dir
- **WHEN** 用户执行 `deep-ai-analysis web-server --req-resp-dir ~/ai-logs`
- **THEN** 服务启动后使用指定目录查找 parsed JSONL 文件

### Requirement: HTTP lookup button on messages
前端用户消息气泡和助手消息气泡 SHALL 在右上角显示「查看请求」按钮（主会话和 subagent 均支持）。

#### Scenario: Button visible on user and assistant messages
- **WHEN** 渲染 user 气泡（非纯 tool_result 消息）或 assistant 气泡
- **THEN** 气泡右上角显示「查看请求」按钮（user 传 assistantMsgId，assistant 传自身 message.id）

#### Scenario: Button click triggers lookup
- **WHEN** 用户点击「查看请求」按钮
- **THEN** 前端调用 `/api/message-http/<sessionId>/<messageId>`，显示加载弹窗

#### Scenario: Results displayed in modal
- **WHEN** 后端返回匹配记录
- **THEN** 弹窗展示：token 用量、助手回复内容、折叠的 request_json 摘要、完整 request_json、原始 response_json

#### Scenario: No results
- **WHEN** 后端返回空 records 数组
- **THEN** 弹窗显示"未找到对应的 HTTP 请求记录"

### Requirement: Backend API — list raw logs
`server.py` SHALL 提供 `GET /api/logs` 接口，扫描 logs_dir 下所有 `*_parsed.jsonl` 文件并返回记录列表。支持可选的 `session` query 参数过滤 claude_session_id。

#### Scenario: List all logs
- **WHEN** 调用 `GET /api/logs`
- **THEN** 返回 `{"records": [...], "sessions": [...]}` 按 timestamp 降序排列；`sessions` 为所有出现过的 session ID 列表

#### Scenario: Filter by session
- **WHEN** 调用 `GET /api/logs?session=<id>`
- **THEN** 仅返回 `claude_session_id` 等于指定值的记录

#### Scenario: Empty logs dir
- **WHEN** logs_dir 不存在或无 `*_parsed.jsonl` 文件
- **THEN** 返回 `{"records": [], "sessions": []}`

### Requirement: Raw log viewer page
`viewer/logs.html` SHALL 提供两栏布局的原始日志查看页面。

#### Scenario: Session filter
- **WHEN** 页面加载完成
- **THEN** 顶部显示 session 选择器，选项来自 `/api/logs` 返回的 sessions 列表；默认显示全部

#### Scenario: Log list
- **WHEN** 加载完成或 session 筛选变更
- **THEN** 左栏显示日志列表，每条展示：时间戳、model、stop_reason badge、input+output token 数、response 前 80 字

#### Scenario: Log detail
- **WHEN** 用户点击列表中某条记录
- **THEN** 右栏展示该记录的完整明细：基本信息（url、session_id）、response 内容（完整文本）、token usage、request 摘要（含 messages 数量，折叠展开）、完整 request_json（折叠展开）

### Requirement: Backend API — list req-resp sessions
`server.py` SHALL 提供 `GET /api/req-resp/sessions` 接口，扫描 logs_dir（即 req-resp-dir）下的子目录，返回所有 session 及其对应的日期文件列表。

#### Scenario: List sessions
- **WHEN** 调用 `GET /api/req-resp/sessions`
- **THEN** 返回 `{"sessions": [{"id": "<sessionId>", "dates": ["YYYY-MM-DD", ...]}]}`，按 session ID 排序

#### Scenario: Empty directory
- **WHEN** logs_dir 不存在或无子目录
- **THEN** 返回 `{"sessions": []}`

### Requirement: Backend API — list req-resp records
`server.py` SHALL 提供 `GET /api/req-resp/records?session=<id>&date=<YYYY-MM-DD>` 接口，读取对应 JSONL 文件并返回记录列表。对于 SSE 记录，SHALL 解析 `sse_events` 中的 `message_start` 事件，将 `message.id` 注入为顶层字段 `_message_id`；非 SSE 记录该字段为 `null`。

#### Scenario: Records found
- **WHEN** 调用 `GET /api/req-resp/records?session=<id>&date=<date>`，对应 JSONL 文件存在
- **THEN** 返回 `{"records": [...]}` 数组，每条保留原始字段，SSE 记录额外包含 `_message_id` 字段（格式 `msg_bdrk_xxx`）

#### Scenario: _message_id injected for SSE records
- **WHEN** 记录 `is_sse` 为 true 且 `sse_events` 包含 `message_start` 事件
- **THEN** 记录顶层包含 `_message_id` 字段，值等于 `message_start.message.id`

#### Scenario: _message_id null for non-SSE records
- **WHEN** 记录 `is_sse` 为 false
- **THEN** 记录顶层 `_message_id` 为 `null`

#### Scenario: File not found
- **WHEN** 指定 session/date 的 JSONL 文件不存在
- **THEN** 返回 `{"records": []}` 和 HTTP 200

### Requirement: Raw req-resp viewer search
`viewer/req-resp.html` SHALL 在顶部提供搜索框，支持按 `_message_id`（精确/前缀匹配）或 URL 路径（模糊匹配）实时过滤左侧记录列表。

#### Scenario: Search by message ID
- **WHEN** 用户在搜索框输入 `msg_bdrk_` 开头的字符串
- **THEN** 左侧列表仅显示 `_message_id` 包含该字符串的记录，计数实时更新

#### Scenario: Search by URL
- **WHEN** 用户在搜索框输入非 `msg_bdrk_` 开头的字符串
- **THEN** 左侧列表仅显示 URL 包含该字符串的记录

#### Scenario: Clear search
- **WHEN** 搜索框为空
- **THEN** 显示全部记录

### Requirement: Raw req-resp viewer page
`viewer/req-resp.html` SHALL 提供两栏布局的原始请求/响应日志查看页面。

#### Scenario: Session and date selection
- **WHEN** 页面加载完成
- **THEN** 顶部显示 session 选择器（来自 `/api/req-resp/sessions`）和日期选择器

#### Scenario: Record list
- **WHEN** 用户选择 session 和日期后
- **THEN** 左栏展示记录列表，每条显示：时间、URL path、is_sse badge、响应状态码

#### Scenario: Record detail
- **WHEN** 用户点击列表中某条记录
- **THEN** 右栏展示：基本信息、请求 headers（折叠）、请求 body（折叠）、响应 headers（折叠）、SSE events 列表或响应 body（展开）

### Requirement: Claude Log assistant entry link to req-resp viewer
`claude-log.html` 的 assistant 条目明细面板中，SHALL 在 `message.id` 旁展示「在请求日志中查看」链接，点击后在新 tab 打开 `req-resp.html?q=<message.id>`。

#### Scenario: Link visible for assistant entries with message.id
- **WHEN** 右侧明细展示 assistant 条目且 `message.id` 非空
- **THEN** `message.id` 值旁显示外链按钮，href 为 `req-resp.html?q=<message.id>`，target 为 `_blank`

#### Scenario: Link not shown without message.id
- **WHEN** assistant 条目的 `message.id` 为空
- **THEN** 不显示链接

### Requirement: Raw req-resp viewer URL search param
`viewer/req-resp.html` SHALL 在页面加载时读取 URL query 参数 `?q=`，若存在则自动填入搜索框，并在记录加载完成后触发过滤。

#### Scenario: URL param auto-fills search box
- **WHEN** 用户通过 `req-resp.html?q=msg_bdrk_xxx` 打开页面
- **THEN** 搜索框自动填入 `msg_bdrk_xxx`，记录加载完成后列表自动按该值过滤
