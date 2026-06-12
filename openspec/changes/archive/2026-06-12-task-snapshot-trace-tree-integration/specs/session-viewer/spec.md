## ADDED Requirements

### Requirement: Trace 树顶部显示 Tools Skills Snapshot
Claude Log Viewer 的 `Session` 页面 SHALL 在 Trace 树顶部显示唯一的 `Tools / Skills Snapshot` 节点，用于展示当前 Trace 初始可用工具和技能。

#### Scenario: 未切分时显示 Snapshot
- **WHEN** 用户加载 session 并进入 `Session` 页面
- **THEN** Trace 树 SHALL 在会话节点之前显示 `Tools / Skills Snapshot` 节点
- **AND** Snapshot 节点 SHALL 只显示一次
- **AND** 会话节点 SHALL 继续显示在 Snapshot 节点之后

#### Scenario: 切分确认后 Snapshot 仍在顶部
- **WHEN** 用户确认 Task 切分结果后进入 `Session` 页面
- **THEN** Trace 树 SHALL 在所有 Task 节点之前显示 `Tools / Skills Snapshot` 节点
- **AND** Snapshot 节点 SHALL NOT 出现在任何 Task 节点内部
- **AND** Snapshot 节点 SHALL NOT 因 Task 数量增加而重复
- **AND** Task 节点 SHALL 是 Snapshot 之后的一级可展开节点，而不是 Turn 上的 badge

#### Scenario: 点击 Snapshot 展示详情
- **WHEN** 用户点击 `Tools / Skills Snapshot` 节点
- **THEN** 右侧详情区 SHALL 展示当前 Trace 的 Tools 列表和 Skills 列表
- **AND** 右侧详情区 SHALL 展示 Snapshot 的来源说明或锚点信息
- **AND** 右侧详情区 SHALL NOT 展示某个 Task、会话或 Turn 的详情

### Requirement: Task 切分结果需要确认后注入 Trace 树
Claude Log Viewer SHALL 将自动切分得到的 Task Segment 先作为预览结果展示，只有用户确认后才将 Task 注入 `Session` 页面的 Trace 树。

#### Scenario: 切分完成但未确认
- **WHEN** 用户点击“切分 Task”并得到 Task Segment 结果
- **THEN** `Tasks` 页面 SHALL 展示切分预览
- **AND** `Session` 页面的 Trace 树 SHALL 仍保持 `Snapshot -> 会话 -> Turn` 结构
- **AND** 页面 SHALL 提供“确认切分”或等价操作

#### Scenario: 用户确认切分
- **WHEN** 用户在 `Tasks` 页面确认当前 Task Segment 结果
- **THEN** 当前 session SHALL 记录已确认的 Task Trace 状态
- **AND** `Session` 页面的 Trace 树 SHALL 切换为 `Snapshot -> Task -> 会话 -> Turn` 结构
- **AND** 已确认状态 SHALL 只作用于当前 session
- **AND** 页面 SHALL NOT 仅通过在 Turn 行内显示 `Task N` badge 来表示已确认 Task Trace

#### Scenario: 用户重新切分
- **WHEN** 用户在已有确认结果后再次触发重新切分
- **THEN** 页面 SHALL 取消当前 session 的已确认 Task Trace 状态
- **AND** 新结果 SHALL 先作为预览展示
- **AND** `Session` 页面的 Task 注入 SHALL 等待用户再次确认

### Requirement: Task 节点作为会话上层分组
Claude Log Viewer SHALL 在 Task Trace 确认后，将 Task 节点作为会话节点的上层分组展示。

#### Scenario: Task 是 Trace 一级结构
- **WHEN** Task Trace 已确认且存在至少一个 Task Segment
- **THEN** Trace 树 SHALL 在 `Tools / Skills Snapshot` 之后直接展示 Task 节点
- **AND** Source group，例如 `main`、`Claude Code` 或 subagent 名称，MAY 作为 Task 节点或会话节点的元信息展示
- **AND** Source group SHALL NOT 成为 Snapshot 和 Task 之间的树层级
- **AND** 被 Task 覆盖的会话 SHALL NOT 继续作为 Task 外的独立会话节点展示

