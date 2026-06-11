## Purpose
定义 CCWhat Web Viewer 读取、展示和分析本地 Coding Agent session 日志的核心能力，包括 session 加载、日志渲染、请求响应关联和任务切分视图。
## Requirements
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

### Requirement: Task segmentation entry point
Claude Log 页面 SHALL 为当前已加载 session 提供任务切分入口，用于展示 `/api/task-segments` 返回的结构化 Task Segment 结果。

#### Scenario: Button disabled before session selection
- **WHEN** 页面尚未选择或加载 session
- **THEN** 任务切分按钮 SHALL 处于 disabled 状态
- **AND** 按钮 SHALL 显示“任务切分”

#### Scenario: Button enabled after session load
- **WHEN** 用户成功加载一个 session
- **THEN** 页面 SHALL 启用任务切分按钮
- **AND** 若该 session 尚无缓存结果，按钮 SHALL 显示“任务切分”

#### Scenario: Restore cached task segmentation result
- **WHEN** 当前 session 已生成任务切分结果
- **AND** detail panel 当前显示原始日志详情或分析报告
- **THEN** 任务切分按钮 SHALL 显示“查看任务切分”
- **AND** 用户点击后 SHALL 恢复该 session 的缓存任务切分视图

### Requirement: Task segmentation API request
Claude Log 页面 SHALL 使用当前 session ID 调用 `POST /api/task-segments`，不上传完整 session 内容。

#### Scenario: Request current session only
- **WHEN** 用户点击任务切分按钮且当前 session 没有缓存结果
- **THEN** 前端 SHALL 向 `/api/task-segments` 发送 POST 请求
- **AND** 请求体 SHALL 为 `{"sessionId": "<current-session-id>"}`
- **AND** SHALL NOT 发送 turns、筛选结果、完整日志、跨 session 参数或多 session 参数

#### Scenario: Loading state
- **WHEN** `/api/task-segments` 请求进行中
- **THEN** 任务切分按钮 SHALL disabled
- **AND** 按钮 SHALL 显示“切分中…”
- **AND** detail panel SHALL 显示任务切分 loading 状态

#### Scenario: Failed request
- **WHEN** `/api/task-segments` 返回错误或网络失败
- **THEN** 前端 SHALL 恢复任务切分按钮可点击状态
- **AND** detail panel SHALL 显示可读错误信息
- **AND** 若该 session 已有旧缓存结果，旧结果 SHALL 保留

### Requirement: Task segmentation cache
Claude Log 页面 SHALL 按 `sessionId` 在页面内存中缓存任务切分结果。

#### Scenario: Cache successful result
- **WHEN** `/api/task-segments` 返回成功结果
- **THEN** 前端 SHALL 将结果保存到当前页面内存缓存
- **AND** 缓存 key SHALL 为当前 `sessionId`
- **AND** SHALL NOT 写入 localStorage、后端文件、session 日志或导出包

#### Scenario: Session switch updates button state
- **WHEN** 用户切换 session
- **THEN** 页面 SHALL 根据新 session 是否已有任务切分缓存更新按钮文案
- **AND** 新 session 没有缓存时 SHALL 显示“任务切分”
- **AND** 新 session 有缓存时 SHALL 显示“查看任务切分”

#### Scenario: Re-segment current session
- **WHEN** 当前 session 已有任务切分结果
- **AND** 用户在任务切分视图中点击“重新切分”
- **THEN** 前端 SHALL 重新调用 `/api/task-segments`
- **AND** 请求成功后 SHALL 用新结果覆盖当前 session 的旧缓存
- **AND** 请求失败时 SHALL 保留旧缓存并显示失败原因

### Requirement: Task segmentation overview
Claude Log 页面 SHALL 在 detail panel 中展示任务切分概览和 task card 列表。

