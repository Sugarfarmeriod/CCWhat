## 1. Turn 数据层和导航索引

- [x] 1.1 梳理 `viewer/claude-log.html` 当前 session entries、group、filter、page state 和 task segment state 的数据流。
- [x] 1.2 新增 Turn 派生 helper，基于完整 group entries 生成稳定 `Turn 1 / Turn 2 / Turn N` 列表。
- [x] 1.3 为主会话和 subagent group 分别生成独立 Turn key、Turn label、entry range、用户摘要、助手摘要、工具数量和错误数量。
- [x] 1.4 新增统一导航索引，支持通过 event id、uuid、`<groupId>:<fileLine>` 和 turnKey 定位到 `{groupId, turnKey, turnIndex, entryIndex}`。
- [x] 1.5 确保搜索筛选和类型筛选不会重新生成 Turn 编号或破坏导航索引。

## 2. Session 页面 Turn-first 展示

- [x] 2.1 将 `Session` 页面主列表改为 Turn List，默认显示 Turn label、消息摘要、entry 数、工具数、错误数和关联 Task badge。
- [x] 2.2 实现 Turn 选择状态，点击 Turn 后仅选中当前 Turn，并在详情区展示 Turn overview。
- [x] 2.3 在 Turn detail 中展示用户文本、助手文本、工具调用/结果摘要、错误摘要和折叠 Raw JSON。
- [x] 2.4 保留 Raw Events 调试入口，确保原始 entries 仍可从专门入口或折叠区查看。
- [x] 2.5 为定位命中的 Turn 和 entry 增加临时高亮、滚动和可见提示。

## 3. Tasks 页面与 Turn 联动

- [x] 3.1 在 task segment 结果渲染前，将 task 的 `startEventId` / `endEventId` 映射为 startTurn/endTurn。
- [x] 3.2 Task detail 的起止位置默认展示为 `Turn N`，将原始 event id 移入折叠调试区或 Raw 区。
- [x] 3.3 将”定位开始事件/定位结束事件”改为”定位开始 Turn/定位结束 Turn”，并接入统一导航索引。
- [x] 3.4 点击定位按钮时切换到 `Session` 页面，展开目标 group，选中并滚动到目标 Turn，必要时高亮具体 entry。
- [x] 3.5 处理不可定位和被筛选隐藏的情况，显示明确提示且不抛脚本错误。
- [x] 3.6 在 Session Turn card 上展示关联 Task badge，并支持点击 badge 切换到 `Tasks` 页面选中对应 Task。
- [x] 3.7 在 Task detail 的 `Turns` 区块展示该 Task 覆盖的 Turn 列表和摘要。

## 4. 测试与验证

- [x] 4.1 更新前端静态回归测试，断言 Turn helper、导航索引、Turn label、Task 起止 Turn 展示和定位函数存在。
- [x] 4.2 更新 DOM 行为测试，覆盖点击 Turn、点击 Task badge、Task 定位开始/结束 Turn、不可定位提示。
- [x] 4.3 验证 `python3 -m pytest -q` 全量测试通过。
- [x] 4.4 验证 `node tests/test_task_segmentation_dom.js` 或等价 DOM 测试通过。
- [ ] 4.5 用真实 session 手动验收：Session 默认 Turn-first，Tasks 起止显示 Turn，定位按钮能跳转并高亮对应 Turn。
- [x] 4.6 运行 `openspec validate turn-first-session-navigation --strict` 并修复所有规格问题。
