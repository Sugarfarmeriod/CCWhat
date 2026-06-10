## Why

mitmproxy 抓包产生的原始 HTTP 请求/响应日志（`~/.deep-ai-analysis/raw-req-resp/<sessionId>/<date>.jsonl`）目前无法直观浏览。需要一个专用页面，展示每次 API 调用的原始内容，便于调试和分析。

## What Changes

- 新增 `viewer/req-resp.html`：原始请求/响应日志查看页面
  - 顶部：session 选择器 + 日期选择器 + API URL 配置
  - 左侧：日志列表（时间、URL、SSE 标记、状态码）
  - 右侧：选中记录的明细（请求 headers/body、响应 headers/body 或 SSE events）
- 后端新增 `GET /api/req-resp/sessions`：列出 req-resp-dir 下所有 session 目录
- 后端新增 `GET /api/req-resp/records?session=<id>&date=<YYYY-MM-DD>`：读取指定 session+日期的 JSONL 文件，返回记录列表

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `session-viewer`: 后端新增两个 `/api/req-resp/` 接口；前端新增 `req-resp.html`

## Impact

- `viewer/server.py`：新增 `/api/req-resp/sessions` 和 `/api/req-resp/records` 路由
- `viewer/req-resp.html`：新增独立页面
- `viewer/server.py` 的 `run_server()` 已有 `logs_dir`（即 req-resp-dir）参数，直接复用
