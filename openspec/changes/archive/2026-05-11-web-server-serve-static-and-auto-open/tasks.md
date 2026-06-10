## 1. viewer/server.py — 静态文件路由

- [x] 1.1 在 `_make_handler` 的 `do_GET` 中，`else` 分支前插入静态文件路由：`/` 和 `/index.html` → `viewer/index.html`，`/claude-log.html`、`/req-resp.html` 同理
- [x] 1.2 添加 `_send_file(path)` 辅助方法：读取文件内容，以 `text/html; charset=utf-8` 返回 200 响应

## 2. viewer/server.py — 自动打开浏览器

- [x] 2.1 在 `run_server` 打印就绪消息后，调用 `webbrowser.open(f"http://127.0.0.1:{port}/claude-log.html")`
- [x] 2.2 顶部添加 `import webbrowser`

## 3. HTML 页面 — apiBase() 默认值

- [x] 3.1 修改 `viewer/index.html`：API URL 输入框 `value` 改为空，`apiBase()` 中 fallback 改为 `window.location.origin`
- [x] 3.2 修改 `viewer/claude-log.html`：同上
- [x] 3.3 修改 `viewer/req-resp.html`：同上

## 4. 验证

- [x] 4.1 运行 `deep-ai-analysis web-server`，确认浏览器自动打开 `http://127.0.0.1:7789/claude-log.html`
- [x] 4.2 确认三个 HTML 页面均可通过 HTTP 地址访问且 API 请求正常（无跨域错误）
