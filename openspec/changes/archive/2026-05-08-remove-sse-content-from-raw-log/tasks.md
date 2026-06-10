## 1. 实现

- [x] 1.1 在 `recorder.py` 中删除 `record["sse_content"] = "\n\n".join(sse_events)` 这一行

## 2. 验证

- [x] 2.1 验证：SSE 记录中不再包含 `sse_content` 字段
- [x] 2.2 验证：`sse_events` 和 `response.body` 字段仍正常存在
