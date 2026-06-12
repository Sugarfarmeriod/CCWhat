## Context

已有 Task Trace Overlay 已经支持会话级边界：

```text
Task Trace Overlay
  task.startConversationKey
  task.endConversationKey
  derived startTurnKey / endTurnKey
  derived startEventId / endEventId
```

本 change 不新增新的数据模型，重点是把“用户从零定义 Task”的交互串起来。

## Interaction Flow

### 1. Tasks 页面入口

Tasks 页面显示两个主要操作：

```text
[自动切分] [手动切分]
```

- 自动切分：沿用现有 `/api/task-segments` 流程。
- 手动切分：不调用后端算法，直接进入 Session 页面手动切分模式。

### 2. 进入 Session 手动切分模式

点击“手动切分”后：

1. 自动跳转到 Session 页面。
2. Session Trace 使用原始会话视图，而不是已有 Task-first 视图。
3. 顶部或侧边显示手动切分状态条：
   - 当前模式：手动切分
   - 当前选择：起始会话 / 结束会话
   - 已创建 Task 数量
   - 操作按钮：创建 Task、撤销上一次、确认执行这次 Task 划分、取消

### 3. 创建 Task 并持续标注

用户操作：

1. 点击一个会话作为起始会话。
2. 点击另一个会话作为结束会话。
3. 系统默认生成标题：`任务 1`、`任务 2`。
4. 用户点击“创建 Task”。
5. 系统把该连续会话范围写入 active Task Trace Overlay。
6. 该范围在原始会话树中持续高亮，并显示 `Task 1` 标记。
7. 用户继续选择下一段会话创建下一个 Task。

持续高亮是手动切分模式的核心反馈：

- 当前候选范围使用临时高亮。
- 已创建 Task 范围使用稳定高亮。
- 不同 Task 应至少通过编号区分；如果实现成本可控，可以使用不同色带。
- 已创建 Task 范围在用户继续选择下一段时仍然保留。

第一版标题和类型可以简化：

- title 默认 `任务 N`。
- taskType 默认 `manual` 或 `unknown`。
- 后续仍可复用已有 Task metadata 编辑能力。

### 4. 撤销上一次

用户点击“撤销上一次”后：

- 删除最近一次手动创建的 Task。
- 移除该 Task 对应的持续高亮。
- 恢复这些会话为未分配状态。
- 保持手动切分模式，允许用户重新选择范围。

第一版只要求撤销最近一次创建，不要求任意历史步骤跳转。

### 5. 确认执行手动切分

用户点击“确认执行这次 Task 划分”后：

- overlay source 为 `manual` 或 `edited`。
- overlay dirty 状态保持为 true，提示用户可保存或导出。
- 清除手动切分模式中的临时/持续高亮状态。
- Session Trace 切换为 Task-first 结构。
- 未分配会话显示在 `Unassigned` 区域。

## Rules

- Task 范围必须是连续会话范围。
- 一个会话不能同时属于多个 Task。
- 已分配会话在手动切分模式中必须持续高亮，并标明对应 Task。
- 如果用户选择的范围与已有 Task 重叠，第一版应阻止创建并给出提示。
- 选择结束会话早于起始会话时，第一版可以自动交换或提示；建议自动交换以减少摩擦。
- 取消手动切分时，不应静默丢弃已创建但未保存的 overlay；第一版可以提示确认。

## Testing Strategy

只做最小必要测试：

- 静态测试：确认 Tasks 页面存在手动切分入口和相关函数。
- DOM 冒烟：点击手动切分后进入 Session 手动切分模式。
- DOM 冒烟：选择两个会话后能创建一个 manual Task Overlay。
- DOM 冒烟：撤销上一次会移除最近创建的 Task。

复杂交互、真实内容理解、连续多个 Task 的体验，交给手动验收。
