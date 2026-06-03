### Requirement: Parse request body
`clear-req-resp` SHALL 将原始日志记录中 `request.body` 字符串解析为 JSON 对象，存入输出记录的 `request_json` 字段。

#### Scenario: Valid JSON request body
- **WHEN** 原始记录的 `request.body` 是合法 JSON 字符串
- **THEN** 输出记录包含 `request_json` 字段，值为解析后的 JSON 对象

#### Scenario: Invalid JSON request body
- **WHEN** 原始记录的 `request.body` 不是合法 JSON
- **THEN** 该条记录被跳过，并在 stderr 打印警告信息

### Requirement: Reconstruct response from SSE events
`clear-req-resp` SHALL 从 `sse_events` 列表中重建结构化的 `response_json` 对象，其结构为 `{"message": {...}}`。

#### Scenario: Reconstruct message skeleton
- **WHEN** `sse_events` 中存在 `type: "message_start"` 事件
- **THEN** `response_json.message` 包含 `id`、`type`、`role`、`model` 字段，值来自该事件的 `message` 对象

#### Scenario: Concatenate text deltas
- **WHEN** `sse_events` 中存在一个或多个 `type: "content_block_delta"` 且 `delta.type == "text_delta"` 的事件
- **THEN** `response_json.message.content.text` 为所有 `delta.text` 按顺序拼接的完整字符串

#### Scenario: Extract stop reason and usage
- **WHEN** `sse_events` 中存在 `type: "message_delta"` 事件
- **THEN** `response_json.message.stop_reason` 来自该事件的 `delta.stop_reason`，`response_json.message.usage` 来自该事件的 `usage` 对象

### Requirement: Output cleaned record
`clear-req-resp` SHALL 输出仅包含 `timestamp`、`domain`、`method`、`url`、`claude_session_id`、`request_json`、`response_json` 的清洗后记录，移除原始的 `request`、`response`、`sse_events`、`is_sse` 字段。`claude_session_id` 取自原始记录的 `request.headers["X-Claude-Code-Session-Id"]`，若不存在则为 `null`。

#### Scenario: Output structure matches spec
- **WHEN** 一条 SSE 记录被成功清洗
- **THEN** 输出 JSON 对象仅包含 `timestamp`、`domain`、`method`、`url`、`claude_session_id`、`request_json`、`response_json` 七个顶层字段

#### Scenario: claude_session_id extracted from header
- **WHEN** 原始记录的 `request.headers` 包含 `X-Claude-Code-Session-Id`
- **THEN** 输出记录的 `claude_session_id` 值等于该 header 的值

#### Scenario: claude_session_id absent
- **WHEN** 原始记录的 `request.headers` 不包含 `X-Claude-Code-Session-Id`
- **THEN** 输出记录的 `claude_session_id` 为 `null`

### Requirement: Skip non-SSE records
`clear-req-resp` SHALL 跳过 `is_sse: false` 的记录，不写入输出文件。

#### Scenario: Non-SSE record skipped
- **WHEN** 输入 JSONL 中存在 `is_sse: false` 的记录
- **THEN** 该记录不出现在输出文件中，命令在 stderr 打印跳过数量

### Requirement: File and directory input
`clear-req-resp` SHALL 支持单个 JSONL 文件或目录作为输入，输出为 JSONL 格式（每条清洗记录占一行）。

#### Scenario: Single file input
- **WHEN** 用户执行 `deep-ai-analysis clear-req-resp <file.jsonl>`
- **THEN** 清洗结果写入 `<file>_parsed.jsonl`（与输入同目录），或 `--output` 指定的路径

#### Scenario: Directory input
- **WHEN** 用户执行 `deep-ai-analysis clear-req-resp <dir/>`
- **THEN** 遍历目录下所有 `.jsonl` 文件，每个文件生成对应的 `_parsed.jsonl` 至同目录

#### Scenario: Output path override
- **WHEN** 用户执行 `deep-ai-analysis clear-req-resp <file.jsonl> --output <out.jsonl>`
- **THEN** 结果写入 `<out.jsonl>`；目录模式下不支持 `--output`，提示错误

#### Scenario: JSONL output format
- **WHEN** 输入文件包含多条记录
- **THEN** 输出文件每行为一条合法 JSON（JSONL 格式），不带尾随逗号或数组包装
