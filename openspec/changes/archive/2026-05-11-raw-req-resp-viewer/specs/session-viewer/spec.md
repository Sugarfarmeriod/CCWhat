## ADDED Requirements

### Requirement: Backend API — list req-resp sessions
`server.py` SHALL 提供 `GET /api/req-resp/sessions` 接口，扫描 logs_dir（即 req-resp-dir）下的子目录，返回所有 session 及其对应的日期文件列表。

#### Scenario: List sessions
- **WHEN** 调用 `GET /api/req-resp/sessions`
- **THEN** 返回 `{"sessions": [{"id": "<sessionId>", "dates": ["YYYY-MM-DD", ...]}]}`，按 session ID 排序

#### Scenario: Empty directory
- **WHEN** logs_dir 不存在或无子目录
- **THEN** 返回 `{"sessions": []}`

### Requirement: Backend API — list req-resp records
`server.py` SHALL 提供 `GET /api/req-resp/records?session=<id>&date=<YYYY-MM-DD>` 接口，读取对应 JSONL 文件并返回记录列表。

#### Scenario: Records found
- **WHEN** 调用 `GET /api/req-resp/records?session=<id>&date=<date>`，对应 JSONL 文件存在
- **THEN** 返回 `{"records": [...]}` 数组，每条保留原始字段

#### Scenario: File not found
- **WHEN** 指定 session/date 的 JSONL 文件不存在
- **THEN** 返回 `{"records": []}` 和 HTTP 200

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
