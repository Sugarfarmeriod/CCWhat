## 1. 后端

- [x] 1.1 在 `viewer/server.py` 中实现 `get_logs(logs_dir, session_filter)` 函数：扫描所有 `*_parsed.jsonl`，收集记录和 session 列表，按 timestamp 降序排列
- [x] 1.2 在 HTTP handler 中注册 `GET /api/logs` 路由，支持 `?session=` query 参数

## 2. 前端

- [x] 2.1 创建 `viewer/logs.html`：顶部 session 筛选器 + API URL 输入，页面主体为左右分栏布局
- [x] 2.2 实现左栏日志列表：调用 `/api/logs`，每条显示时间、model、stop_reason badge、token 数、response 摘要
- [x] 2.3 实现右栏日志明细：点击列表项后渲染完整信息（基本信息、response 内容、token usage、折叠 request_json）
- [x] 2.4 实现 session 筛选：切换 session 时重新请求并刷新列表

## 3. 验证

- [x] 3.1 启动服务，打开 `viewer/logs.html`，验证列表加载、筛选、点击明细功能正常
