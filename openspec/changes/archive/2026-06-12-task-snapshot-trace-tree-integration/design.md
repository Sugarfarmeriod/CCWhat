## Context

已归档的前两个 change 建立了以下基础：

```text
Trace
  会话
    Turn
```

当前缺口是：

1. Task 切分结果仍没有成为主 Trace 树的一部分。
2. Tools / Skills 缺少固定全局入口。
3. 用户从 Task 回看原始执行过程时，仍需要在独立 Task 页面和 Session Trace 页面之间切换。

本 change 的目标结构是：

```text
Trace
  Tools / Skills Snapshot
  Task 1
    会话 1
      Turn 1
      Turn 2
  Task 2
    会话 1
      Turn 1
```

如果用户还没有确认 Task 切分，则显示：

```text
Trace
  Tools / Skills Snapshot
  会话 1
    Turn 1
  会话 2
    Turn 1
```

## Goals / Non-Goals

**Goals:**

- 在 Trace 树顶部固定展示 `Tools / Skills Snapshot`。
- 用户确认 Task 切分后，将 Task 作为会话上层分组注入 Trace 树。
- Task 节点、会话节点和 Turn 节点共用一套选中、展开、滚动和高亮机制。
- 点击 Snapshot / Task / 会话 / Turn 时，右侧展示对应层级详情。
- 保持 `Tasks` 页面作为切分预览、确认和调试入口。

**Non-Goals:**

- 不改变 task segmentation 算法。
- 不做 Task 成功率、失败诊断、复杂 evidence 面板。
- 不做 Task 边界人工拖拽编辑。
- 不做 Tools / Skills 变化 diff 的完整检测。
- 不重构后端 API。

## Decisions

### Decision 1：Snapshot 是 Trace 全局节点

`Tools / Skills Snapshot` 永远是 Trace 树最顶部节点：

```text
Trace
  Tools / Skills Snapshot
```

它不属于 Task，不属于会话，也不应该在每个 Task 下重复出现。

如果中途 Tools / Skills 变化，本 change 只保留可插入特殊 Turn 的扩展点；完整变化检测留给后续 change。

### Decision 2：Task 注入需要显式确认

自动切分完成后，不应立即重排主 Trace 树。推荐流程：

1. 用户点击“切分 Task”。
2. `Tasks` 页面展示切分结果预览。
3. 用户点击“确认切分”。
4. `Session` 页面的 Trace 树进入 Task-first 结构。

如果用户重新切分，确认状态应失效，直到用户再次确认。

### Decision 3：Task 与会话/Turn 的映射基于现有导航索引

Task 注入不重新切分原始 entries。实现上应使用现有：

- `task.startEventId`
- `task.endEventId`
- event/uuid/file anchor lookup
- Conversation/minimal Turn lookup

将 Task 范围映射到覆盖的会话和 Turn。

如果一个会话被多个 Task 范围覆盖，第一版可以允许同一个会话在多个 Task 下出现，但每个 Task 只展示自己范围内覆盖的 Turn；同时在 Task detail 中标记该会话为跨 Task 会话。不要为了 UI 简洁而破坏原始导航索引。

### Decision 4：Task node 是浏览分组，不是评测结论

Task 节点只展示基础信息：

- Task label，例如 `Task 1`
- title / user intent
- task type
- status / confidence，如果已有
- 覆盖的会话数量和 Turn 数量
- boundary reason 简短摘要

不在本 change 中做新的 status 判断，也不重新计算成功率。

### Decision 5：右侧详情保持分层但克制

点击不同节点的右侧详情：

- Snapshot：Tools 列表、Skills 列表、来源和更新时间/锚点。
- Task：Task 基础摘要、范围、会话列表、边界理由、跳转入口。
- 会话：复用 Change 2 的会话详情。
- Turn：复用 Change 2 的 `Agent 响应 + 原始 JSON` 极简详情。

不要在 Task detail 中提前引入复杂 diagnostics、diff、test 或 req/resp。

### Decision 6：保留 Tasks 页面

`Tasks` 页面仍然存在，职责变为：

- 触发切分。
- 展示切分预览。
- 让用户确认切分。
- 调试边界和原始 task segment JSON。

确认后，主浏览回到 `Session` 页面的 Trace 树。

## Data Model Sketch

建议前端派生节点时使用显式 node type：

```js
{
  nodeType: "snapshot" | "task" | "conversation" | "turn",
  key: "...",
  label: "...",
  groupId: "main",
  taskId: "task-001",
  conversationKey: "...",
  turnKey: "...",
  summary: "..."
}
```

建议新增状态：

```js
let taskTraceConfirmedBySession = {};
let selectedTraceNodeType = null; // "snapshot" | "task" | "conversation" | "turn"
let expandedTaskKeys = new Set();
```

具体实现可以沿用现有对象/集合风格，不强制引入新框架。

## Edge Cases

- 无 task segments：仍显示 Snapshot + 会话/Turn。
- task segments 已生成但未确认：仍显示 Snapshot + 会话/Turn，Tasks 页面显示预览。
- task segments 确认后：显示 Snapshot + Task/会话/Turn。
- 重新切分中：保持旧树或显示 loading，但不要部分更新导致树不一致。
- 重新切分完成但未确认：Trace 树回到未确认状态或继续显示上一次已确认结果，需要有明确提示；第一版建议重新切分后取消确认。
- Task 起止锚点无法映射：Task 节点仍可显示，但右侧明确提示有无法定位范围。

## Migration Plan

1. 在现有 Trace tree builder 前插入 Snapshot node。
2. 新增 Snapshot 数据提取和详情渲染。
3. 新增 task-confirmed 状态和“确认切分”交互。
4. 新增 Task-to-Conversation/Turn mapping helper。
5. Trace tree builder 根据确认状态选择：
   - 未确认：Snapshot + 会话/Turn
   - 已确认：Snapshot + Task/会话/Turn
6. 扩展 select/render detail 逻辑支持 snapshot/task。
7. 更新定位、筛选和测试。