#### Scenario: Render summary
- **WHEN** `/api/task-segments` 返回成功结果
- **THEN** detail panel SHALL 展示 summary 信息
- **AND** 至少包含任务数量、ambiguous 状态、topic flip 数量和生成耗时

#### Scenario: Render empty state
- **WHEN** `/api/task-segments` 返回 `tasks` 为空数组
- **THEN** detail panel SHALL 显示“未识别到任务片段”或等价空状态
- **AND** SHALL NOT 渲染空白页面

#### Scenario: Render task cards
- **WHEN** 返回结果包含一个或多个 tasks
- **THEN** detail panel SHALL 为每个 task 渲染一个 task card
- **AND** task card SHALL 展示 task id、title、task type、status、filesChanged 数量、commands 数量、errors 数量、subagent 数量和 ambiguous 标记

#### Scenario: Select a task
- **WHEN** 用户点击 task card
- **THEN** 页面 SHALL 将该 task 标记为选中
- **AND** 在同一 detail panel 中展示该 task 的详情区块

### Requirement: Task segmentation detail panel
Claude Log 页面 SHALL 展示所选 Task Segment 的 evidence、边界原因、文件权重和原始 JSON。

#### Scenario: Render task overview
- **WHEN** 用户选中一个 task
- **THEN** task 详情 SHALL 展示 title、task type、status、startEventId、endEventId 和 finalClaim

#### Scenario: Render evidence
- **WHEN** 用户选中一个 task
- **THEN** task 详情 SHALL 展示 filesRead、filesChanged、commands、testCommands、errors、subagentIds 和 todosUser
- **AND** 空 evidence 列表 SHALL 显示为空状态而不是 undefined/null

#### Scenario: Render boundary reasons
- **WHEN** task 包含 `boundaryReasons`
- **THEN** task 详情 SHALL 逐条展示 boundary reason
- **AND** SHALL 保留原始原因文本中的信号名称和分数信息

#### Scenario: Render file weights
- **WHEN** task 包含 `fileWeights`
- **THEN** task 详情 SHALL 按权重降序展示文件和权重

#### Scenario: Render raw task JSON
- **WHEN** 用户查看 task 详情
- **THEN** 页面 SHALL 提供折叠的 raw JSON 区块
- **AND** raw JSON 内容 SHALL 经过 HTML 转义，不执行其中的 HTML 或脚本

### Requirement: Task segmentation event navigation
Claude Log 页面 SHALL 支持从 Task Segment 定位到起止事件附近的原始日志条目。

#### Scenario: Locate start event
- **WHEN** task 包含可映射的 `startEventId`
- **AND** 用户点击“定位开始事件”
- **THEN** 页面 SHALL 选中并展开对应原始日志条目
- **AND** detail panel SHALL 显示该原始日志条目详情

#### Scenario: Locate end event
- **WHEN** task 包含可映射的 `endEventId`
- **AND** 用户点击“定位结束事件”
- **THEN** 页面 SHALL 选中并展开对应原始日志条目
- **AND** detail panel SHALL 显示该原始日志条目详情

#### Scenario: Event not found
- **WHEN** task 的 `startEventId` 或 `endEventId` 无法映射到当前前端日志条目
- **THEN** 对应定位入口 SHALL disabled 或显示不可定位提示
- **AND** 页面 SHALL NOT 抛出脚本错误

### Requirement: Task segmentation debug boundaries
Claude Log 页面 SHALL 展示或折叠展示 `/api/task-segments` 返回的 debug boundaries，用于人工校准规则。

#### Scenario: Render debug boundaries
- **WHEN** 返回结果包含 `debugBoundaries`
- **THEN** 任务切分视图 SHALL 提供 debug boundaries 区块
- **AND** 每条 boundary SHALL 展示 eventId、score、shouldSplit 和 reasons

#### Scenario: No debug boundaries
- **WHEN** 返回结果不包含 debug boundaries 或为空数组
- **THEN** 页面 SHALL 显示空状态
- **AND** SHALL NOT 影响 task cards 或 task detail 渲染

