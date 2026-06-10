## Why

目前 `web-server` 只提供 REST API，viewer 页面（`index.html`、`claude-log.html`、`req-resp.html`）需要通过本地文件系统 `file://` 方式打开，导致两个问题：
1. 浏览器的 CORS / fetch 限制使页面无法访问本地 API（部分浏览器拒绝 `file://` 发起的跨域请求）
2. 用户启动服务器后需要手动找到并打开 HTML 文件，操作繁琐

## What Changes

- `viewer/server.py` 增加静态文件服务：对 `/`、`/index.html`、`/claude-log.html`、`/req-resp.html` 等路径提供 `viewer/` 目录下对应 HTML 文件的响应
- `web-server` 命令启动完成后自动调用 `webbrowser.open` 打开 `http://127.0.0.1:<port>/claude-log.html`
- HTML 页面中 `apiBase()` 默认值从 `http://127.0.0.1:7789` 改为同域相对路径（`window.location.origin`），避免硬编码端口

## Capabilities

### New Capabilities

- `static-file-serving`: web-server 提供 viewer/ 目录下静态 HTML 文件的 HTTP 服务
- `auto-open-browser`: web-server 启动后自动在浏览器中打开 claude-log.html

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- 修改 `viewer/server.py`：`_make_handler` 增加静态文件路由，`run_server` 增加 `webbrowser.open` 调用
- 修改 `viewer/index.html`、`viewer/claude-log.html`、`viewer/req-resp.html`：`apiBase()` 默认值改为 `window.location.origin`
- 无新依赖（`webbrowser` 是 Python 标准库）
