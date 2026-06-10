## ADDED Requirements

### Requirement: Task-first Workbench App Shell
Claude Log viewer SHALL be redesigned as a Task-first Agent Session Workbench with a persistent left navigation, global context bar, and page-based main workspace.

#### Scenario: 默认进入 Tasks 页面
- **WHEN** 用户打开当前 session viewer
- **THEN** 页面 SHALL 默认显示 `Tasks` 页面
- **AND** SHALL NOT 默认显示 Raw Events 日志树

#### Scenario: 左侧一级功能导航
- **WHEN** viewer 渲染完成
- **THEN** 左侧 SHALL 显示一级功能导航
- **AND** 导航 SHALL 包含 `Tasks`、`Overview`、`Timeline`、`Sessions`、`Raw Events`、`Req / Resp`、`Diff`、`Diagnostics`、`Export`、`Settings`
- **AND** 当前 active 页面 SHALL 有明确选中态

#### Scenario: Raw Events 不再占据全局左侧
- **WHEN** 用户处于 `Tasks`、`Overview`、`Diff` 或 `Diagnostics` 页面
- **THEN** 左侧 SHALL 仍显示一级功能导航
- **AND** SHALL NOT 显示 session user turn 日志树作为全局导航

### Requirement: Global Context Bar
Workbench SHALL keep only global context controls in the top bar.

#### Scenario: 顶部上下文栏内容
- **WHEN** viewer 渲染完成
- **THEN** 顶部 SHALL 显示当前 Agent、Project、Session、Search 和 Refresh
- **AND** 顶部 SHALL NOT 放置导出、重新切分、诊断、Diff 筛选等页面内操作

#### Scenario: 全局搜索入口
- **WHEN** 用户使用顶部搜索框
- **THEN** 搜索意图 SHALL 覆盖 tasks、turns、events、files、commands
- **AND** 搜索框 placeholder SHOULD 表达其跨对象搜索范围

#### Scenario: 上下文选择
- **WHEN** 用户查看 Agent、Project 或 Session 控件
- **THEN** 控件 SHALL 表示当前上下文
- **AND** SHOULD 支持后续切换当前上下文的交互形态

### Requirement: Tasks Workbench Page
`Tasks` 页面 SHALL be the primary Task Trace workspace for the current session.

#### Scenario: Task List and Task Detail layout
- **WHEN** 用户进入 `Tasks` 页面
- **THEN** 页面 SHALL 显示 Task List 和 Task Detail 两个主要区域
- **AND** 用户选择 task 后 SHALL 在 Task Detail 中显示该 task 的详情

#### Scenario: Task card fields
- **WHEN** Task List 渲染 task card
- **THEN** task card SHALL 展示 task id、title、task type、status、turn range、files changed 数量、commands 数量、tests 结果、errors 数量、confidence 和 boundary reason 摘要

#### Scenario: Task Detail tabs
- **WHEN** 用户选择一个 task
- **THEN** Task Detail SHALL 提供 `Overview`、`Evidence`、`Turns`、`Files & Diff`、`Commands`、`Raw` 这些信息区或等价 tabs
- **AND** commands、tests、errors SHALL NOT 只能混在通用 Evidence 列表中展示

#### Scenario: Task selection
- **WHEN** 用户点击 Task List 中任意 task
- **THEN** 页面 SHALL 将该 task 设置为 active task
- **AND** Task Detail、相关 evidence 链接和 task-scope 页面跳转 SHALL 使用 active task

### Requirement: Task Detail Evidence Semantics
Task Detail SHALL distinguish agent claims, evidence, failures, and raw debug data.

#### Scenario: Agent final claim
- **WHEN** task 包含 `finalClaim`
- **THEN** 页面 SHALL 以“Agent 最终声明”展示
- **AND** SHALL 标明该内容是 agent 自述，不代表任务成功
- **AND** 长文本 SHALL 默认摘要展示并可展开全文

#### Scenario: Errors summary
- **WHEN** task 包含 errors
- **THEN** 页面 SHALL 默认展示错误摘要和错误数量
- **AND** 长错误日志 SHALL 折叠展示原文
- **AND** 错误摘要 SHALL 避免撑开 Task Detail 布局

#### Scenario: Raw debug data
- **WHEN** 用户需要查看原始 task 数据
- **THEN** 页面 SHALL 在 `Raw` 区域或折叠区域展示 raw JSON
- **AND** raw JSON SHALL 经过 HTML 转义

### Requirement: Canonical Navigation Target
Workbench SHALL use a canonical navigation target model to connect tasks, turns, events, files, commands, req/resp records, and diffs.

#### Scenario: Build navigation aliases
- **WHEN** session 加载完成
- **THEN** 前端 SHALL 建立可导航 alias index
- **AND** alias index SHALL 支持 `eventId`、`main:<line>`、`agent-<id>:<line>`、normalized event id、message id、uuid 和 tool use id 中可用的标识
- **AND** 每个可导航 entry SHALL 能映射到 entry index 和 turn key