### Requirement: Session + Tasks 双模块工作台
Viewer SHALL prioritize two core modules: `Session` and `Tasks`.

#### Scenario: 左侧核心导航
- **WHEN** viewer 渲染完成
- **THEN** 左侧 SHALL 显示 `Session` 和 `Tasks` 两个核心导航项
- **AND** `Session` SHALL be the default active page
- **AND** 其他非核心页面 MAY be hidden or shown as explicit placeholders

#### Scenario: 选择 session 后不出现空白主工作区
- **WHEN** 用户选择 project 和 session
- **THEN** viewer SHALL load the session data
- **AND** the active page SHALL render visible content
- **AND** page content SHALL NOT remain blank

### Requirement: Session 页面承接旧版日志展示
`Session` page SHALL migrate and preserve the previous local log viewer capability.

#### Scenario: Session 页面展示日志树和详情区
- **WHEN** 用户进入 `Session` 页面并已选择 session
- **THEN** 页面 SHALL 显示 turn tree / entry list
- **AND** 页面 SHALL 显示 entry detail panel
- **AND** 用户 SHALL be able to click an entry and inspect its raw/detail content

#### Scenario: Session 页面保留筛选和搜索
- **WHEN** 用户在 Session 页面查看日志
- **THEN** 页面 SHALL retain type filters
- **AND** 页面 SHALL respect the global search query for entries

#### Scenario: Session 页面为空时显示明确状态
- **WHEN** session 已加载但没有 entries
- **THEN** 页面 SHALL show a clear empty state
- **AND** SHALL NOT show an empty blank panel

#### Scenario: raw-events alias 跳转到 Session
- **WHEN** internal code navigates to `raw-events`
- **THEN** viewer SHALL route it to `Session`
- **AND** SHALL preserve canonical event focusing behavior

### Requirement: Tasks 页面承接任务切分
`Tasks` page SHALL provide task segmentation and task detail browsing for the current session.

#### Scenario: Tasks 页面无切分结果时显示 CTA
- **WHEN** 用户进入 `Tasks` 页面且当前 session 尚未加载
- **THEN** 页面 SHALL display a clear disabled state
- **AND** SHALL explain that a session must be selected first

#### Scenario: 已加载 session 后进入 Tasks 自动切分
- **WHEN** 用户已经选择并成功加载一个 session
- **AND** 当前 session 没有 task segmentation result
- **WHEN** 用户点击左侧 `Tasks`
- **THEN** viewer SHALL automatically request task segmentation for the current session
- **AND** 页面 SHALL show loading, success, or error state
- **AND** 页面 SHALL NOT remain blank

#### Scenario: Tasks 页面复用当前 session 切分缓存
- **WHEN** 当前 session already has a task segmentation result
- **AND** 用户点击左侧 `Tasks`
- **THEN** 页面 SHALL render cached Task List and Task Detail immediately
- **AND** SHALL NOT send an unnecessary duplicate segmentation request

#### Scenario: Tasks 页面展示 Task List 和 Task Detail
- **WHEN** task segmentation returns tasks
- **THEN** 页面 SHALL render Task List and Task Detail panes
- **AND** selecting a task SHALL update Task Detail

#### Scenario: 报告分析不阻塞任务切分
- **WHEN** a long-running session report analysis request is in progress
- **AND** 用户在 `Tasks` 页面触发 task segmentation
- **THEN** viewer server SHALL be able to process the task segmentation request without waiting for the analysis request to finish
- **AND** task segmentation SHALL NOT be serialized behind report generation by the HTTP server

#### Scenario: Task 卡片名称稳定
- **WHEN** task segmentation returns multiple tasks
- **THEN** task card title SHALL use a stable ordinal label such as `任务 1`, `任务 2`
- **AND** SHALL NOT display raw noisy event text, encoded payload fragments, or adapter-specific internal strings as the card title

