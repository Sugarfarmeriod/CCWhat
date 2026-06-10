## ADDED Requirements

### Requirement: Task Segment 任务卡片选择
Claude Log 页面 SHALL 支持用户点击任意 Task Segment card 后切换当前选中任务，并展示该任务对应的详情内容。

#### Scenario: 点击任务卡片切换详情
- **WHEN** Task Segment 面板已渲染多个 task cards
- **AND** 用户点击非当前选中的 task card
- **THEN** 页面 SHALL 将该 task 标记为唯一选中 task
- **AND** task detail SHALL 展示被点击 task 的 `taskId`、`title`、`taskType`、`startEventId`、`endEventId`、evidence、fileWeights 和 boundaryReasons
- **AND** 之前选中的 task card SHALL 不再显示 selected 状态

#### Scenario: 任务选择状态由数据驱动
- **WHEN** Task Segment 面板重渲染
- **THEN** selected 状态 SHALL 由 `selectedTaskSegmentId` 和 task data 决定
- **AND** SHALL NOT 依赖查询 inline `onclick` 字符串来查找当前 card

#### Scenario: 点击无效任务不会破坏当前视图
- **WHEN** 用户触发的 task id 不存在于当前 session 的缓存结果中
- **THEN** 页面 SHALL 保持当前选中 task 和当前 detail 内容
- **AND** SHALL NOT 抛出脚本错误

### Requirement: Task Segment Final Claim 展示
Claude Log 页面 SHALL 将 Task Segment 的 `finalClaim` 展示为 Agent 最终声明，并明确该内容是 agent 自述而非任务成功证据。

#### Scenario: 展示 final claim 摘要
- **WHEN** 当前 task 包含 `finalClaim`
- **THEN** task detail SHALL 显示“Agent 最终声明”区块
- **AND** 默认 SHALL 展示不超过 160 字符的摘要
- **AND** SHALL 显示该声明不代表任务成功的提示

#### Scenario: 展开 final claim 全文
- **WHEN** `finalClaim` 超过摘要长度
- **THEN** task detail SHALL 提供折叠的全文查看入口
- **AND** 全文内容 SHALL 经过 HTML 转义
- **AND** 展开全文 SHALL NOT 改变当前选中 task

#### Scenario: 无 final claim
- **WHEN** 当前 task 不包含 `finalClaim`
- **THEN** task detail SHALL 显示空状态或不渲染 Agent 最终声明正文
- **AND** SHALL NOT 显示 undefined/null

### Requirement: Task Segment 错误摘要展示
Claude Log 页面 SHALL 将 Task Segment 的 `errors` 默认展示为短摘要，并将长错误原文折叠，以便用户快速扫描负向证据。

#### Scenario: 展示错误摘要
- **WHEN** 当前 task 的 evidence 包含 `errors`
- **THEN** task detail SHALL 显示错误数量
- **AND** 每条错误默认 SHALL 展示短摘要
- **AND** 单条摘要 SHALL 截断到有限长度，避免撑开页面或遮挡其他 evidence

#### Scenario: 展开错误原文
- **WHEN** 某条 error 原文长于摘要
- **THEN** 页面 SHALL 提供折叠原文查看入口
- **AND** 原文 SHALL 经过 HTML 转义
- **AND** 折叠区 SHALL NOT 默认展开

#### Scenario: 无错误
- **WHEN** 当前 task 的 `errors` 为空或不存在
- **THEN** task detail SHALL 显示错误为空状态
- **AND** SHALL NOT 显示 undefined/null

### Requirement: 左侧稳定 Turn 索引
Claude Log 页面 SHALL 基于完整 session entries 构建稳定 turn 索引，使 Task Segment 的事件定位不受当前类型筛选或搜索筛选改变。

#### Scenario: 完整 entries 构建 turn 归属
- **WHEN** session 加载成功
- **THEN** 页面 SHALL 基于完整 group entries 构建 turn tree
- **AND** 每个可定位 entry SHALL 记录其所属 `_turnKey`
- **AND** 每个可定位 entry SHOULD 记录其 turn root index

#### Scenario: 筛选不改变 turn 归属
- **WHEN** 用户启用 type filter 或搜索 filter
- **THEN** entry 的 `_turnKey` SHALL 保持不变
- **AND** 定位事件 SHALL 使用既有 `_turnKey` 展开 turn
- **AND** SHALL NOT 从过滤后的 entries 重新推断目标事件所属 turn

#### Scenario: Subagent turn 归属
- **WHEN** 目标事件来自 subagent
- **THEN** 页面 SHALL 使用该 subagent group 内的 turn index 定位
- **AND** SHALL 展开对应 subagent group

### Requirement: Task Segment 事件定位到左侧导航
Claude Log 页面 SHALL 支持从 Task Segment 的 `startEventId` 和 `endEventId` 定位到左侧导航中的对应 group、turn 和 entry。

#### Scenario: 定位开始事件到左侧导航
- **WHEN** 当前 task 包含可映射的 `startEventId`
- **AND** 用户点击“定位开始事件”
- **THEN** 页面 SHALL 展开目标 entry 所属 group
- **AND** 页面 SHALL 展开目标 entry 所属 turn
- **AND** 左侧导航 SHALL 滚动到目标 entry 或其 turn header
- **AND** 目标 entry 或其 turn header SHALL 显示高亮状态

#### Scenario: 定位结束事件到左侧导航
- **WHEN** 当前 task 包含可映射的 `endEventId`
- **AND** 用户点击“定位结束事件”
- **THEN** 页面 SHALL 展开目标 entry 所属 group
- **AND** 页面 SHALL 展开目标 entry 所属 turn
- **AND** 左侧导航 SHALL 滚动到目标 entry 或其 turn header
- **AND** 目标 entry 或其 turn header SHALL 显示高亮状态

#### Scenario: 定位不默认替换 task detail
- **WHEN** 用户从 task detail 点击“定位开始事件”或“定位结束事件”
- **THEN** 页面 SHALL 保持当前 Task Segment detail 可见
- **AND** SHALL NOT 默认用原始日志 detail 替换 task detail

#### Scenario: 目标被筛选隐藏
- **WHEN** 目标 entry 存在但被当前 type filter 或搜索 filter 隐藏
- **THEN** 页面 SHALL 展开并滚动到目标 turn header
- **AND** 页面 SHALL 提示目标事件被当前筛选隐藏
- **AND** SHALL NOT 抛出脚本错误

#### Scenario: 事件无法映射
- **WHEN** `startEventId` 或 `endEventId` 无法映射到当前 session 的 entry
- **THEN** 对应定位按钮 SHALL disabled 或展示不可定位提示
- **AND** 页面 SHALL 保持当前 task detail 不变
