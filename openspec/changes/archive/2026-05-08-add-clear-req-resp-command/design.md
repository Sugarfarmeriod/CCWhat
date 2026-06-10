## Context

原始 JSONL 日志（`proxy` 命令输出）中，每条 SSE 记录包含：
- `request.body`：字符串形式的 JSON，是 Anthropic API 请求体
- `sse_events`：原始 SSE event 文本列表，每条格式为 `event: <type>\ndata: <json>`
- `response.body`：所有 events 拼接的原始文本

清洗目标参考 `sample_data/req_resp_log_v1_parsed.json`：
- `request_json`：直接 `json.loads(request.body)`
- `response_json.message`：从 sse_events 重建，包含 id、type、role、model、stop_reason、content.text（拼接所有 text_delta）、usage（来自 message_delta）

## Goals / Non-Goals

**Goals:**
- 将 `request.body` 解析为 `request_json`
- 从 `sse_events` 重建 `response_json`（message 骨架 + 拼接 text_delta + stop_reason/usage）
- 支持处理单个 JSONL 文件或整个日志目录
- 输出为 JSON 文件（pretty-printed），默认路径为 `<input>_parsed.json`

**Non-Goals:**
- 不处理非 SSE（`is_sse: false`）的普通 HTTP 记录（跳过或直接透传）
- 不修改原始日志文件
- 不支持流式/增量写入（一次性读写）

## Decisions

### SSE event 解析策略

逐条遍历 `sse_events`，提取 `data:` 行，`json.loads` 后按 `type` 字段分发：
- `message_start` → 提取 message 骨架（id, type, role, model）
- `content_block_delta` 且 `delta.type == "text_delta"` → 累积 `delta.text`
- `message_delta` → 提取 stop_reason 和 usage

**Why**: SSE event 格式固定，按 type 分发是最直接且鲁棒的方式，避免正则解析脆弱性。

### 独立 parser 模块

SSE 重建逻辑放入 `deep_ai_analysis/parsers/sse_parser.py`，命令层只负责 IO。

**Why**: 逻辑与 CLI 解耦，便于单独测试，也为后续扩展（如批量分析）预留入口。

### 输出格式

单个输入文件 → 单个输出 JSON 文件（非 JSONL），pretty-printed，便于人工阅读。
目录输入 → 遍历所有 `.jsonl` 文件，每个文件生成对应的 `_parsed.json`。

## Risks / Trade-offs

- **SSE event 格式变化**：若上游更改 event 类型结构，parser 需同步更新 → 通过 sample_data 测试固化行为
- **非 SSE 记录**：当前跳过（`is_sse: false`），不写入输出 → 在 CLI 输出中打印跳过数量告知用户
