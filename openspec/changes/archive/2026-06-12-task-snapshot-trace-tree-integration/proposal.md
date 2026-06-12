## Why

前两个 change 已经完成了 `Trace -> 会话 -> Turn` 的数据层和 UI 浏览结构。当前 Task 切分结果仍主要停留在独立 `Tasks` 页面中，用户需要在 Task 页面和 Session Trace 页面之间来回跳转，无法在同一条主 Trace 树里理解“这个 Task 包含哪些会话和 Turn”。

同时，Tools / Skills 列表还没有稳定入口。它们是理解 Agent 执行环境的重要上下文，但不应该放进某个 Task 或会话内部；它们应该作为当前 Trace 的全局快照固定在树顶部。

本 change 是 Trace 树重构的第三步：将确认后的 Task 切分结果注入 `Session` 页面的 Trace 树，并在 Trace 顶部增加 `Tools / Skills Snapshot` 节点。

## What Changes

- `Session` 页面的 Trace 树顶部新增 `Tools / Skills Snapshot` 节点。
- 点击 `Tools / Skills Snapshot` 后，右侧展示当前 Trace 初始可用 Tools 和 Skills 列表。
- 未确认 Task 切分时，Trace 树保持：
  - `Tools / Skills Snapshot`
  - `会话 -> Turn`
- Task 切分完成并确认后，Trace 树切换为：
  - `Tools / Skills Snapshot`
  - `Task -> 会话 -> Turn`
- Task 节点展示 Task label、标题/摘要、类型、状态、置信度、覆盖的会话/Turn 数量。
- 点击 Task 节点后，右侧展示 Task 基础摘要和该 Task 下的会话列表。
- 点击 Task 下的会话或 Turn，继续复用已有会话详情和 Turn 极简详情。
- `Tasks` 页面继续保留作为 Task 切分预览、确认和调试入口。
- Task 注入 SHALL 基于现有 task segment 结果和已有 Conversation/minimal Turn 导航索引，不修改任务切分算法。

## Non-Goals

- 不实现 Task 成功率评测、失败归因或复杂 outcome 面板。
- 不实现人工拖拽调整 Task / 会话 / Turn 边界。
- 不实现复杂 Tools / Skills 版本 diff。
- 不实现 Tools / Skills Changed Turn 的完整变化检测；本 change 只保留扩展点和基础占位规则。
- 不修改后端 API，除非现有前端数据完全无法派生 Snapshot。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 将已确认的 Task Segment 注入 Session Trace 树，并展示 Trace 级 Tools / Skills Snapshot。

## Impact

- 主要影响 `viewer/claude-log.html` 的 Trace tree node 派生、节点渲染、选中状态、右侧 detail、Task 切分确认流程和定位逻辑。
- 需要更新前端静态测试和 DOM 行为测试，覆盖 Snapshot 节点、Task 注入前后树形结构、Task 节点点击、Task 下会话/Turn 导航、Task 定位和不重复 Snapshot。
- 不修改 `ccwhat/task_segments` 的切分算法。