#### Scenario: Task Detail 保留核心 tabs
- **WHEN** 用户查看 task detail
- **THEN** 页面 SHALL provide Overview, Evidence, Turns, Files & Diff, Commands, and Raw task tabs or equivalent sections

#### Scenario: Task evidence 跳转回 Session 页面
- **WHEN** 用户点击 task start/end/evidence navigation
- **THEN** viewer SHALL navigate to `Session`
- **AND** SHALL focus the corresponding entry when the target can be resolved
- **AND** SHALL show clear debug information when the target cannot be resolved

#### Scenario: Session 和 Tasks 往返切换不丢失页面
- **WHEN** 用户已加载 session 并停留在 `Session`
- **AND** 用户点击 `Tasks`
- **AND** 用户再点击 `Session`
- **THEN** `Session` 页面 SHALL restore the current session log list and detail area
- **AND** viewer SHALL have an active page
- **AND** 主工作区 SHALL NOT be blank

### Requirement: Session 报告分析入口
`Session` page SHALL expose the existing session report analysis workflow.

#### Scenario: Session 页面展示报告分析按钮
- **WHEN** 用户进入 `Session` 页面
- **THEN** 页面 SHALL show a report analysis button in the Session toolbar
- **AND** the button SHALL be disabled until the current session is loaded

#### Scenario: 报告分析复用已有链路
- **WHEN** 用户点击 Session 页面报告分析按钮
- **THEN** viewer SHALL open the existing report mode modal
- **AND** confirming the modal SHALL call the existing `/api/analyze` workflow
- **AND** report output SHALL be shown in the Session detail area
- **AND** viewer SHALL NOT navigate to a missing `evidence` page

### Requirement: 非核心页面降级
Non-core workbench pages SHALL NOT block the Session and Tasks migration.

#### Scenario: 非核心入口不伪装为已完成
- **WHEN** Overview, Timeline, Req / Resp, Diff, Diagnostics, Export, or Settings is visible
- **THEN** it SHALL either show a clear placeholder or a minimal existing entry point
- **AND** it SHALL NOT be required for this change's manual acceptance

### Requirement: 回归测试
The change SHALL include regression tests for the two core modules and navigation aliases.

#### Scenario: 静态结构测试
- **WHEN** tests inspect `viewer/claude-log.html`
- **THEN** they SHALL verify default `Session` navigation, `Tasks` navigation, and Session log container presence

#### Scenario: Session load tests
- **WHEN** tests inspect frontend session loading behavior
- **THEN** they SHALL verify `loadSession()` does not auto-jump away because task segmentation is missing
- **AND** it renders the current active page after session data loads

#### Scenario: Task navigation tests
- **WHEN** tests inspect task evidence navigation
- **THEN** they SHALL verify task navigation targets route to Session/raw-events alias and keep event focusing behavior

#### Scenario: Tasks 自动切分与往返测试
- **WHEN** DOM tests simulate loading a session and clicking `Tasks`
- **THEN** tests SHALL verify task segmentation is requested for the current session
- **AND** tests SHALL verify switching back to `Session` restores visible log content

#### Scenario: 并发和标题回归测试
- **WHEN** tests inspect viewer server construction
- **THEN** they SHALL verify the viewer uses a threaded HTTP server
- **WHEN** tests inspect task segmentation output
- **THEN** they SHALL verify task titles are stable ordinal labels

#### Scenario: 报告分析入口测试
- **WHEN** tests inspect frontend analysis behavior
- **THEN** they SHALL verify a visible Session report analysis button exists
- **AND** analysis code SHALL route report rendering to `Session`, not a missing `evidence` page

### Requirement: Task Segment 任务卡片选择
Claude Log 页面 SHALL 支持用户点击任意 Task Segment card 后切换当前选中任务，并展示该任务对应的详情内容。