#### Scenario: Task 节点展示基础信息
- **WHEN** Trace 树渲染 Task 节点
- **THEN** Task 节点 SHALL 展示人类可读 label，例如 `Task 1`
- **AND** Task 节点 SHALL 展示 title 或 user intent 摘要
- **AND** Task 节点 MAY 展示 task type、status、confidence、覆盖会话数、覆盖 Turn 数和 boundary reason 简短摘要
- **AND** Task 节点 SHALL NOT 使用长 UUID 或 event id 作为默认标题

#### Scenario: Task 下展示会话和 Turn
- **WHEN** Task 节点处于展开状态
- **THEN** Trace 树 SHALL 在该 Task 下展示被该 Task 覆盖的会话节点
- **AND** 每个会话节点下 SHALL 展示该 Task 覆盖范围内的 Turn 节点
- **AND** 会话和 Turn 的 label SHALL 保持原始 Trace 中的稳定编号
- **AND** Task 下的 Turn 节点 SHALL NOT 再通过 `Task N` badge 表示自己的所属 Task

#### Scenario: Task 锚点使用统一导航索引映射
- **WHEN** Task Segment 包含 `startEventId` 或 `endEventId`
- **THEN** Task-to-Trace 映射 SHALL 使用现有统一 Turn lookup 能力解析锚点
- **AND** 映射 SHALL 支持 event id、uuid、message id、block anchor 和 `main:<line>` / subagent file anchor
- **AND** 映射 SHALL NOT 只用 `_eventId` 或 `uuid` 自建索引

#### Scenario: Task 部分无法映射仍显示 Task 节点
- **WHEN** Task Trace 已确认但某个 Task 的起止锚点只能部分映射或无法映射
- **THEN** Trace 树 SHALL 仍显示该 Task 节点
- **AND** Task detail SHALL 显示该 Task 的映射降级状态
- **AND** 页面 SHALL NOT 因该 Task 映射失败而回退为 `会话 -> Turn + Task badge` 展示

#### Scenario: Task 展开折叠
- **WHEN** 用户点击 Task 节点的展开/折叠控件
- **THEN** 页面 SHALL 切换该 Task 下会话节点和 Turn 节点的可见状态
- **AND** 其他 Task 的展开状态 SHALL 保持不变

#### Scenario: 未确认状态才允许 Turn badge 作为预览辅助
- **WHEN** Task Segment 只处于预览状态且尚未确认
- **THEN** 页面 MAY 在 Turn 节点上展示 `Task N` badge 作为辅助跳转
- **AND** 一旦 Task Trace 被确认，Task 所属关系 SHALL 通过 `Task -> 会话 -> Turn` 树层级表达

### Requirement: Task 节点详情
Claude Log Viewer SHALL 在用户选中 Task 节点时展示 Task 基础摘要，帮助用户理解该 Task 覆盖的目标和执行范围。

#### Scenario: 点击 Task 节点
- **WHEN** 用户点击 Trace 树中的 Task 节点主体
- **THEN** 页面 SHALL 将该 Task 标记为当前选中节点
- **AND** 右侧详情区 SHALL 展示 Task 基础摘要

#### Scenario: Task detail 内容
- **WHEN** 右侧详情区展示 Task detail
- **THEN** 页面 SHALL 展示 Task label、title 或 user intent、task type、status、confidence、起止 Turn、覆盖会话列表和 boundary reason
- **AND** 页面 SHALL 提供跳转到该 Task 首个会话或首个 Turn 的入口
- **AND** 页面 SHALL NOT 在本 change 中展示复杂 diagnostics、diff、test result 或 req/resp 明细