#### Scenario: Task boundary target
- **WHEN** task 包含 `startEventId` 或 `endEventId`
- **THEN** 页面 SHALL 尝试解析为 canonical navigation target
- **AND** 若解析成功，用户 SHALL 能从 task 跳转到对应 Raw Events turn 或 entry
- **AND** 若解析失败，页面 SHALL 显示不可定位状态和调试信息，而不是静默失败

#### Scenario: Normalized event id support
- **WHEN** session 来自 Codex、OpenCode 或 generic normalized events
- **THEN** task boundary navigation SHALL NOT 只依赖 `main:<line>` 或 `agent-<id>:<line>` 格式
- **AND** SHALL 使用 normalized event 的 `id` 或 `eventId` 建立映射

#### Scenario: Cross-page navigation preserves scope
- **WHEN** 用户从 Task Detail 跳转到 Raw Events、Diff、Req / Resp 或 Diagnostics
- **THEN** 目标页面 SHALL 保留当前 session scope
- **AND** SHOULD 保留当前 active task scope

### Requirement: Overview Page
`Overview` 页面 SHALL summarize the current session from a task-oriented perspective.

#### Scenario: Session summary metrics
- **WHEN** 用户进入 `Overview`
- **THEN** 页面 SHALL 展示当前 session 的 task 数、turn 数、tool calls、files changed、commands、tests、failed tests、failed tasks、ambiguous tasks、low confidence tasks

#### Scenario: Task timeline and map
- **WHEN** Overview 渲染成功
- **THEN** 页面 SHALL 展示 task timeline 或 task map
- **AND** 用户 SHOULD 能从 timeline/map 定位到对应 task

### Requirement: Evidence Pages
Workbench SHALL provide evidence pages for Raw Events, Req / Resp, and Diff without making them the primary navigation surface.

#### Scenario: Raw Events page
- **WHEN** 用户进入 `Raw Events`
- **THEN** 页面 SHALL 保留按 turn 展示原始日志的能力
- **AND** SHALL 支持从 canonical navigation target 定位到具体 turn 或 entry

#### Scenario: Diff page scope
- **WHEN** 用户进入 `Diff`
- **THEN** 页面 SHALL 支持 session scope 的文件改动视图
- **AND** 当存在 active task 时 SHOULD 支持 task scope 的相关文件和 patch 摘要

#### Scenario: Req Resp page scope
- **WHEN** 用户进入 `Req / Resp`
- **THEN** 页面 SHALL 支持查看当前 session 的原始请求响应
- **AND** 当存在 active task 或 active event target 时 SHOULD 聚焦相关 message/request

### Requirement: Diagnostics Page
`Diagnostics` 页面 SHALL surface task-oriented failure and ambiguity signals for the current session.

#### Scenario: Diagnostics categories
- **WHEN** 用户进入 `Diagnostics`
- **THEN** 页面 SHALL 展示失败任务、低置信度边界、测试失败、重复工具调用、Agent 声明与证据不一致、不可定位事件等诊断项中的可用项

#### Scenario: Diagnostics links to evidence
- **WHEN** diagnostic item 关联 task 或 event
- **THEN** 用户 SHALL 能从该 diagnostic item 跳转到对应 task 或 evidence page

### Requirement: Export Page
`Export` 页面 SHALL centralize export actions for session observability and task trace data.

#### Scenario: Export options
- **WHEN** 用户进入 `Export`
- **THEN** 页面 SHALL 展示 Session、Task Trace、Raw Logs、Req / Resp、Diff、Dataset preview 等导出选项
- **AND** 导出动作 SHALL NOT 出现在全局顶部栏

#### Scenario: Dataset preview boundary
- **WHEN** 页面展示 Dataset 导出选项
- **THEN** 页面 SHALL 将其标记为预览或实验能力
- **AND** SHALL NOT 暗示完整 Dataset Builder 已实现

### Requirement: Developer Tool Visual Style
Workbench SHALL use a dense, professional developer-tool visual style suitable for repeated inspection and diagnosis.

#### Scenario: Non-marketing layout
- **WHEN** 页面渲染
- **THEN** UI SHALL prioritize compact controls, tables/lists/cards for operational data, clear panes and readable status badges
- **AND** SHALL NOT use marketing hero layout, decorative landing-page composition, or chat-app-first layout

#### Scenario: Long technical text handling
- **WHEN** 页面展示 paths、commands、errors、JSON、diff 或 request/response data
- **THEN** long text SHALL wrap, truncate, scroll, or collapse in a controlled way
- **AND** SHALL NOT overlap adjacent UI or resize fixed controls unpredictably
