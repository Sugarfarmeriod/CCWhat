## 1. Task 卡片选择

- [x] 1.1 将 task card 渲染从 inline `onclick` 改为 `data-task-id` 和事件绑定
- [x] 1.2 修改 `selectTaskSegment(taskId, sessionId)`，由 `selectedTaskSegmentId` 驱动整块 Task Segment 面板重渲染
- [x] 1.3 移除依赖 `querySelector([onclick*=...])` 的 selected class 手动查询逻辑
- [x] 1.4 增加无效 task id 的保护逻辑，确保不会清空当前 task detail 或抛出脚本错误

## 2. Final Claim 和错误展示

- [x] 2.1 将 `finalClaim` 展示标签改为“Agent 最终声明”，并补充“这是 Agent 自述，不代表任务成功”的提示
- [x] 2.2 实现 final claim 摘要展示和折叠全文展示，全文必须 HTML 转义
- [x] 2.3 实现错误摘要 helper，默认提取短摘要并限制单条展示长度
- [x] 2.4 将 `errors` 渲染改为摘要列表 + 折叠原文，长错误原文默认不展开
- [x] 2.5 确保空 final claim 和空 errors 显示为空状态，不出现 undefined/null

## 3. 稳定 Turn 索引

- [x] 3.1 调整 turn 构建流程，使 `_turnKey` 和 `_turnRootIdx` 基于完整 group entries 标记
- [x] 3.2 确保 type filter 和搜索 filter 只影响渲染可见性，不改变 entry 的 turn 归属
- [x] 3.3 为主会话和 subagent entries 都保留稳定 `_gid`、`_idx`、`_turnKey`、`_turnRootIdx`
- [x] 3.4 增加 helper 判断目标 entry 当前是否被 filter 隐藏

## 4. 左侧导航定位

- [x] 4.1 新增 `focusEntryInNav(idx, options)` helper，负责展开 group、展开 turn、重渲染左侧列表、滚动和高亮
- [x] 4.2 修改 `navigateToEventId(eventId)`，定位到左侧导航而不是默认替换右侧 task detail
- [x] 4.3 为目标 entry 和目标 turn header 增加可定位的 DOM dataset，便于 `scrollIntoView`
- [x] 4.4 当目标 entry 被当前 filter 隐藏时，滚动到 turn header 并在 task detail 中显示筛选隐藏提示
- [x] 4.5 当 event id 无法映射时，保持当前 task detail 不变并显示 disabled 或不可定位提示

## 5. 回归测试

- [x] 5.1 更新 `tests/test_task_segmentation_frontend.py`，断言 task cards 使用 `data-task-id` 且不依赖 inline onclick 查询
- [x] 5.2 增加 task 点击切换重渲染相关静态断言
- [x] 5.3 增加 final claim 摘要/折叠和错误摘要/折叠的静态断言
- [x] 5.4 增加稳定 turn index、`focusEntryInNav`、`scrollIntoView`、filter-hidden 提示的静态断言
- [x] 5.5 运行前端静态测试、task segmentation 相关测试和现有 viewer/current-session analysis 测试
- [x] 5.6 抽取 `viewer/claude-log.html` 内脚本执行 `node --check`
- [x] 5.7 运行 `openspec validate improve-task-segmentation-navigation --strict`

## 6. 手动验收

- [x] 6.1 启动本地 viewer server，打开一个包含多个 Task Segment 的真实 session
- [x] 6.2 验证点击 task-001 之外的 task card 后，选中态和 task detail 均切换到对应 task
- [x] 6.3 验证 final claim 默认显示摘要，全文可展开，且文案不暗示任务成功
- [x] 6.4 验证 errors 默认显示短摘要，长日志折叠，不撑开页面
- [x] 6.5 验证“定位开始事件/定位结束事件”会展开左侧 group/turn、滚动到目标 entry 或 turn header，并保持 task detail 可见
- [x] 6.6 在启用 type filter/search filter 的情况下验证目标被隐藏时的提示行为
