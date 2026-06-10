## Context

`viewer-task-segmentation-panel` 已经把 `/api/task-segments` 的结果展示到 Claude Log viewer，但第一版交互更像静态结果面板。用户实际复盘长 session 时，需要在多个 task 之间快速切换，并把 task 的 `startEventId` / `endEventId` 对应到左侧原始日志 turn，才能判断边界是否合理。

当前主要约束：

- Task Segment 结果仍来自已有 `POST /api/task-segments`，本 change 不改变 API 和切分算法。
- Claude Log viewer 的左侧列表已有 group、turn、entry 三层渲染，但 turn 是渲染时由 entries 临时构建，容易被当前筛选条件影响。
- Task detail 右侧面板既承载 task 详情，也承载原始日志详情；定位事件时如果直接替换右侧内容，会打断用户对 task evidence 的观察。

## Goals / Non-Goals

**Goals:**

- 让 task card 点击切换可靠工作，任意 task 都能成为当前选中任务并展示对应详情。
- 让 `startEventId` / `endEventId` 能定位到左侧导航中的对应 group、turn 和 entry。
- 让左侧 turn 结构基于完整 session entries 保持稳定，不因 type filter 导致 turn 边界变化。
- 让 `finalClaim` 和 `errors` 更适合人工阅读：默认摘要、可展开全文、明确语义。
- 保持现有分析报告、导出、原始日志 detail、request/response viewer 行为不变。

**Non-Goals:**

- 不修改任务切分规则、BM25、文件 overlap 或 evidence 抽取算法。
- 不引入 success/failed 自动评测。
- 不新增后端接口，不持久化 task segment 结果。
- 不重做整个 Claude Log viewer 布局。

## Decisions

### 1. Task 选择由状态重渲染驱动

task card SHALL 使用 `data-task-id` 表示身份，点击事件 SHALL 读取 dataset 后更新 `selectedTaskSegmentId`，再通过 `renderTaskSegments(cached, sessionId)` 重渲染整个 task panel。

理由：

- 选中态只有一个来源：`selectedTaskSegmentId`。
- 避免依赖 inline `onclick` 字符串和 `querySelector([onclick*=...])` 这类脆弱查询。
- 重渲染可以同步更新 card selected class、detail panel、debug boundaries 等派生内容。

备选方案是局部 DOM patch，但局部 patch 容易遗漏 selected class、detail 内容和后续新增字段，第一版不采用。

### 2. 建立稳定 turn index

左侧导航 SHALL 先基于完整 group entries 构建 turn tree，并为每个 entry 写入稳定索引：

- `_turnKey`: group 内 turn 标识，例如 `main:12`
- `_turnRootIdx`: turn root entry 的 `allEntries` index
- `_idx`: entry 的全局 index，沿用现有字段

渲染时可以继续应用 type filter 和搜索 filter，但 filter 不得改变 entry 归属的 turn。定位逻辑应使用预先标记的 `_turnKey`，而不是重新从过滤后的 entries 推断 turn。

### 3. 定位事件聚焦左侧导航，不默认替换 Task 面板

`navigateToEventId(eventId)` SHALL 找到 entry index 后调用新的 `focusEntryInNav(idx, options)` helper：

- 展开目标 group。
- 展开目标 turn。
- 重新渲染左侧列表。
- 滚动到目标 entry；如果目标 entry 不可见，则滚动到 turn header 并给出筛选提示。
- 高亮目标 entry 或 turn header。

默认不调用 `renderDetail(allEntries[idx])` 替换右侧 task detail。这样用户可以保持右侧 task evidence 可见，同时在左侧对照原始 turn。

如果后续需要查看原始日志详情，可以另加“查看原始事件”操作，或允许用户点击左侧高亮 entry。

### 4. 筛选隐藏目标时给出明确反馈

定位目标可能被当前 type filter 或搜索隐藏。第一版采用保守策略：

- 不强行清空用户筛选。
- 如果目标 entry 被隐藏，左侧 SHALL 展开并滚动到其 turn header。
- task detail 中 SHALL 显示短提示，说明目标事件被当前筛选隐藏，并提示用户清除筛选或调整 filter。

这个策略避免定位操作修改用户正在使用的过滤条件。

### 5. Final Claim 作为 Agent 自述展示

`finalClaim` SHALL 改名展示为“Agent 最终声明”。默认只展示短摘要，全文放入折叠区，并显示说明：这是 Agent 自述，不代表任务成功。

理由：`finalClaim` 是弱证据，主要用于和文件修改、命令、测试、错误等 evidence 对照，不能被误解为评测结论。

### 6. Errors 使用摘要优先

`errors` SHALL 默认展示短摘要列表，每条默认截断到有限长度，并提供折叠原文。摘要可以先用纯前端规则生成：

- 取第一条非空行。
- 优先保留包含 `Error`、`failed`、`FAILED`、`Traceback`、`Exception`、`Permission denied` 等关键词的行。
- 单条摘要长度限制在约 160 字符。

第一版不引入 LLM 摘要，也不改变后端 evidence 抽取。

## Risks / Trade-offs

- [Risk] 定位到左侧但不替换右侧 detail，用户可能期待右侧显示原始事件。  
  Mitigation: 文案使用“定位到左侧”语义，并保留用户点击左侧 entry 查看原始详情的自然路径。

- [Risk] 筛选隐藏目标时，用户看不到具体 entry。  
  Mitigation: 展开并滚动到 turn header，同时显示筛选提示；后续可加“一键显示目标事件”。

- [Risk] 稳定 turn index 需要调整现有 build/render 流程。  
  Mitigation: 保持数据结构小范围扩展，只增加 `_turnKey` / `_turnRootIdx` / DOM dataset，不重写列表 UI。

- [Risk] errors 摘要规则可能遗漏关键信息。  
  Mitigation: 默认摘要只用于扫描，原始错误全文仍可展开查看。
