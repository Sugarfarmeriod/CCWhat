## 1. 合并基线与风险确认

- [x] 1.1 基于 `origin/main` 建立实施分支或临时工作树，确认云端稳定性修复作为合并底座。
- [x] 1.2 对比本地 `main` 与 `origin/main` 的差异，列出需要保留的本地 UI 外壳元素，禁止整文件覆盖 `viewer/claude-log.html`。
- [x] 1.3 保留云端 `viewer/server.py` 的 `ThreadingHTTPServer`、`ccwhat/adapters/opencode.py` 的跨线程 SQLite 修复、`ccwhat/commands/run.py` 的 viewer agent probe。
- [x] 1.4 处理 `ccwhat/commands/run.py` 等合并冲突，确保 agent mismatch fail-fast 和本地已有测试语义都保留。

## 2. 修复云端初始化 bug

- [x] 2.1 移除或重构 `viewer/claude-log.html` 中会导致自递归的 `_origInit = init` 包装写法。
- [x] 2.2 将初始化逻辑拆成唯一 `init()` 入口和必要 helper，例如项目加载、workbench 初始化、按钮状态刷新。
- [x] 2.3 确认页面打开后自动执行初始化，且不会抛出 `Maximum call stack size exceeded`。
- [x] 2.4 增加或更新 DOM 测试，覆盖 `init()` 非递归和首屏自动初始化。

## 3. 保持云端默认行为

- [x] 3.1 将 workbench 默认 active page 固定为 `sessions`。
- [x] 3.2 确认 `loadSession()` 完成后刷新当前页面，但不自动跳转到 `tasks`。
- [x] 3.3 确认 `Tasks` 页面只在用户点击左侧入口或任务切分按钮后触发/展示任务切分。
- [x] 3.4 更新静态测试，断言默认页为 `Session`，不是 `Tasks`。

## 4. 迁移本地 App Shell 视觉

- [x] 4.1 从本地 viewer 迁移左侧导航视觉和分组结构，包含 `Session`、`Tasks`、`Overview`、`Timeline`、`Req / Resp`、`Diff`、`Diagnostics`、`Export`、`Settings`。
- [x] 4.2 迁移顶部上下文栏视觉，保留 Agent、Project、Session、Search、Refresh 等全局控件。
- [x] 4.3 将页面级操作放回对应页面内部，避免所有功能按钮挤在顶栏。
- [x] 4.4 为尚未完整实现的页面补齐开发中/空状态占位，避免点击后空白。
- [x] 4.5 保持真实 API 数据渲染，不引入设计稿 mock 数据作为运行时内容。

## 5. 保留证据定位与任务交互

- [x] 5.1 保留云端 canonical navigation target 构建逻辑，确保视觉迁移不破坏 `startEventId` / `endEventId` 定位。
- [x] 5.2 确认 Task 详情中的定位开始事件、定位结束事件能切回 `Session` 页面并滚动高亮对应 turn/event。
- [x] 5.3 确认未知 event id 的定位按钮禁用或显示提示，不抛 JS 异常。
- [x] 5.4 保留 Task 卡片点击切换详情、debug boundaries、final claim 摘要和错误折叠展示。

## 6. Agent 与端口复用稳定性

- [x] 6.1 确认 agent badge 初始可为中性占位，但加载后使用真实 agent 名称。
- [x] 6.2 保留 `/api/viewer/status` 或 `/api/projects` agent 探测逻辑，避免硬编码 `claude`。
- [x] 6.3 确认已有 viewer 端口服务其他 agent 时，`ccwhat run` fail fast 且不会打开 stale viewer。
- [x] 6.4 保留并通过 OpenCode threaded viewer 相关测试。

## 7. 测试与验证

- [x] 7.1 运行 `python3 -m pytest -q`，确保 Python 全量测试通过。
- [x] 7.2 运行 `node tests/test_task_segmentation_dom.js`，确保 DOM 交互测试通过。
- [x] 7.3 更新 `tests/test_task_segmentation_frontend.py`，覆盖左侧导航、默认 Session、手动 Tasks、agent badge、init 非递归。
- [x] 7.4 运行 `openspec validate stabilize-cloud-viewer-and-port-local-shell-ui --strict`。
- [x] 7.5 使用真实 Claude session 手动检查：打开 viewer、加载 session、默认停留 Session、点击 Tasks、定位 task 开始/结束事件。
- [x] 7.6 使用真实 OpenCode 或 Codex session 手动检查：agent badge、session load、Raw Events、Tasks 入口、端口复用行为。
