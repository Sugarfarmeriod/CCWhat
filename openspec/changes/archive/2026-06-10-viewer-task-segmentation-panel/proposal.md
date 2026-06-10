## Why

第一版纯规则 Task 切分已经提供 `/api/task-segments` 结构化结果，但目前只能通过 API/JSON 手动查看，无法让用户在真实长 session 中快速观察切分质量、证据归属和边界原因。需要在 Claude Log viewer 中加入任务切分面板，把算法结果变成可交互的复盘视图。

## What Changes

- 在 `viewer/claude-log.html` 为当前已加载 session 新增“任务切分”入口。
- 前端调用 `POST /api/task-segments`，只提交当前 `sessionId`，并按 session 在页面内存中缓存结果。
- 新增任务列表视图，展示每个 Task Segment 的标题、类型、状态、文件数量、命令/错误数量、subagent 数量和 ambiguity 标记。
- 新增 Task 详情视图，展示当前 task 的 timeline 摘要、evidence panel、file weights、boundary reasons 和 final claim。
- 支持从 task 详情跳转/定位到对应起止事件附近的原始日志条目，便于从结构化视图回到原始证据。
- 展示 loading、空结果、错误、重新切分和缓存恢复状态。
- 第一版只做展示和人工校准，不修改切分算法，不做 success/failed 评测，不持久化 task segment 结果。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `session-viewer`: Claude Log 页面新增当前 session 的 Task Segment 展示、缓存、详情、证据和边界调试视图。

## Impact

- 影响代码：`viewer/claude-log.html` 前端 UI、样式和交互；必要时补充轻量前端 helper 函数。
- 影响测试：新增前端静态回归测试，覆盖按钮入口、请求 shape、缓存行为、task cards、evidence rendering、boundary reasons 和错误状态。
- API 依赖：复用已存在的 `POST /api/task-segments`，不新增后端算法行为。
- 行为边界：报告视图 `/api/analyze` 保持独立；任务切分面板不写入后端文件、不写入 localStorage、不改变导出包。
