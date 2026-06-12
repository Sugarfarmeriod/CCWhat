## ADDED Requirements

### Requirement: Session Trace 双视图切换
Claude Log Viewer SHALL 在 Session Trace 中提供 `默认视图` 和 `调试视图` 两种左侧树展示模式。

#### Scenario: 默认进入默认视图
- **WHEN** 用户加载 viewer 并选择一个 session
- **THEN** Session Trace SHALL 默认使用 `默认视图`
- **AND** 左侧树 SHALL 展示主执行链路 Step
- **AND** 页面 SHALL NOT 展示完整内部事件列表作为默认体验

#### Scenario: 用户切换到调试视图
- **WHEN** 用户点击 `调试视图`
- **THEN** Session Trace SHALL 切换到 `debug` 模式
- **AND** 左侧树 SHALL 展示完整 Turn 时间线
- **AND** Turn 的顺序 SHALL 与底层 Minimal Turn 原始顺序一致

#### Scenario: 用户切回默认视图
- **WHEN** 用户从 `调试视图` 点击 `默认视图`
- **THEN** Session Trace SHALL 切回 `default` 模式
- **AND** 左侧树 SHALL 重新展示 primary Step projection
- **AND** 主工作区 SHALL NOT 变成空白

### Requirement: Trace 树消费 View Projection
Session Trace 树 SHALL 使用 `buildTurnViewProjection(mode, source)` 的投影结果渲染 Turn/Step 节点，而不是直接展示完整 Minimal Turn 列表。

#### Scenario: 默认视图渲染 Step projection
- **WHEN** `traceViewMode` 为 `default`
- **THEN** Trace 树 SHALL 使用 default projection
- **AND** 子节点 SHALL 使用 `Step N` label
- **AND** Step 编号 SHALL 连续，不因隐藏 internal Turn 产生断号

#### Scenario: 调试视图渲染 Turn projection
- **WHEN** `traceViewMode` 为 `debug`
- **THEN** Trace 树 SHALL 使用 debug projection
- **AND** 子节点 SHALL 使用底层 `Turn N` label
- **AND** ordinary internal Turn SHALL 仍按原始时序显示在其真实位置

#### Scenario: Task-first 树保持层级
- **WHEN** 当前 session 已确认或已有 Task Trace 数据
- **THEN** projection 渲染 SHALL 保留 `Task -> 会话 -> Step/Turn` 层级
- **AND** 切换视图 SHALL NOT 改变 Task 起止锚点或 Task 归属

#### Scenario: Conversation-first 树保持层级
- **WHEN** 当前 session 没有 Task Trace 数据
- **THEN** projection 渲染 SHALL 保留 `会话 -> Step/Turn` 层级
- **AND** 切换视图 SHALL NOT 改变 Conversation 或 Turn 的底层锚点

### Requirement: 默认视图降噪
默认视图 SHALL 隐藏普通 internal Turn，只保留 primary Step。

#### Scenario: 普通内部事件默认隐藏
- **WHEN** session 包含 ordinary `permission-mode`、`last-prompt`、`PostToolUse`、`file-history-snapshot`、`queue-operation`、system/context 注入或 attachment metadata
- **THEN** 默认视图 SHALL NOT 在左侧树中展示这些 ordinary internal Turn
- **AND** 调试视图 SHALL 仍展示这些 Turn

#### Scenario: thinking 默认可见
- **WHEN** session 包含 thinking 或 reasoning Turn
- **THEN** 默认视图 SHALL 将其作为 primary Step 展示
- **AND** thinking 内容 SHALL NOT 因默认视图被隐藏

#### Scenario: 异常内部事件默认可见
- **WHEN** ordinary internal Turn 包含 error、warning、failed、denied、rejected、blocked 或 permission-impacting 内容
- **THEN** 默认视图 SHALL 将其作为 primary Step 展示
- **AND** 该 Step SHALL 保留 underlying Turn 锚点

### Requirement: 类型筛选降级为调试筛选
底层类型筛选 SHALL 只作为调试视图下的高级筛选展示。

#### Scenario: 默认视图隐藏类型筛选
- **WHEN** `traceViewMode` 为 `default`
- **THEN** `user / assistant / system / attachment / perm / fhs / queue / other` 类型筛选 SHALL 隐藏或弱化为不可见高级控件
- **AND** 默认视图主入口 SHALL 只突出 `默认视图 / 调试视图`

#### Scenario: 调试视图显示类型筛选
- **WHEN** `traceViewMode` 为 `debug`
- **THEN** 类型筛选 SHALL 可见
- **AND** 类型筛选 SHALL 只影响左侧 Trace 树的可见节点
- **AND** 类型筛选 SHALL NOT 修改底层 Turn、Task 或 Conversation 数据

#### Scenario: 筛选为空时显示明确状态
- **WHEN** 调试视图类型筛选或搜索导致某 Conversation 没有可见 Turn
- **THEN** Trace 树 SHALL 显示明确空状态
- **AND** SHALL NOT 直接渲染空白区域

### Requirement: 视图切换选择状态
Session Trace SHALL 在默认视图和调试视图之间切换时保持稳定选择状态，或给出明确回退提示。

#### Scenario: 可见节点保持选中
- **WHEN** 当前选中的 Step/Turn 在目标视图中仍可见
- **THEN** 切换视图后 SHALL 保持该节点选中
- **AND** 右侧 Detail SHALL NOT 被清空

#### Scenario: internal Turn 在默认视图不可见
- **WHEN** 当前选中普通 internal Turn
- **AND** 用户切换到默认视图
- **THEN** Trace 树 SHALL 回退选中最近可见父节点或清晰提示该 Turn 已在默认视图隐藏
- **AND** 页面 SHALL 提供切回调试视图查看完整 Turn 的提示
- **AND** 主工作区 SHALL NOT 变成空白

#### Scenario: 空 projection 范围
- **WHEN** 某 Task 或 Conversation 在默认视图中没有 primary Step
- **THEN** Trace 树 SHALL 保留 Task 或 Conversation 节点
- **AND** 子区域 SHALL 显示“默认视图无主执行 Step，切换调试视图查看完整 Turn”或等价提示
