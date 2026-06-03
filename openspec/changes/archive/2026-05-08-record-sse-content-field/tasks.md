## 1. 实现

- [x] 1.1 在 `recorder.py` 的 `response` 钩子中，构建 SSE record dict 时新增 `sse_content` 字段，值为 `"\n\n".join(sse_events)`

## 2. 验证

- [x] 2.1 验证：SSE 记录中存在 `sse_content` 字段且值等于 `sse_events` 拼接结果
- [x] 2.2 验证：普通 HTTP 记录中不包含 `sse_content` 字段
