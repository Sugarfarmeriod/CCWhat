## Why

`claude-log.html` 展示 Claude Code 的会话日志，其中 assistant 条目包含 `message.id`（`msg_bdrk_xxx`）。`req-resp.html` 支持通过该 ID 搜索对应的原始 HTTP 请求/响应日志。两者目前相互独立，用户需要手动复制 `message.id` 到 `req-resp.html` 搜索，操作繁琐。

## What Changes

- `claude-log.html` 的 assistant 条目右侧明细面板（「Message 元数据」区块）中，在 `message.id` 旁新增「在请求日志中查看」链接按钮
- 点击后在新 tab 打开 `req-resp.html?q=<message.id>`，页面自动将搜索框填入该 ID 并触发过滤
- `req-resp.html` 支持读取 URL query 参数 `q`，页面加载完成后自动填入搜索框并触发 `renderList()`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `session-viewer`（claude-log.html）：assistant 明细中 message.id 旁新增跳转链接
- `session-viewer`（req-resp.html）：支持 URL query 参数 `?q=` 自动填充搜索框

## Impact

- `viewer/claude-log.html`：Message 元数据区块中，`message.id` 行新增外链按钮
- `viewer/req-resp.html`：页面初始化时读取 `?q=` 参数，填入搜索框并触发过滤
