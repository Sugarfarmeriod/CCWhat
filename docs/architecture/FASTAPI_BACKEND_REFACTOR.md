# FastAPI 后端重构说明

## 背景

CCWhat Viewer 之前使用 `BaseHTTPRequestHandler` 手写路由、CORS、JSON body 读取和二进制响应。该实现可用，但所有路由逻辑集中在一个 handler class 中，后续新增接口、测试隔离和异常处理成本较高。

v2.2.7 将生产后端入口迁移到 FastAPI + uvicorn，同时保留旧 `_make_handler()` 兼容层，保证现有测试和潜在外部调用可以继续工作。

## 新入口

- `viewer.server.create_app(...)`
  - FastAPI 应用工厂。
  - 注册静态页面、Viewer API、分析报告、Dataset、搜索、导出和 replay 路由。
  - 通过 `app.state.viewer_backend` 持有每个 app 实例独立的内存状态。

- `viewer.server.ViewerBackend`
  - 集中保存依赖和状态：`projects_dir`、`logs_dir`、`config_path`、adapter、analyzer 配置、Dataset registry root、report store、replay store。
  - 保留旧接口契约的业务响应组装逻辑。

- `viewer.server.ViewerServer`
  - uvicorn 启动封装。
  - 预绑定本地 socket 以支持 `port=0` 自动分配端口。
  - 暴露 `serve_forever()`、`shutdown()`、`server_close()`，兼容 CLI 管理生命周期。

- `viewer.server._make_handler(...)`
  - 旧 stdlib HTTP 测试兼容层。
  - 内部创建 FastAPI app，并用 `TestClient` 转发请求。
  - 仅在旧测试或兼容调用显式使用时才导入 `TestClient`，生产 `create_server()` 不依赖 `httpx`。

## 保留的接口契约

以下接口保持旧请求和响应格式：

- 静态页面：`/`、`/index.html`、`/claude-log.html`、`/req-resp.html`
- Viewer 状态：`GET /api/viewer/status`
- 录制状态：`GET /api/recording/status`
- 项目与会话：`GET /api/projects`、`GET /api/session/{sessionId}`
- 日志与 HTTP 关联：`GET /api/logs`、`GET /api/message-http/{sessionId}/{messageId}`、`GET /api/message-source/{sessionId}/{messageId}`
- 请求响应：`GET /api/req-resp/sessions`、`GET /api/req-resp/records`
- 全局搜索：`GET /api/search`
- 导出：`GET /api/export`
- 分析报告：`POST /api/analyze`、`GET /api/analysis-report/{reportId}`、`GET /api/analysis-report/{reportId}/export`
- 任务切分：`POST /api/task-segments`
- Dataset：`POST /api/save-task-dataset`、`GET /api/task-datasets/{datasetId}/download`
- Replay：`POST /api/replay/session`、`POST /api/replay/send`、`GET /api/replay/status`
- Session 重命名：`POST /api/session/{sessionId}/rename`

## 兼容注意事项

- `/api/projects` 继续返回数组，不包一层 `{projects: ...}`。
- `/api/search` 继续默认 `scope=current_session`，返回 `ok/results/truncated/warnings`。
- `/api/analyze`、`/api/task-segments`、`/api/save-task-dataset` 继续接收单个 `sessionId` 字段。
- `/api/replay/*` 继续复用原始请求体和原始 headers，只替换用户编辑文本。
- Dataset 下载路径穿越校验在 FastAPI middleware 和 `_make_handler` 兼容层各处理一次，避免 Starlette 路径规范化把旧 400 变成 404。

## 验证

- 编译检查：`PYTHONPYCACHEPREFIX=/tmp/ccwhat-pycache .venv/bin/python -m compileall ccwhat viewer tests`
- Viewer/API 测试：`220 passed`
- 真实 uvicorn smoke：启动 `create_server(0, ...)` 后请求 `/api/viewer/status` 返回 200。
