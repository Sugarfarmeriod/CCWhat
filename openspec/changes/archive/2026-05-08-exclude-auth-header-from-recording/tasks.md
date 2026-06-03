## 1. 实现过滤逻辑

- [x] 1.1 在 `proxy.py` 中定义常量 `SENSITIVE_HEADERS = {"authorization"}`（小写集合）
- [x] 1.2 在 `response` 钩子的普通请求记录路径中，构建 `request_headers` dict 时过滤掉键名 `.lower()` 在 `SENSITIVE_HEADERS` 中的 header
- [x] 1.3 在 SSE 流结束写入 JSONL 的路径中，同样过滤 `request_headers`

## 2. 验证

- [x] 2.1 手动测试：发送带 `Authorization: Bearer test-token` 的请求，确认生成的 JSONL 记录中不含该 header
- [x] 2.2 手动测试：确认其他 headers（如 `Content-Type`、`User-Agent`）仍正常保留
- [x] 2.3 手动测试 SSE 场景：确认 SSE 记录的 `request.headers` 同样不含 `Authorization`
