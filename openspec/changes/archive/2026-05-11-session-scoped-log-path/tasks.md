## 1. 修改 recorder.py

- [x] 1.1 修改 `_jsonl_path(self, session_id: str) -> Path`：路径改为 `self._output_dir / session_id / YYYY-MM-DD.jsonl`
- [x] 1.2 在 `response()` 钩子中从 `flow.request.headers.get("X-Claude-Code-Session-Id", "unknown")` 提取 `session_id`，传给 `_jsonl_path(session_id)` 和 `_append_record()`

## 2. 验证

- [x] 2.1 验证：写入记录时路径包含 sessionId 子目录（`output_dir/session_id/YYYY-MM-DD.jsonl`）
- [x] 2.2 验证：无 session header 时，路径使用 `unknown` 子目录
