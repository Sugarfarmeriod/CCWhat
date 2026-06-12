## Why

前两个 change 已经完成了 Turn 投影和 Trace 树双视图，但右侧 Detail 仍可能受到当前类型筛选或简化渲染影响，导致用户在默认视图或调试筛选后无法看到完整证据。

这一阶段要把产品主线补完整：左侧负责降噪导航，右侧永远负责完整证据。

## What Changes

- 让默认视图中的 `Step` 点击后，右侧 Detail 展示其 underlying Minimal Turn 的完整内容，而不是只展示摘要。
- 让调试视图中的 internal Turn（例如 `permission-mode`、`file-history-snapshot`、`queue-operation`、system/context/hook/unknown）点击后，右侧 Detail 展示完整字段和原始 JSON。
- 修复类型筛选对 Detail 的影响：调试筛选只影响左侧 Trace 树可见节点，不裁剪已选中 Turn 的 Detail 内容。
- 强化 tool 证据展示：`tool_use` 展示完整 input，`tool_result` 展示完整 result，并保留 `tool_use_id`、error 状态和 raw JSON。
- 修复 Task-first 闭环：任务切分生成结果后，Session Trace SHALL 立即使用 `Task -> 会话 -> Step/Turn` 结构；确认按钮只表达确认状态，不再决定是否进入 Task-first。
- 保留现有前端结构，不重写页面、不修改后端 API、不改变 Minimal Turn / projection / Task segmentation 算法。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 明确 Session Trace 右侧 Detail 的完整证据契约，并补齐 Task segmentation 结果到 Session Trace 的 Task-first 闭环。

## Impact

- 主要影响 [viewer/claude-log.html](/Users/elon2ge/workspace/CCWhat/viewer/claude-log.html) 中的 Turn Detail 渲染函数、Trace node selection、类型筛选行为、raw JSON 展示、Task-first Trace source 选择。
- 需要更新或新增 `tests/test_task_segmentation_frontend.py`、`tests/test_task_segmentation_dom.js`，覆盖默认视图 Step Detail、调试视图 internal Turn Detail、筛选后 Detail 不裁剪等行为。
- 不新增后端接口，不新增依赖。
