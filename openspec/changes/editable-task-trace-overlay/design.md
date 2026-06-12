## Context

当前 Task Trace 的数据流大致是：

```text
Raw Trace
  -> Conversation / Turn
  -> Auto Task Segmentation
  -> Confirmed Task Trace
  -> Trace Tree: Task -> 会话 -> Turn
```

本 change 将 confirmed Task Trace 抽象成可编辑的 overlay：

```text
Raw Trace
  -> Conversation / Turn
  -> Task Trace Overlay
     - source: auto | manual | edited
     - tasks: [...]
  -> Trace Tree
```

原始 Trace 和 Conversation/Turn 数据不可变；用户编辑只修改 overlay。Task 的最小编辑单元是 Conversation（会话），Step/Turn 只作为会话内部详情展示。

## Goals / Non-Goals

**Goals:**

- 自动切分结果可人工校正。
- 用户可从零手动创建 Task。
- Trace 树始终展示当前 active overlay。
- 编辑操作可保存、撤销和导出。
- 第一版使用明确按钮和选择模式，不做拖拽。

**Non-Goals:**

- 不做数据库持久化。
- 不做拖拽交互。
- 不做复杂 Task outcome 编辑。
- 不做多人协作。
- 不修改 task segmentation 算法。

## Concepts

### Task Trace Overlay

Overlay 是对原始 Trace 的任务划分覆盖层。

建议结构：

```js
{
  overlayId: "overlay-...",
  sessionId: "...",
  source: "auto" | "manual" | "edited",
  baseTaskSegmentRunId: "...",
  revision: 1,
  saved: false,
  tasks: [
    {
      taskId: "task-001",
      title: "修复导出错误",
      taskType: "bugfix",
      startConversationKey: "...",
      endConversationKey: "...",
      startTurnKey: "...", // derived export anchor
      endTurnKey: "...",   // derived export anchor
      startEventId: "...",
      endEventId: "...",
      source: "auto" | "manual" | "edited",
      editHistory: []
    }
  ]
}
```

第一版必须以 `startConversationKey/endConversationKey` 作为可编辑主范围，并从会话首尾 Turn 反推 `startTurnKey/endTurnKey` 与 event anchor；导出时应同时包含会话范围和可复现锚点。

### Edit Mode

Task Trace 默认是浏览模式。用户点击“编辑 Task Trace”进入编辑模式。

编辑模式下允许：

- 选中 Task。
- 选中 Conversation。
- 对选中 Task 或 Conversation 执行边界操作。
- 保存或撤销本轮编辑。

### Manual Create Mode

用户点击“手动创建 Task”后进入选择模式：

1. 选择起始会话。
2. 选择结束会话。
3. 输入标题和类型。
4. 创建 Task。

创建后进入 edited/manual overlay，Trace 树刷新为 Task-first。

## Decisions

### Decision 1：Overlay 不改 Raw Trace

所有编辑都作用在 overlay 上。Conversation、Turn、Raw JSON 和 event anchors 不被修改。

### Decision 2：第一版用按钮，不做拖拽

提供明确操作：

- `设为 Task 起始会话`
- `设为 Task 结束会话`
- `移到上一个 Task`
- `移到下一个 Task`
- `从当前会话拆分 Task`
- `合并下一个 Task`
- `删除 Task`
- `修改标题/类型`

按钮比拖拽更适合第一版验收，且更容易写测试。

### Decision 3：编辑后立即刷新树，但需要保存

编辑操作可以实时更新 preview tree，但 overlay 标记为 unsaved。

用户可以：

- 保存编辑：overlay 变为 active saved overlay。
- 撤销编辑：回到上一个 saved overlay。

第一版的“保存”可以是前端内存态保存，不要求后端持久化。

### Decision 4：Task 范围以连续会话范围为主

第一版 Task 范围用 start/end Conversation 表示，覆盖其间连续会话。一个会话内部的所有 Step/Turn 必须整体属于同一个 Task。

不支持一个 Task 包含多个不连续 Conversation range。若用户需要复杂场景，后续再扩展为 multi-range task。

### Decision 5：手动划分和自动切分共用 overlay

自动切分确认后创建 `source=auto` overlay。

用户编辑后 source 变为 `edited`。

用户完全手动创建时 source 为 `manual`。

Trace tree builder 不需要关心来源，只消费 active overlay。

## UX Sketch

### 自动切分后校正

```text
Tasks 页面
  [任务切分]
  [确认切分]

Session 页面
  [编辑 Task Trace]

选中 Turn
  仅展示 Turn 详情，不作为 Task 编辑边界

选中会话
  [移到上一个 Task]
  [移到下一个 Task]
  [从当前会话拆分 Task]
  [设为当前 Task 起始会话]
  [设为当前 Task 结束会话]

选中 Task
  [修改标题/类型]
  [合并下一个 Task]
  [删除 Task]

顶部编辑栏
  [保存编辑]
  [撤销编辑]
```

### 纯手动创建

```text
Session 页面
  [手动创建 Task]
    选择起始会话
    选择结束会话
    输入标题/类型
    [创建]
```

## Edge Cases

- 没有自动切分结果：允许手动创建 Task。
- 只有一个 Task：移动到上/下一个 Task 的按钮 disabled。
- 选择的结束会话早于起始会话：自动交换或提示错误；第一版建议提示错误。
- Task 删除后剩余会话未分配：显示在 `Unassigned` 或恢复到会话层提示。
- 任务范围重叠：第一版应避免生成重叠范围；操作会调整相邻 Task 边界。
- 会话内部 Turn 不允许被拆分到不同 Task；如果用户选中 Turn，操作应回退到该 Turn 所属会话。
- 保存前切换 session：提示存在未保存编辑，第一版可以自动撤销并提示。

## Export

导出 overlay JSON 至少包含：

- sessionId
- overlayId
- source
- revision
- createdAt / updatedAt
- tasks
- 每个 task 的 title、type、startConversationKey、endConversationKey、startTurnKey、endTurnKey、startEventId、endEventId

后续 Dataset Builder 可以消费这个 overlay。
