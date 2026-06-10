## ADDED Requirements

### Requirement: Task segmentation entry point
Claude Log 页面 SHALL 为当前已加载 session 提供任务切分入口，用于展示 `/api/task-segments` 返回的结构化 Task Segment 结果。

#### Scenario: Button disabled before session selection
- **WHEN** 页面尚未选择或加载 session
- **THEN** 任务切分按钮 SHALL 处于 disabled 状态
- **AND** 按钮 SHALL 显示“任务切分”

#### Scenario: Button enabled after session load
- **WHEN** 用户成功加载一个 session
- **THEN** 页面 SHALL 启用任务切分按钮
- **AND** 若该 session 尚无缓存结果，按钮 SHALL 显示“任务切分”

#### Scenario: Restore cached task segmentation result
- **WHEN** 当前 session 已生成任务切分结果
- **AND** detail panel 当前显示原始日志详情或分析报告
- **THEN** 任务切分按钮 SHALL 显示“查看任务切分”
- **AND** 用户点击后 SHALL 恢复该 session 的缓存任务切分视图

### Requirement: Task segmentation API request
Claude Log 页面 SHALL 使用当前 session ID 调用 `POST /api/task-segments`，不上传完整 session 内容。

#### Scenario: Request current session only
- **WHEN** 用户点击任务切分按钮且当前 session 没有缓存结果
- **THEN** 前端 SHALL 向 `/api/task-segments` 发送 POST 请求
- **AND** 请求体 SHALL 为 `{"sessionId": "<current-session-id>"}`
- **AND** SHALL NOT 发送 turns、筛选结果、完整日志、跨 session 参数或多 session 参数

#### Scenario: Loading state
- **WHEN** `/api/task-segments` 请求进行中
- **THEN** 任务切分按钮 SHALL disabled
- **AND** 按钮 SHALL 显示“切分中…”
- **AND** detail panel SHALL 显示任务切分 loading 状态

#### Scenario: Failed request
- **WHEN** `/api/task-segments` 返回错误或网络失败
- **THEN** 前端 SHALL 恢复任务切分按钮可点击状态
- **AND** detail panel SHALL 显示可读错误信息
- **AND** 若该 session 已有旧缓存结果，旧结果 SHALL 保留

### Requirement: Task segmentation cache
Claude Log 页面 SHALL 按 `sessionId` 在页面内存中缓存任务切分结果。

#### Scenario: Cache successful result
- **WHEN** `/api/task-segments` 返回成功结果
- **THEN** 前端 SHALL 将结果保存到当前页面内存缓存
- **AND** 缓存 key SHALL 为当前 `sessionId`
- **AND** SHALL NOT 写入 localStorage、后端文件、session 日志或导出包

#### Scenario: Session switch updates button state
- **WHEN** 用户切换 session
- **THEN** 页面 SHALL 根据新 session 是否已有任务切分缓存更新按钮文案
- **AND** 新 session 没有缓存时 SHALL 显示“任务切分”
- **AND** 新 session 有缓存时 SHALL 显示“查看任务切分”

#### Scenario: Re-segment current session
- **WHEN** 当前 session 已有任务切分结果
- **AND** 用户在任务切分视图中点击“重新切分”
- **THEN** 前端 SHALL 重新调用 `/api/task-segments`
- **AND** 请求成功后 SHALL 用新结果覆盖当前 session 的旧缓存
- **AND** 请求失败时 SHALL 保留旧缓存并显示失败原因

### Requirement: Task segmentation overview
Claude Log 页面 SHALL 在 detail panel 中展示任务切分概览和 task card 列表。

#### Scenario: Render summary
- **WHEN** `/api/task-segments` 返回成功结果
- **THEN** detail panel SHALL 展示 summary 信息
- **AND** 至少包含任务数量、ambiguous 状态、topic flip 数量和生成耗时

#### Scenario: Render empty state
- **WHEN** `/api/task-segments` 返回 `tasks` 为空数组
- **THEN** detail panel SHALL 显示“未识别到任务片段”或等价空状态
- **AND** SHALL NOT 渲染空白页面

#### Scenario: Render task cards
- **WHEN** 返回结果包含一个或多个 tasks
- **THEN** detail panel SHALL 为每个 task 渲染一个 task card
- **AND** task card SHALL 展示 task id、title、task type、status、filesChanged 数量、commands 数量、errors 数量、subagent 数量和 ambiguous 标记

#### Scenario: Select a task
- **WHEN** 用户点击 task card
- **THEN** 页面 SHALL 将该 task 标记为选中
- **AND** 在同一 detail panel 中展示该 task 的详情区块

### Requirement: Task segmentation detail panel
Claude Log 页面 SHALL 展示所选 Task Segment 的 evidence、边界原因、文件权重和原始 JSON。

#### Scenario: Render task overview
- **WHEN** 用户选中一个 task
- **THEN** task 详情 SHALL 展示 title、task type、status、startEventId、endEventId 和 finalClaim

#### Scenario: Render evidence
- **WHEN** 用户选中一个 task
- **THEN** task 详情 SHALL 展示 filesRead、filesChanged、commands、testCommands、errors、subagentIds 和 todosUser
- **AND** 空 evidence 列表 SHALL 显示为空状态而不是 undefined/null

#### Scenario: Render boundary reasons
- **WHEN** task 包含 `boundaryReasons`
- **THEN** task 详情 SHALL 逐条展示 boundary reason
- **AND** SHALL 保留原始原因文本中的信号名称和分数信息

#### Scenario: Render file weights
- **WHEN** task 包含 `fileWeights`
- **THEN** task 详情 SHALL 按权重降序展示文件和权重

#### Scenario: Render raw task JSON
- **WHEN** 用户查看 task 详情
- **THEN** 页面 SHALL 提供折叠的 raw JSON 区块
- **AND** raw JSON 内容 SHALL 经过 HTML 转义，不执行其中的 HTML 或脚本

### Requirement: Task segmentation event navigation
Claude Log 页面 SHALL 支持从 Task Segment 定位到起止事件附近的原始日志条目。

#### Scenario: Locate start event
- **WHEN** task 包含可映射的 `startEventId`
- **AND** 用户点击“定位开始事件”
- **THEN** 页面 SHALL 选中并展开对应原始日志条目
- **AND** detail panel SHALL 显示该原始日志条目详情

#### Scenario: Locate end event
- **WHEN** task 包含可映射的 `endEventId`
- **AND** 用户点击“定位结束事件”
- **THEN** 页面 SHALL 选中并展开对应原始日志条目
- **AND** detail panel SHALL 显示该原始日志条目详情

#### Scenario: Event not found
- **WHEN** task 的 `startEventId` 或 `endEventId` 无法映射到当前前端日志条目
- **THEN** 对应定位入口 SHALL disabled 或显示不可定位提示
- **AND** 页面 SHALL NOT 抛出脚本错误

### Requirement: Task segmentation debug boundaries
Claude Log 页面 SHALL 展示或折叠展示 `/api/task-segments` 返回的 debug boundaries，用于人工校准规则。

#### Scenario: Render debug boundaries
- **WHEN** 返回结果包含 `debugBoundaries`
- **THEN** 任务切分视图 SHALL 提供 debug boundaries 区块
- **AND** 每条 boundary SHALL 展示 eventId、score、shouldSplit 和 reasons

#### Scenario: No debug boundaries
- **WHEN** 返回结果不包含 debug boundaries 或为空数组
- **THEN** 页面 SHALL 显示空状态
- **AND** SHALL NOT 影响 task cards 或 task detail 渲染