#### Scenario: 点击任务卡片切换详情
- **WHEN** Task Segment 面板已渲染多个 task cards
- **AND** 用户点击非当前选中的 task card
- **THEN** 页面 SHALL 将该 task 标记为唯一选中 task
- **AND** task detail SHALL 展示被点击 task 的 `taskId`、`title`、`taskType`、`startEventId`、`endEventId`、evidence、fileWeights 和 boundaryReasons
- **AND** 之前选中的 task card SHALL 不再显示 selected 状态

#### Scenario: 任务选择状态由数据驱动
- **WHEN** Task Segment 面板重渲染
- **THEN** selected 状态 SHALL 由 `selectedTaskSegmentId` 和 task data 决定
- **AND** SHALL NOT 依赖查询 inline `onclick` 字符串来查找当前 card

#### Scenario: 点击无效任务不会破坏当前视图
- **WHEN** 用户触发的 task id 不存在于当前 session 的缓存结果中
- **THEN** 页面 SHALL 保持当前选中 task 和当前 detail 内容
- **AND** SHALL NOT 抛出脚本错误

### Requirement: Task Segment Final Claim 展示
Claude Log 页面 SHALL 将 Task Segment 的 `finalClaim` 展示为 Agent 最终声明，并明确该内容是 agent 自述而非任务成功证据。

#### Scenario: 展示 final claim 摘要
- **WHEN** 当前 task 包含 `finalClaim`
- **THEN** task detail SHALL 显示“Agent 最终声明”区块
- **AND** 默认 SHALL 展示不超过 160 字符的摘要
- **AND** SHALL 显示该声明不代表任务成功的提示

#### Scenario: 展开 final claim 全文
- **WHEN** `finalClaim` 超过摘要长度
- **THEN** task detail SHALL 提供折叠的全文查看入口
- **AND** 全文内容 SHALL 经过 HTML 转义
- **AND** 展开全文 SHALL NOT 改变当前选中 task

#### Scenario: 无 final claim
- **WHEN** 当前 task 不包含 `finalClaim`
- **THEN** task detail SHALL 显示空状态或不渲染 Agent 最终声明正文
- **AND** SHALL NOT 显示 undefined/null

### Requirement: Task Segment 错误摘要展示
Claude Log 页面 SHALL 将 Task Segment 的 `errors` 默认展示为短摘要，并将长错误原文折叠，以便用户快速扫描负向证据。

#### Scenario: 展示错误摘要
- **WHEN** 当前 task 的 evidence 包含 `errors`
- **THEN** task detail SHALL 显示错误数量
- **AND** 每条错误默认 SHALL 展示短摘要
- **AND** 单条摘要 SHALL 截断到有限长度，避免撑开页面或遮挡其他 evidence

#### Scenario: 展开错误原文
- **WHEN** 某条 error 原文长于摘要
- **THEN** 页面 SHALL 提供折叠原文查看入口
- **AND** 原文 SHALL 经过 HTML 转义
- **AND** 折叠区 SHALL NOT 默认展开

#### Scenario: 无错误
- **WHEN** 当前 task 的 `errors` 为空或不存在
- **THEN** task detail SHALL 显示错误为空状态
- **AND** SHALL NOT 显示 undefined/null

### Requirement: 左侧稳定 Turn 索引
Claude Log 页面 SHALL 基于完整 session entries 构建稳定 turn 索引，使 Task Segment 的事件定位不受当前类型筛选或搜索筛选改变。

#### Scenario: 完整 entries 构建 turn 归属
- **WHEN** session 加载成功
- **THEN** 页面 SHALL 基于完整 group entries 构建 turn tree
- **AND** 每个可定位 entry SHALL 记录其所属 `_turnKey`
- **AND** 每个可定位 entry SHOULD 记录其 turn root index

#### Scenario: 筛选不改变 turn 归属
- **WHEN** 用户启用 type filter 或搜索 filter
- **THEN** entry 的 `_turnKey` SHALL 保持不变
- **AND** 定位事件 SHALL 使用既有 `_turnKey` 展开 turn
- **AND** SHALL NOT 从过滤后的 entries 重新推断目标事件所属 turn

