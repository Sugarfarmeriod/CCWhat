## Why

当前 viewer 的 Turn 仍接近“用户消息分组”，缺少“会话”这一层，也没有把 Turn 收敛成最小执行单位。后续要实现 `Trace -> Task -> 会话 -> Turn` 树状结构，必须先把数据层级打正，否则 UI、Task 注入和定位都会继续建立在错误抽象上。

本 change 是 Trace 树重构的第一步，只建立 `Trace -> 会话 -> 最小 Turn` 数据层，不重做左侧树 UI，不接入 Task 注入，也不处理 Tools / Skills Snapshot。

## What Changes

- 引入前端派生的 `Conversation` 数据结构，表示一次用户请求到 Agent 完成本次反馈之间的交互单元。
- 将现有 Turn 派生逻辑从“用户消息分组”改为“会话内最小执行单位”。
- 一个 Turn SHALL 只表示一种执行片段，例如 user message、thinking/reasoning、assistant text、tool_use、tool_result、context/system。
- 如果一个原始 assistant entry 中包含多个 content block，派生层 SHALL 拆成多个 Turn。
- 保留原始 entry/event 到 Conversation 和 Turn 的稳定映射，支持后续定位和 Task 注入。
- 现有 UI 可继续沿用当前样式展示，但内部数据源应可提供 Conversation 和 minimal Turn。
- 不新增后端 API，不改变 task segmentation 算法。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 增加 Conversation 数据层和 minimal Turn 派生契约，为后续 Trace Tree UI 提供稳定数据基础。

## Impact

- 主要影响 `viewer/claude-log.html` 中 session entries 的前端派生逻辑、Turn 构建逻辑和导航索引。
- 需要新增/更新前端静态测试和 DOM 行为测试，覆盖 Conversation 边界、multi-block 拆分、单 Turn 单执行片段和稳定锚点。
- 不修改 Python 后端、不修改 `POST /api/task-segments`、不引入外部依赖。