#### Scenario: Task 范围无法完整映射
- **WHEN** Task 的起止锚点无法映射到 Conversation/minimal Turn
- **THEN** Task detail SHALL 显示明确的无法定位提示
- **AND** Task 节点 SHALL 仍可被选中
- **AND** 页面 SHALL NOT 抛出脚本错误或静默失败

### Requirement: Trace 节点选择支持 Snapshot Task Conversation Turn
Claude Log Viewer SHALL 使用统一节点选择机制支持 `snapshot`、`task`、`conversation` 和 `turn` 四类节点。

#### Scenario: 选择唯一节点
- **WHEN** 用户点击 Snapshot、Task、会话或 Turn 节点
- **THEN** 页面 SHALL 只将被点击节点标记为当前选中节点
- **AND** 其他节点 SHALL 取消选中状态
- **AND** 右侧详情 SHALL 匹配当前节点类型

#### Scenario: Task 下选择会话
- **WHEN** 用户点击某个 Task 下的会话节点
- **THEN** 页面 SHALL 复用已有会话详情展示该会话内容
- **AND** 页面 SHALL 保持该会话所属 Task 的上下文可见

#### Scenario: Task 下选择 Turn
- **WHEN** 用户点击某个 Task 下的 Turn 节点
- **THEN** 页面 SHALL 复用已有 Turn 极简详情展示 `Agent 响应` 和 `原始 JSON`
- **AND** 页面 SHALL 保持该 Turn 所属 Task 和会话的上下文可见

### Requirement: Task 定位使用注入后的 Trace 树
Claude Log Viewer SHALL 在 Task Trace 确认后，将 Task 相关定位操作导航到注入后的 Task 树节点，而不是只跳到未分组的会话或 Turn。

#### Scenario: 定位开始 Turn
- **WHEN** 用户在 Task detail 点击“定位开始 Turn”
- **THEN** 页面 SHALL 切换到 `Session` 页面
- **AND** 页面 SHALL 展开目标 Task 和目标会话
- **AND** 页面 SHALL 选中、滚动并临时高亮目标 Turn

#### Scenario: 定位结束 Turn
- **WHEN** 用户在 Task detail 点击“定位结束 Turn”
- **THEN** 页面 SHALL 切换到 `Session` 页面
- **AND** 页面 SHALL 展开目标 Task 和目标会话
- **AND** 页面 SHALL 选中、滚动并临时高亮目标 Turn

#### Scenario: 未确认 Task Trace 时定位
- **WHEN** 用户尚未确认 Task Trace 但点击 Task 预览中的定位入口
- **THEN** 页面 SHALL 按现有 `会话 -> Turn` Trace 树定位目标 Turn
- **AND** 页面 SHALL NOT 自动确认 Task Trace

### Requirement: 本 change 不修改切分算法和评测逻辑
本 change SHALL 只负责将已有 Task Segment 结果和 Tools / Skills Snapshot 展示到 Trace 树中，不改变 Task 切分算法和任务评测逻辑。

#### Scenario: 不改变 segment API
- **WHEN** 用户触发 Task 切分
- **THEN** 前端 SHALL 继续使用现有 `/api/task-segments` 返回结果
- **AND** 本 change SHALL NOT 要求后端返回新的切分字段

#### Scenario: 不重新判断任务成功率
- **WHEN** Trace 树渲染 Task 节点
- **THEN** 页面 SHALL 使用已有 Task Segment 中的 status、confidence 或 equivalent 字段
- **AND** 页面 SHALL NOT 在本 change 中新增任务成功率判断规则

#### Scenario: 不实现复杂 Tools Skills 变化检测
- **WHEN** session 中可能存在 Tools 或 Skills 变化
- **THEN** 本 change MAY 保留特殊 Turn 扩展点
- **AND** 本 change SHALL NOT 要求实现完整 Tools / Skills diff 检测和版本历史
