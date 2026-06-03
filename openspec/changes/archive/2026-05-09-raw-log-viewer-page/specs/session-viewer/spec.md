## ADDED Requirements

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
