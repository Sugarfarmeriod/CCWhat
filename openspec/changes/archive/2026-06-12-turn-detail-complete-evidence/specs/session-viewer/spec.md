## ADDED Requirements

### Requirement: Task-first Trace 闭环
Claude Log Viewer SHALL 在当前 session 有 task segmentation 结果后，将 Session Trace 渲染为 `Task -> 会话 -> Step/Turn` 结构。

#### Scenario: 任务切分后立即进入 Task-first
- **WHEN** 用户对当前 session 成功运行任务切分
- **THEN** Session Trace SHALL 使用该 task segmentation result 作为 active task source
- **AND** 左侧 Trace 树 SHALL 以 Task 作为 Snapshot 后的一级节点
- **AND** SHALL NOT 要求用户额外点击确认后才进入 Task-first

#### Scenario: 确认状态不决定 Task-first 结构
- **WHEN** 当前 session 有 task segmentation result 但尚未确认
- **THEN** Session Trace SHALL 仍展示 `Task -> 会话 -> Step/Turn`
- **AND** Tasks 页面 SHALL 可以继续显示 `预览中`
- **AND** 用户点击确认后 SHALL 只更新确认状态，不改变 Task-first 数据来源

#### Scenario: 未归类会话可见
- **WHEN** 当前 session 有 task segmentation result
- **AND** 某些 Conversation 或 Turn 不属于任何 Task range
- **THEN** Session Trace SHALL 在 Task-first 结构后展示 `Unassigned`
- **AND** Unassigned 下的会话 SHALL 继续支持默认视图 Step 和调试视图 Turn

#### Scenario: 重新切分刷新 active task source
- **WHEN** 用户重新切分当前 session
- **THEN** 新结果 SHALL 替换 active task source
- **AND** Session Trace SHALL 立即刷新为新的 Task-first 结构
- **AND** 旧确认状态 SHALL 被清除或降级为未确认

### Requirement: Turn Detail 完整证据
Claude Log Viewer SHALL 在右侧 Detail 中展示当前选中 Minimal Turn 的完整证据，视图模式不得裁剪 Detail 内容。

#### Scenario: 默认视图 Step 展示完整 underlying Turn
- **WHEN** 用户在默认视图点击一个 `Step`
- **THEN** 右侧 Detail SHALL 使用该 Step 的 `underlyingTurnKey` 定位底层 Minimal Turn
- **AND** Detail SHALL 展示该 Minimal Turn 的完整主证据
- **AND** Detail SHALL 提供可展开的原始 JSON

#### Scenario: 调试视图 Turn 展示完整内容
- **WHEN** 用户在调试视图点击一个 `Turn`
- **THEN** 右侧 Detail SHALL 展示该 Turn 的完整内容
- **AND** SHALL 包含 entry/block 定位信息
- **AND** SHALL 提供可展开的原始 JSON

#### Scenario: 视图切换不清空已选证据
- **WHEN** 用户已选中一个在目标视图仍可见的 Step 或 Turn
- **AND** 用户切换默认视图和调试视图
- **THEN** 右侧 Detail SHALL 保持当前底层 Turn 的证据内容
- **AND** SHALL NOT 变成空白或只显示摘要

### Requirement: 调试筛选不裁剪 Detail
调试视图中的类型筛选 SHALL 只影响左侧 Trace 树可见节点，不得裁剪右侧 Detail 的证据内容。

#### Scenario: 已选 Turn 被筛选隐藏后 Detail 保持完整
- **WHEN** 用户在调试视图选中一个 Turn
- **AND** 用户修改类型筛选使该 Turn 不再出现在左侧树
- **THEN** 右侧 Detail SHALL 继续展示该 Turn 的完整证据
- **AND** SHALL NOT 显示“当前筛选隐藏了该 Turn 的全部事件”作为替代内容

#### Scenario: 默认视图不受类型筛选影响
- **WHEN** 用户在调试视图调整类型筛选
- **AND** 用户切回默认视图并点击任意 Step
- **THEN** 右侧 Detail SHALL 展示该 Step underlying Turn 的完整证据
- **AND** SHALL NOT 根据调试筛选裁剪内容

### Requirement: Tool Turn 证据完整
Claude Log Viewer SHALL 对 tool_use 和 tool_result Turn 展示完整工具证据。

#### Scenario: tool_use 展示完整 input
- **WHEN** 当前选中 Turn 的 kind 为 `tool_use`
- **THEN** Detail SHALL 展示工具名称
- **AND** SHALL 展示完整 tool id 或 tool_use_id
- **AND** SHALL 展示完整 input JSON
- **AND** SHALL 提供该 content block 和 entry 的原始 JSON

#### Scenario: tool_result 展示完整 result
- **WHEN** 当前选中 Turn 的 kind 为 `tool_result`
- **THEN** Detail SHALL 展示完整 result content
- **AND** SHALL 展示 `tool_use_id`
- **AND** SHALL 展示 `is_error` 或等价错误状态
- **AND** SHALL 提供该 content block 和 entry 的原始 JSON

#### Scenario: 长工具结果不被摘要截断
- **WHEN** tool_result content 长度超过左侧 summary 截断阈值
- **THEN** Detail SHALL 保留完整 content
- **AND** SHALL 使用滚动或折叠展示控制布局

### Requirement: Internal Turn 证据完整
Claude Log Viewer SHALL 对 internal Turn 展示可调试的完整证据。

#### Scenario: permission-mode 展示完整状态
- **WHEN** 当前选中 Turn 表示 `permission-mode` 或权限相关 internal event
- **THEN** Detail SHALL 展示权限状态、相关文本或 payload
- **AND** SHALL 提供 entry metadata 和原始 JSON

#### Scenario: snapshot 和 queue 展示结构化内容
- **WHEN** 当前选中 Turn 表示 `file-history-snapshot` 或 `queue-operation`
- **THEN** Detail SHALL 展示可读的结构化字段
- **AND** SHALL 提供完整原始 JSON

#### Scenario: system context unknown 有 raw fallback
- **WHEN** 当前选中 Turn 的 kind 为 `system`、`context` 或 `unknown`
- **THEN** Detail SHALL 展示可提取文本或 structured payload
- **AND** 如果无法识别主证据，SHALL 至少展示完整原始 JSON

### Requirement: Detail 定位信息
右侧 Detail SHALL 展示足够的定位信息，帮助用户从 Step/Turn 追溯到底层日志。

#### Scenario: 显示基础锚点
- **WHEN** Detail 展示任意 Minimal Turn
- **THEN** Detail SHALL 显示 turn label、kind、conversation key 或 group id
- **AND** 如果存在 SHALL 显示 file line、entry index、event id、block anchor

#### Scenario: Raw JSON 包含 entry 和 content block
- **WHEN** Detail 展示任意 Minimal Turn
- **THEN** 原始 JSON 区域 SHALL 包含对应 entry 的核心字段
- **AND** 如果 Turn 来自 content block，SHALL 包含该 block 的完整 JSON
