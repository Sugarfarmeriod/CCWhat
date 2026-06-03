## MODIFIED Requirements

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

## ADDED Requirements

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
