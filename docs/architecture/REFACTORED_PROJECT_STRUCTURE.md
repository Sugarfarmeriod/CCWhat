# FastAPI 重构后的项目结构

## 后端入口层

```text
viewer/server.py
├── 数据读取 helper
├── HTTP / req-resp / recording / search helper
├── ViewerBackend
├── create_app()
├── _make_handler()
├── ViewerServer
├── create_server()
└── run_server()
```

### `ViewerBackend`

`ViewerBackend` 是 Viewer API 的业务上下文对象。它不直接启动网络服务，只负责保存依赖和构造兼容旧接口的响应。

主要职责：

- 读取项目和会话数据。
- 生成 session report 事件和 turns。
- 执行 scoped search。
- 管理内存态 report store 和 replay store。
- 调用分析报告、任务切分、Dataset 保存等既有业务模块。

### `create_app()`

`create_app()` 是 FastAPI app factory。它负责：

- 创建 `ViewerBackend`。
- 注册 CORS。
- 注册静态页面和所有 `/api/*` 路由。
- 注册路径规范化 middleware。

生产后端的网络框架从这里开始，后续新增 API 应优先挂到 `create_app()`。

### `_make_handler()`

`_make_handler()` 是兼容层，不再承载真实路由实现。

它的用途：

- 支持现有基于 `HTTPServer(("127.0.0.1", 0), _make_handler(...))` 的测试。
- 支持少量直接访问 `RequestHandlerClass` 的兼容测试。

它的限制：

- 依赖 `fastapi.testclient.TestClient`，因此只应在测试/兼容路径使用。
- 不应在新生产代码中继续扩展 stdlib handler 逻辑。

### `ViewerServer`

`ViewerServer` 是 uvicorn 的最小生命周期封装。

它提供：

- `server_port`
- `serve_forever()`
- `shutdown()`
- `server_close()`
- 懒加载的 `RequestHandlerClass`

`RequestHandlerClass` 只在旧测试访问时创建，避免生产启动依赖 `httpx`。

## CLI 集成

```text
ccwhat/commands/run.py
└── _ManagedWebServer Protocol
```

`ccwhat run` 不再依赖 `HTTPServer` 类型，而是通过 `_ManagedWebServer` 协议管理 Viewer：

- `serve_forever()`
- `shutdown()`
- `server_close()`

这样 CLI 只依赖生命周期能力，不关心底层是 stdlib HTTPServer 还是 uvicorn。

## 依赖变化

```text
pyproject.toml
├── fastapi >= 0.115
├── uvicorn >= 0.30
└── dev: httpx >= 0.27
```

- `fastapi` 和 `uvicorn` 是运行时依赖。
- `httpx` 只用于 `TestClient` 兼容测试，因此放在 dev extra。

## 测试结构

本次迁移主要验证以下测试面：

- `tests/test_current_session_analysis.py`
- `tests/test_export_import_packages.py`
- `tests/test_global_session_search_api.py`
- `tests/test_session_rename.py`
- `tests/test_task_dataset_save_export_api.py`
- `tests/test_task_segmentation_api.py`
- `tests/test_viewer_server_threading.py`

`tests/test_viewer_server_threading.py` 已更新为验证 `ViewerServer`，不再断言 `ThreadingHTTPServer`。

## 后续新增接口建议

新增后端接口时优先遵循以下顺序：

1. 将业务逻辑放进独立模块或 `ViewerBackend` 方法。
2. 在 `create_app()` 中注册 FastAPI route。
3. 如果旧测试仍需要 stdlib HTTPServer，复用 `_make_handler()`，不要新增 handler 分支。
4. 为路由补最小 API 测试，再考虑是否需要真实 uvicorn smoke。