#### Scenario: Subagent turn 归属
- **WHEN** 目标事件来自 subagent
- **THEN** 页面 SHALL 使用该 subagent group 内的 turn index 定位
- **AND** SHALL 展开对应 subagent group

### Requirement: Task Segment 事件定位到左侧导航
Claude Log 页面 SHALL 支持从 Task Segment 的 `startEventId` 和 `endEventId` 定位到左侧导航中的对应 group、turn 和 entry。

#### Scenario: 定位开始事件到左侧导航
- **WHEN** 当前 task 包含可映射的 `startEventId`
- **AND** 用户点击“定位开始事件”
- **THEN** 页面 SHALL 展开目标 entry 所属 group
- **AND** 页面 SHALL 展开目标 entry 所属 turn
- **AND** 左侧导航 SHALL 滚动到目标 entry 或其 turn header
- **AND** 目标 entry 或其 turn header SHALL 显示高亮状态

#### Scenario: 定位结束事件到左侧导航
- **WHEN** 当前 task 包含可映射的 `endEventId`
- **AND** 用户点击“定位结束事件”
- **THEN** 页面 SHALL 展开目标 entry 所属 group
- **AND** 页面 SHALL 展开目标 entry 所属 turn
- **AND** 左侧导航 SHALL 滚动到目标 entry 或其 turn header
- **AND** 目标 entry 或其 turn header SHALL 显示高亮状态

#### Scenario: 定位不默认替换 task detail
- **WHEN** 用户从 task detail 点击“定位开始事件”或“定位结束事件”
- **THEN** 页面 SHALL 保持当前 Task Segment detail 可见
- **AND** SHALL NOT 默认用原始日志 detail 替换 task detail

#### Scenario: 目标被筛选隐藏
- **WHEN** 目标 entry 存在但被当前 type filter 或搜索 filter 隐藏
- **THEN** 页面 SHALL 展开并滚动到目标 turn header
- **AND** 页面 SHALL 提示目标事件被当前筛选隐藏
- **AND** SHALL NOT 抛出脚本错误

#### Scenario: 事件无法映射
- **WHEN** `startEventId` 或 `endEventId` 无法映射到当前 session 的 entry
- **THEN** 对应定位按钮 SHALL disabled 或展示不可定位提示
- **AND** 页面 SHALL 保持当前 task detail 不变

### Requirement: Viewer 初始化入口唯一且非递归
`viewer/claude-log.html` SHALL 只有一个真实页面初始化入口，页面打开后 SHALL 自动加载项目列表并初始化 workbench 状态。初始化流程 MUST NOT 通过函数声明提升导致 `init()` 调用自身。

#### Scenario: 页面自动初始化
- **WHEN** 用户打开 viewer 页面
- **THEN** 前端调用项目列表加载逻辑
- **AND** 页面不会出现 `Maximum call stack size exceeded`

#### Scenario: 初始化函数非递归
- **WHEN** 前端测试执行 `init()`
- **THEN** `init()` 至多进入一次顶层初始化流程
- **AND** 不会通过 `_origInit` 或等价包装调用自身

### Requirement: Viewer 默认进入 Session 页面
Workbench SHALL 默认展示 `Session` 页面，`Session` 页面内部展示当前 session 的 turns/events 列表和详情。选择或加载 session 后，前端 SHALL 刷新当前页面，但 MUST NOT 自动跳转到 `Tasks` 页面。

#### Scenario: 首屏默认 Session
- **WHEN** viewer 初次加载完成
- **THEN** 左侧导航中 `Session` 处于 active 状态
- **AND** 主工作区展示 session/raw events 相关内容或选择 session 的提示

#### Scenario: 加载 session 不自动进入 Tasks
- **WHEN** 用户选择一个 session 并完成加载
- **THEN** 当前页面仍为 `Session`
- **AND** `Tasks` 页面不会自动运行任务切分

