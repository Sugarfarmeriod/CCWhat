## Why

当前 Task Trace 已经支持自动切分并注入 Trace 树，但纯规则算法不可能总是准确。真实使用中，用户会发现某些会话应该属于相邻 Task，或者算法漏切、误切。

如果平台只允许“接受/不接受算法结果”，它仍然只是一个自动分析工具；如果允许用户校正和手动划分 Task，它就开始具备数据标注能力，能为后续 Dataset Builder、Offline Eval 和失败诊断沉淀更可靠的人工确认 Task Trace。

本 change 引入 `Task Trace Overlay`：原始 Trace 不变，自动切分结果和人工编辑结果作为覆盖层存在。用户可以基于自动切分结果调整，也可以从零手动创建 Task。

## What Changes

- 引入前端 Task Trace Overlay 状态，用于表示当前 session 的 active Task 划分。
- 自动切分结果确认后先生成 `auto overlay`。
- 用户可以进入编辑模式，对 overlay 做人工校正：
  - 调整 Task 起始会话 / 结束会话。
  - 将完整会话移到上一个或下一个 Task。
  - 从某个会话拆分新 Task。
  - 合并相邻 Task。
  - 删除 Task。
  - 修改 Task 标题和类型。
- 用户可以不运行自动切分，直接手动创建 Task：
  - 选择起始会话。
  - 选择结束会话。
  - 输入标题和类型。
  - 保存为 manual overlay。
- Trace 树展示当前 active overlay，而不是只展示算法原始结果。
- 提供撤销未保存编辑、保存编辑、导出 overlay JSON 的基础能力。

## Non-Goals

- 不实现拖拽排序或拖拽调整边界。
- 不实现后端数据库持久化。
- 不实现多人协作、冲突合并或审核流。
- 不重新设计 task segmentation 算法。
- 不实现复杂评测状态编辑。
- 不改变原始 Trace、Conversation 或 Turn 派生数据。
- 不支持把单个会话内部的 Step/Turn 拆到不同 Task；Step/Turn 只作为详情展示和导出锚点。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 支持在 Session Trace 树中编辑和手动创建 Task Trace Overlay，并将 overlay 作为当前 Task-first 树结构来源。

## Impact

- 主要影响 `viewer/claude-log.html` 的 Task state、Trace tree builder、Task detail、Turn action、Tasks 页面确认流程和导出逻辑。
- 需要新增前端静态测试和 DOM 行为测试，覆盖 overlay 创建、编辑、保存、撤销、导出和 Trace 树刷新。
- 第一版可使用前端内存态；若已有本地导出机制，可以扩展导出 JSON，但不要求后端持久化。
