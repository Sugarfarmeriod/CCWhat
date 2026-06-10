## Why

当前 Task Segment 面板已经能展示多个任务，但实际使用时存在交互断点：点击 task card 不能可靠切换详情，起止事件定位只替换右侧详情而不能帮助用户在左侧 turn 导航中对照原始上下文。同时 `finalClaim` 和 `errors` 直接展示原始长文本，信息密度低，影响人工校准切分质量。

## What Changes

- 修复 task card 选择交互，使用户点击任意任务后能稳定切换选中态和详情内容。
- 将 task card 的选择状态改为由 `selectedTaskSegmentId` 驱动，避免依赖 fragile inline handler 或 DOM 字符串查询。
- 重构 Task Segment 的起止事件定位交互：点击“定位开始事件/定位结束事件”时，左侧导航 SHALL 展开对应 group/turn、滚动到目标 entry，并高亮目标位置。
- 明确左侧 turn tree 应基于完整 session entries 构建，不能因当前类型筛选而改变 turn 边界。
- 改善 `finalClaim` 展示：作为“Agent 最终声明”展示摘要，并提供折叠全文，明确它是 agent 自述而非成功证据。
- 改善 `errors` 展示：默认显示短摘要和数量，长错误原文折叠展示，避免 task detail 被长日志淹没。
- 不修改 Task Segment 切分算法、后端 API 字段含义或 success/failed 评测逻辑。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `session-viewer`: 改进 Claude Log 页面中 Task Segment 面板的任务切换、证据摘要、错误展示和事件定位到左侧 turn 的交互行为。

## Impact

- 影响代码：`viewer/claude-log.html` 的 task card 渲染、任务详情渲染、左侧 turn/entry 导航定位 helper 和相关 CSS。
- 影响测试：补充前端静态回归测试，覆盖 task card 使用 `data-task-id`、点击切换重渲染、final claim 摘要/折叠、errors 摘要/折叠、定位时展开并滚动左侧导航。
- 行为边界：复用现有 `POST /api/task-segments` 响应；不新增后端接口；不改变分析报告、导出、原始日志详情和 request/response viewer 行为。
