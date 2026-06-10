## Why

现有 viewer 只能查看 Claude Code 会话对话，无法直接浏览底层的 HTTP 请求/响应原始日志（`*_parsed.jsonl`）。需要一个专门的原始日志查看页面，以列表+明细的布局方便快速浏览和分析每次 API 调用。

## What Changes

- 新增 `viewer/logs.html`：ClaudeCode 原始日志查看页面
  - 顶部：session 筛选器（从后端获取 logs 目录下的 session 列表）
  - 左列：日志列表，每条显示摘要（时间、model、token 用量、response 摘要）
  - 右列：选中条目的完整明细（request_json + response_json，分区折叠展示）
- 后端新增 `GET /api/logs` 接口：扫描 logs_dir 下所有 `*_parsed.jsonl`，返回记录列表（含 session 过滤）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `session-viewer`: 后端新增 `/api/logs` 接口；前端新增 `logs.html` 页面

## Impact

- `viewer/server.py`：新增 `/api/logs` 路由
- `viewer/logs.html`：新增独立页面
