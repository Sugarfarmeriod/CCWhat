## ADDED Requirements

### Requirement: 前端派生会话层
Claude Log Viewer SHALL 在加载 session entries 后派生 Conversation 层，用于表示一次用户请求到 Agent 完成本次反馈之间的交互单元。

#### Scenario: 真实用户请求开始新会话
- **WHEN** session entries 中出现真实用户请求
- **THEN** viewer SHALL 创建一个新的 Conversation
- **AND** Conversation SHALL 拥有人类可读 label，例如 `会话 1`
- **AND** Conversation SHALL 记录 start anchor、end anchor、user message text 和所属 group

#### Scenario: 下一条真实用户请求结束上一会话
- **WHEN** 已存在当前 Conversation
- **AND** 后续 entries 中出现下一条真实用户请求
- **THEN** viewer SHALL 结束上一 Conversation
- **AND** viewer SHALL 创建新的 Conversation
- **AND** 两个 Conversation 的编号 SHALL 保持稳定且按原始执行顺序递增

#### Scenario: 非真实用户请求不开始新会话
- **WHEN** entry 是纯 tool_result、system-reminder、local-command、last-prompt、queue、permission 或重复镜像用户消息
- **THEN** viewer SHALL NOT 将该 entry 作为新 Conversation 的起点
- **AND** 该 entry SHALL 归入当前 Conversation、preamble 或 metadata

#### Scenario: 首个用户请求前的 entries
- **WHEN** 首个真实用户请求前存在 system/context/metadata entries
- **THEN** viewer SHALL NOT 因这些 entries 改变普通 Conversation 编号
- **AND** viewer MAY 将其归入 preamble 或 group metadata

### Requirement: 会话内派生最小 Turn
Claude Log Viewer SHALL 在每个 Conversation 内派生 minimal Turn，且每个 Turn 只表示一种执行片段。

#### Scenario: 用户消息 Turn
- **WHEN** Conversation 由真实用户请求开始
- **THEN** viewer SHALL 为该用户请求创建 `user_message` Turn
- **AND** 该 Turn SHALL 只包含当前用户请求对应的最小内容和原始 JSON 引用

#### Scenario: Thinking Turn
- **WHEN** assistant content 或 normalized event 表示 thinking/reasoning
- **THEN** viewer SHALL 创建 `thinking` Turn
- **AND** 该 Turn SHALL NOT 合并后续 tool_use 或 assistant text

#### Scenario: Assistant text Turn
- **WHEN** assistant content block 是普通 text
- **THEN** viewer SHALL 创建 `assistant_text` Turn
- **AND** 该 Turn SHALL NOT 合并同一 entry 中的 tool_use block

#### Scenario: Tool use Turn
- **WHEN** assistant content block 是 `tool_use`
- **THEN** viewer SHALL 为该 block 创建一个 `tool_use` Turn
- **AND** 该 Turn SHALL 记录 tool name、tool_use_id、input 摘要和 block anchor

#### Scenario: Tool result Turn
- **WHEN** user entry 或 normalized event 包含 `tool_result`
- **THEN** viewer SHALL 为该 tool_result 创建一个 `tool_result` Turn
- **AND** 该 Turn SHALL 记录 tool_use_id、结果摘要、错误状态和 block anchor

#### Scenario: 多 block assistant entry 拆分
- **WHEN** 一个 assistant entry 的 `message.content` 包含多个 block
- **THEN** viewer SHALL 按 block 顺序创建多个 Turn
- **AND** 每个 Turn SHALL 对应唯一 content block
- **AND** 一个 Turn SHALL NOT 包含多次 tool_use

#### Scenario: 一个 Turn 只表示一种片段
- **WHEN** viewer 完成 Turn 派生
- **THEN** 每个非 unknown Turn SHALL 只有一个 kind
- **AND** `tool_use` Turn SHALL NOT 同时包含 `tool_result`
- **AND** `assistant_text` Turn SHALL NOT 同时包含 `tool_use`

### Requirement: Conversation 和 Turn 稳定锚点
Claude Log Viewer SHALL 为 Conversation 和 minimal Turn 建立稳定锚点，使原始 entry、content block 和派生节点可互相定位。

#### Scenario: Conversation key 稳定
- **WHEN** viewer 派生 Conversation
- **THEN** 每个 Conversation SHALL 拥有稳定 `conversationKey`
- **AND** `conversationKey` SHALL 包含 group scope 和 conversation index

#### Scenario: Turn key 稳定
- **WHEN** viewer 派生 Turn
- **THEN** 每个 Turn SHALL 拥有稳定 `turnKey`
- **AND** `turnKey` SHALL 包含 group scope、conversation scope 和 turn index

#### Scenario: Entry anchor 映射到 Conversation 和 Turn
- **WHEN** 原始 entry 可通过 uuid、message id、event id 或 file anchor 定位
- **THEN** viewer SHALL 能将该 entry 映射到所属 Conversation
- **AND** viewer SHALL 能将该 entry 映射到该 entry 派生出的一个或多个 Turn

#### Scenario: Content block anchor 映射到 Turn
- **WHEN** Turn 来自 entry 内的某个 content block
- **THEN** viewer SHALL 为该 Turn 记录 block anchor
- **AND** block anchor SHALL 能映射回唯一 Turn

#### Scenario: 兼容旧 entry 级定位
- **WHEN** 旧逻辑提供 entry 级 `startEventId` 或 `endEventId`
- **THEN** viewer SHALL 能将该 anchor 映射到所属 Conversation
- **AND** viewer SHALL 能映射到该 entry 下第一个或最后一个相关 minimal Turn

### Requirement: Change 1 不改变 Task 树注入和 Tools Skills Snapshot
Conversation minimal Turn 数据层改造 SHALL NOT 在本 change 中实现 Task 注入或 Tools / Skills Snapshot UI。

#### Scenario: 不注入 Task 树
- **WHEN** task segmentation 返回任务结果
- **THEN** 本 change SHALL NOT 要求将 Task 作为左侧树顶层分组渲染
- **AND** Task 注入 SHALL 留给后续 change

#### Scenario: 不展示 Tools Skills Snapshot
- **WHEN** session 加载完成
- **THEN** 本 change SHALL NOT 要求在 Trace 顶部展示 Tools / Skills Snapshot 节点
- **AND** Tools / Skills Snapshot SHALL 留给后续 change
