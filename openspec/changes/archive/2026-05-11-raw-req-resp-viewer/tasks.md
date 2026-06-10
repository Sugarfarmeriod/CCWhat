## 1. 后端接口

- [x] 1.1 实现 `get_req_resp_sessions(logs_dir)` 函数：扫描子目录，收集 sessionId 及其下 YYYY-MM-DD.jsonl 日期列表
- [x] 1.2 实现 `get_req_resp_records(logs_dir, session_id, date)` 函数：读取对应 JSONL 文件，返回记录列表
- [x] 1.3 在 HTTP handler 中注册 `GET /api/req-resp/sessions` 和 `GET /api/req-resp/records` 路由

## 2. 前端页面

- [x] 2.1 创建 `viewer/req-resp.html`：顶部 session+日期选择器，主体左右分栏
- [x] 2.2 实现左栏列表：加载记录，每条显示时间、URL path、is_sse badge、状态码
- [x] 2.3 实现右栏明细：基本信息、请求 headers（折叠）、请求 body（折叠）、响应 headers（折叠）、SSE events / 响应 body

## 3. 验证

- [x] 3.1 启动服务，打开 `viewer/req-resp.html`，选择 session 和日期，验证列表和明细正常展示
