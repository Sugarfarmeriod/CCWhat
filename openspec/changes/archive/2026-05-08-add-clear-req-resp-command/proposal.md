## Why

`proxy` 命令记录的原始 JSONL 日志包含 SSE 原始事件文本、JSON 字符串形式的请求体等难以直接分析的字段。需要一个独立的清洗命令，将原始日志转化为结构化、易于分析的 JSON 格式，供后续分析使用。

## What Changes

- 新增 `clear-req-resp` 子命令，接受日志目录（或单个 JSONL 文件）作为输入
- 对每条原始日志记录执行以下清洗：
  - 将 `request.body`（JSON 字符串）解析为 `request_json` 对象
  - 从 `sse_events` 中重建 `response_json`：提取 `message_start` 的 message 骨架，合并 `content_block_delta` 的 text_delta 为完整 content.text，填入 `message_delta` 的 stop_reason 和 usage
  - 保留 `timestamp`、`domain`、`method`、`url` 顶层字段，并新增 `claude_session_id`（来自请求 header `X-Claude-Code-Session-Id`）
  - 移除 `request`、`response`、`sse_events`、`is_sse` 原始字段
- 输出写入同目录下的 `<原文件名>_parsed.jsonl`（JSONL 格式，每条记录一行）；或指定输出路径

## Capabilities

### New Capabilities

- `clear-req-resp`: 清洗原始 proxy 日志，将请求体解析为 JSON、从 SSE events 重建结构化响应对象

### Modified Capabilities

（无）

## Impact

- 新增 `deep_ai_analysis/commands/clear_req_resp.py`
- 新增 `deep_ai_analysis/parsers/sse_parser.py`（从 SSE events 重建 response_json）
- `deep_ai_analysis/cli.py`：注册新子命令
- 依赖：仅标准库（`json`、`pathlib`），无新增外部依赖
