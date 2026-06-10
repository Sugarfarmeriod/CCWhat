## 1. 后端

- [x] 1.1 在 `get_req_resp_records()` 中，对每条记录调用辅助函数提取 SSE `message_start.message.id`，注入为 `_message_id`（非 SSE 记录注入 `None`）

## 2. 前端

- [x] 2.1 在 `req-resp.html` 顶部 session/date 选择器旁新增搜索框（`<input>`）
- [x] 2.2 在 `renderList()` 中根据搜索框内容过滤记录：`_message_id` 包含搜索词 或 URL 包含搜索词（大小写不敏感）；搜索框 `oninput` 触发 `renderList()`

## 3. 验证

- [x] 3.1 验证：加载记录后，按 `message_id` 搜索，列表正确过滤；清空搜索恢复全部记录
