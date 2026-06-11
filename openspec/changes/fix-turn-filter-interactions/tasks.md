## 1. OpenSpec 与行为确认

- [x] 1.1 明确 type filter 是 Turn 内 event 内容筛选，不是 Turn 结构筛选。
- [x] 1.2 确认全部类型取消时 Turn card 保留、Turn detail 显示空态提示。

## 2. 前端修复

- [x] 2.1 新增 Turn entries helper，统一返回 all entries、visible entries、hidden count、visible tool count、visible error count。
- [x] 2.2 修改 `renderTurnList()`，让 Turn card 使用筛选后的可见计数，并显示隐藏事件数量。
- [x] 2.3 修改 `buildTurnDetailHtml()`，用户消息、助手回复、工具调用和错误均基于 visible entries 渲染。
- [x] 2.4 当 visible entries 为空时，Turn detail 显示明确空态提示，不展示未筛选内容。
- [x] 2.5 保留折叠 Raw JSON 的完整 entries，用于调试。

## 3. 测试与验证

- [x] 3.1 更新静态测试，断言 Turn detail 使用 `visibleTurnEntries` 渲染主体内容。
- [x] 3.2 新增 DOM 测试：只保留 `user` 后助手内容隐藏。
- [x] 3.3 新增 DOM 测试：取消所有类型后 Turn card 仍存在且 detail 显示全部隐藏提示。
- [x] 3.4 运行 `node tests/test_task_segmentation_dom.js`。
- [x] 3.5 运行相关 Python 前端静态测试。
- [x] 3.6 运行 `openspec validate fix-turn-filter-interactions --strict`。
