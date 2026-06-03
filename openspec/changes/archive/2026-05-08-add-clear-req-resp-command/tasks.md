## 1. SSE Parser

- [x] 1.1 创建 `deep_ai_analysis/parsers/__init__.py`
- [x] 1.2 创建 `deep_ai_analysis/parsers/sse_parser.py`，实现 `parse_sse_record(raw: dict) -> dict`：
  - 从 `sse_events` 中按 type 分发提取 message 骨架、拼接 text_delta、获取 stop_reason/usage
  - 从 `request.headers["X-Claude-Code-Session-Id"]` 提取 `claude_session_id`（不存在则 None）
  - 返回 `{"timestamp", "domain", "method", "url", "claude_session_id", "request_json", "response_json"}` 结构

## 2. clear-req-resp 命令

- [x] 2.1 创建 `deep_ai_analysis/commands/clear_req_resp.py`，实现 `clear_req_resp` click 命令：
  - 参数：`input`（JSONL 文件或目录）、`--output`（可选，单文件模式用）
  - 目录模式：遍历 `.jsonl` 文件，逐个调用 parser，输出 `<name>_parsed.jsonl`（JSONL 格式）
  - 单文件模式：输出到 `--output` 指定路径或默认 `<input>_parsed.jsonl`（JSONL 格式）
  - 跳过 `is_sse: false` 记录，打印处理数/跳过数统计

## 3. 注册命令

- [x] 3.1 在 `deep_ai_analysis/cli.py` 中 import 并注册 `clear_req_resp` 命令

## 4. 验证

- [x] 4.1 用 `sample_data/req_resp_log_v1_output.json` 作为输入运行命令，验证输出包含 `claude_session_id` 字段且值正确
- [x] 4.2 验证输出为 JSONL 格式（每条记录占一行）