### Requirement: Tasks 页面由用户手动进入
`Tasks` 页面 SHALL 作为左侧一级导航入口存在。任务切分 SHALL 仅在用户点击 `Tasks` 页面或任务切分按钮后触发或展示缓存结果。

#### Scenario: 用户点击 Tasks
- **WHEN** 用户点击左侧 `Tasks`
- **THEN** 主工作区切换到 `Tasks` 页面
- **AND** 若当前 session 已加载，页面展示任务切分入口、加载状态、缓存结果或任务列表

#### Scenario: 未加载 session 时点击 Tasks
- **WHEN** 用户尚未选择 session 并点击 `Tasks`
- **THEN** 页面显示需要先选择 session 的提示
- **AND** 不发送 `/api/task-segments` 请求

### Requirement: 左侧导航作为一级功能入口
Viewer SHALL 使用左侧一级导航展示产品级功能入口，而不是把全局左栏固定为 turn 树。导航 SHALL 至少包含 `Session`、`Tasks`、`Overview`、`Timeline`、`Req / Resp`、`Diff`、`Diagnostics`、`Export`、`Settings`。

#### Scenario: 左侧导航入口齐全
- **WHEN** viewer 页面渲染完成
- **THEN** 左侧导航展示所有 required 功能入口
- **AND** turn/event 列表只在 `Session` 页面内部展示

#### Scenario: 未完成页面有占位
- **WHEN** 用户点击尚未完整实现的数据页面
- **THEN** 主工作区显示清晰的开发中、空状态或需要选择 session 的占位
- **AND** 页面不能空白

### Requirement: 本地 App Shell 视觉迁移
Viewer SHALL 采用本地 App Shell 的视觉方向：左侧导航分组、顶部上下文栏、紧凑按钮、开发者工具风格和高信息密度布局。该视觉迁移 MUST NOT 改变云端已有的数据加载、server、adapter 和 task segmentation API 行为。

#### Scenario: 顶部只承载全局上下文
- **WHEN** viewer 页面渲染完成
- **THEN** 顶部区域展示 Agent、Project、Session、Search、Refresh 等全局上下文控件
- **AND** 页面级操作放在对应页面内部

#### Scenario: 不直接复制设计稿
- **WHEN** 实现 App Shell 视觉迁移
- **THEN** 页面使用真实 API 和当前 viewer 状态
- **AND** 不以静态设计稿或 mock 数据替代真实 session 数据

### Requirement: Agent badge 使用真实 agent
Viewer 的 agent badge SHALL 从后端返回的真实 agent 信息设置。初始 DOM MAY 使用中性占位，但加载完成后 MUST NOT 硬编码为 `claude`，除非后端真实返回的 agent 就是 `claude`。

#### Scenario: 显示真实 agent
- **WHEN** `/api/projects` 或 `/api/viewer/status` 返回 `agent: "opencode"`
- **THEN** agent badge 显示 `opencode`
- **AND** 不显示硬编码的 `claude`

### Requirement: 任务证据定位保持稳定
Task 详情中的开始事件、结束事件、命令、错误和其他 evidence 跳转 SHALL 使用 canonical navigation target 定位到 `Session` 页面内部的对应 turn/event。视觉迁移 MUST NOT 破坏已有 `startEventId` / `endEventId` 定位能力。

#### Scenario: 定位开始事件
- **WHEN** 用户在 Task 详情点击定位开始事件
- **THEN** workbench 切换或保持在 `Session` 页面
- **AND** 左侧或页面内部的对应 turn/event 被滚动到可见位置并高亮

#### Scenario: 未知事件显示可解释状态
- **WHEN** Task evidence 的 event id 无法映射到当前 session entries
- **THEN** 定位按钮禁用或显示无法定位的提示
- **AND** 不抛出 JavaScript 异常

