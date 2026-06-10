## Context

`viewer/server.py` 使用 Python 标准库 `http.server.BaseHTTPRequestHandler`。当前 `do_GET` 只处理 `/api/…` 路径，其他路径返回 404 JSON。`viewer/` 目录与 `server.py` 同级，包含 `index.html`、`claude-log.html`、`req-resp.html`。

三个 HTML 页面中都有 `apiBase()` 函数，目前硬编码默认值为 `http://127.0.0.1:7789`，通过 HTTP 服务后应使用同域地址避免跨域。

## Goals / Non-Goals

**Goals:**
- GET `/`、`/<name>.html` 返回 `viewer/<name>.html`（或 `viewer/index.html`）的内容
- `run_server` 打印就绪消息后立即调用 `webbrowser.open` 打开 `claude-log.html`
- HTML 页面 `apiBase()` 默认改为 `window.location.origin`（同域，不依赖硬编码端口）

**Non-Goals:**
- 不服务 JS/CSS 等外部资源（三个页面都是单文件，无外部资源依赖）
- 不添加目录浏览
- 不缓存控制（开发工具，无需 Cache-Control）

## Decisions

**静态路由实现：** 在 `do_GET` 的 `else` 分支前插入静态文件判断：
- 路径 `/` 或 `/index.html` → `viewer/index.html`
- `/claude-log.html` → `viewer/claude-log.html`
- `/req-resp.html` → `viewer/req-resp.html`
- Content-Type: `text/html; charset=utf-8`

`viewer_dir` 通过 `Path(__file__).parent` 获得（`server.py` 与 HTML 同目录），无需额外参数传入 `_make_handler`。

**自动打开浏览器：** `run_server` 打印就绪行后，调用 `webbrowser.open(f"http://127.0.0.1:{port}/claude-log.html")`。打开失败不影响服务器启动（`webbrowser.open` 失败时静默忽略）。

**`apiBase()` 默认值：** 将三个 HTML 中 `value="http://127.0.0.1:7789"` 改为 `value=""` 并在 `apiBase()` 中 fallback 到 `window.location.origin`。

## Risks / Trade-offs

- [风险] 用户通过 `file://` 打开旧书签时 `apiBase()` 返回空字符串 → `fetch('')` 会失败。可接受：通过 HTTP 服务是新推荐方式，`file://` 方式已在 README 说明
- [权衡] `webbrowser.open` 在无桌面环境（headless server）会静默失败，不影响服务正常运行
