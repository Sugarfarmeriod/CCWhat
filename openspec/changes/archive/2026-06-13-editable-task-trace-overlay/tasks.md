## 1. 上下文梳理

- [x] 1.1 梳理当前 Task Trace confirmed state、Trace tree builder、Task detail、Turn selection 和 export 相关函数。
- [x] 1.2 确认 Turn 稳定锚点字段：turnKey、conversationKey、groupId、source entry、event id、file anchor、block anchor。
- [x] 1.3 确认当前 Task Segment 到 Trace node 的映射 helper，可复用为 overlay 到 Trace node 的映射。
- [x] 1.4 明确本 change 不修改 Raw Trace、Conversation/Turn 派生、task segmentation 算法和后端 API。

## 2. Task Trace Overlay 数据层

- [x] 2.1 新增 overlay 数据结构和状态，例如 `taskTraceOverlaysBySession`、`activeTaskTraceOverlayBySession`、`savedTaskTraceOverlayBySession`。
- [x] 2.2 自动切分确认时，将 Task Segment result 转换为 `source=auto` overlay。
- [x] 2.3 Trace tree builder 改为消费 active overlay，而不是直接消费 raw task segment result。
- [x] 2.4 overlay task 使用 startConversationKey/endConversationKey 作为主要范围，保留 startTurnKey/endTurnKey/startEventId/endEventId 作为派生导出锚点。
- [x] 2.5 overlay 修改后标记 `source=edited` 和 `dirty=true`。
- [x] 2.6 保证 Task 编辑边界只能落在会话之间，不能把单个会话内部 Turn/Step 拆到不同 Task。

## 3. 编辑模式 UI

- [x] 3.1 新增“编辑 Task Trace”入口，仅在当前 session 存在 active overlay 时启用。
- [x] 3.2 新增编辑模式状态，例如 `taskTraceEditMode`、`selectedEditableTaskId`、`selectedEditableConversationKey`。
- [x] 3.3 编辑模式下显示“保存编辑”“撤销编辑”“退出编辑”入口和 dirty 状态提示。
- [x] 3.4 切换 session、重新切分或退出编辑模式时处理未保存修改提示。
- [x] 3.5 编辑模式下选中 Task / Conversation 时，在右侧 detail 或 action bar 展示可用操作；选中 Turn 时回退到所属 Conversation。

## 4. 边界调整和会话移动

- [x] 4.1 实现“设为 Task 起始会话”，更新当前 Task 的 startConversationKey 并刷新 Trace 树。
- [x] 4.2 实现“设为 Task 结束会话”，更新当前 Task 的 endConversationKey 并刷新 Trace 树。
- [x] 4.3 实现边界合法性校验：起始会话不能晚于结束会话，范围不能为空，第一版不支持非法跨 group 范围。
- [x] 4.4 实现“移到上一个 Task”，用于把当前 Task 首部边界会话整体移给上一个 Task。
- [x] 4.5 实现“移到下一个 Task”，用于把当前 Task 尾部边界会话整体移给下一个 Task。
- [x] 4.6 不可移动时禁用按钮或显示明确提示。

## 5. 拆分、合并、删除和元数据编辑

- [x] 5.1 实现“从当前会话拆分 Task”，将一个 Task 拆成两个连续 Task。
- [x] 5.2 实现“合并下一个 Task”，合并相邻 Task 并保留合理标题/type。
- [x] 5.3 实现“删除 Task”，并明确处理其覆盖会话：进入 unassigned 或由相邻 Task 接管。
- [x] 5.4 实现 Task 标题编辑。
- [x] 5.5 实现 Task 类型编辑，类型选项沿用现有 task type 集合。
- [x] 5.6 每个编辑操作都记录 minimal edit history 或 updatedAt，便于调试和导出。

## 6. 手动创建 Task

- [x] 6.1 新增“手动创建 Task”入口，在有无自动切分结果时都可用。
- [x] 6.2 新增手动创建模式状态：选择 startConversation、选择 endConversation、填写 title/type。
- [x] 6.3 在 Trace 树会话节点上支持选择起点和终点；选中 Turn 时回退到所属会话。
- [x] 6.4 创建有效 Task 后生成或更新 active overlay，source 为 `manual` 或 `edited`。
- [x] 6.5 手动创建后 Trace 树刷新为 Task-first 结构。
- [x] 6.6 对无效范围、空标题和跨越不支持范围展示明确提示。

## 7. 保存、撤销和导出

- [x] 7.1 实现“保存编辑”：将 active overlay 标记为 saved，更新 revision/updatedAt，并写入 saved overlay 状态。
- [x] 7.2 实现“撤销编辑”：恢复到最近一次 saved overlay。
- [x] 7.3 实现“导出 Task Trace Overlay”入口。
- [x] 7.4 导出 JSON 包含 sessionId、overlayId、source、revision、createdAt、updatedAt、tasks、start/end Conversation、start/end Turn 和 start/end event anchor。
- [x] 7.5 导出 JSON 不包含完整 Raw Trace，但保留足够锚点供后续 Dataset Builder 复现。

## 8. Trace 树和状态一致性

- [x] 8.1 Trace 树始终使用 active overlay 渲染 Task-first 结构。
- [x] 8.2 无 active overlay 时显示 `Snapshot -> 会话 -> Turn`。
- [x] 8.3 编辑后 Task 节点、会话节点和 Turn 节点立即反映新的 overlay 范围。
- [x] 8.4 保持 Turn label、会话 label 稳定，不因 overlay 编辑重新编号原始 Turn。
- [x] 8.5 保证 unassigned 会话有明确展示，不被静默隐藏。

## 9. 测试与验证

- [x] 9.1 更新前端静态测试，断言 overlay state、edit mode、manual create、save/undo/export 函数存在。
- [x] 9.2 更新 DOM 测试：确认自动切分后生成 auto overlay，Trace 树消费 overlay。
- [x] 9.3 更新 DOM 测试：设为 Task 起始/结束会话后树结构刷新且 dirty=true。
- [x] 9.4 更新 DOM 测试：会话移到相邻 Task 后两个 Task 边界正确变化，且会话内部 Turn 不被拆分。
- [x] 9.5 更新 DOM 测试：从会话拆分 Task、合并下一个 Task、删除 Task。
- [x] 9.6 更新 DOM 测试：手动创建 Task，不依赖自动切分结果。
- [x] 9.7 更新 DOM 测试：保存编辑、撤销编辑和 dirty 提示。
- [x] 9.8 更新 DOM 测试：导出 overlay JSON 不包含完整 Raw Trace，但包含必要锚点。
- [x] 9.9 运行 `openspec validate editable-task-trace-overlay --strict` 并修复所有规格问题。
- [x] 9.10 运行前端 DOM 测试和项目全量测试，并记录结果。
- [x] 9.11 用真实 session 手动验收：自动切分后校正、纯手动创建、保存、撤销、导出都符合预期。
