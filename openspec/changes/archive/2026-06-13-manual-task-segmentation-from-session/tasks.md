## 1. 入口与模式状态

- [x] 1.1 梳理现有 Tasks 页面自动切分入口、Session 页面手动创建 Task Trace Overlay 的相关函数。
- [x] 1.2 在 Tasks 页面明确展示“自动切分”和“手动切分”两个入口。
- [x] 1.3 新增或复用手动切分模式状态，例如 `manualTaskSegmentationMode`、起始会话、结束会话、候选范围。
- [x] 1.4 点击“手动切分”后自动跳转 Session 页面，并进入原始会话切分模式。
- [x] 1.5 手动切分工具条提供“创建 Task”“撤销上一次”“确认执行这次 Task 划分”“取消”。

## 2. Session 原始会话上手动选择范围

- [x] 2.1 手动切分模式下优先展示原始会话树，避免已有 Task-first overlay 干扰用户选择。
- [x] 2.2 支持点击会话设置起始会话和结束会话。
- [x] 2.3 高亮当前候选会话范围。
- [x] 2.4 已创建 Task 的会话范围持续高亮，并显示对应 Task 编号。
- [x] 2.5 支持选择顺序自动纠正或给出提示；第一版建议自动按会话顺序归一化。

## 3. 创建和完成 Task

- [x] 3.1 实现“创建 Task”：把当前会话范围追加到 active Task Trace Overlay。
- [x] 3.2 默认标题使用 `任务 N`，默认类型使用 `manual`。
- [x] 3.3 创建后清空当前起止选择，允许连续创建多个 Task。
- [x] 3.4 阻止创建与已有 Task 重叠的会话范围，并显示提示。
- [x] 3.5 实现“撤销上一次”：删除最近一次手动创建的 Task，并移除对应持续高亮。
- [x] 3.6 实现“确认执行这次 Task 划分”：退出手动切分模式，清理临时高亮，并切回 Task-first 展示。
- [x] 3.7 实现“取消手动切分”：存在未保存 overlay 时给出确认提示。

## 4. Overlay 与展示一致性

- [x] 4.1 复用 `startConversationKey/endConversationKey` 作为手动 Task 主边界。
- [x] 4.2 保留派生 `startTurnKey/endTurnKey/startEventId/endEventId` 用于定位和导出。
- [x] 4.3 保证手动切分不会拆分会话内部 Turn/Step。
- [x] 4.4 未分配会话继续显示在 Unassigned 区域。
- [x] 4.5 确认执行前，手动切分模式中的持续高亮只作为标注工作区反馈；确认后由正式 Task-first 树表达结果。

## 5. 最小测试与验证

- [x] 5.1 更新静态测试：手动切分入口和关键函数存在。
- [x] 5.2 更新 DOM 冒烟测试：从 Tasks 点击手动切分后进入 Session 手动切分模式。
- [x] 5.3 更新 DOM 冒烟测试：选择两个会话后可以创建一个 manual Task Overlay。
- [x] 5.4 更新 DOM 冒烟测试：撤销上一次会移除最近创建的 manual Task。
- [x] 5.5 运行 `openspec validate manual-task-segmentation-from-session --strict`。
- [x] 5.6 运行最小相关前端测试；全量测试视改动范围决定。
- [x] 5.7 手动验收：真实 session 中连续创建多个 Task、持续高亮、撤销上一次、确认执行、Task-first 展示、Unassigned 展示。
