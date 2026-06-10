## ADDED Requirements

### Requirement: Session + Tasks 双模块工作台
Viewer SHALL prioritize two core modules: `Session` and `Tasks`.

#### Scenario: 左侧核心导航
- **WHEN** viewer 渲染完成
- **THEN** 左侧 SHALL 显示 `Session` 和 `Tasks` 两个核心导航项
- **AND** `Session` SHALL be the default active page
- **AND** 其他非核心页面 MAY be hidden or shown as explicit placeholders

#### Scenario: 选择 session 后不出现空白主工作区
- **WHEN** 用户选择 project 和 session
- **THEN** viewer SHALL load the session data
- **AND** the active page SHALL render visible content
- **AND** page content SHALL NOT remain blank

### Requirement: Session 页面承接旧版日志展示
`Session` page SHALL migrate and preserve the previous local log viewer capability.

#### Scenario: Session 页面展示日志树和详情区
- **WHEN** 用户进入 `Session` 页面并已选择 session
- **THEN** 页面 SHALL 显示 turn tree / entry list
- **AND** 页面 SHALL 显示 entry detail panel
- **AND** 用户 SHALL be able to click an entry and inspect its raw/detail content

#### Scenario: Session 页面保留筛选和搜索
- **WHEN** 用户在 Session 页面查看日志
- **THEN** 页面 SHALL retain type filters
- **AND** 页面 SHALL respect the global search query for entries

#### Scenario: Session 页面为空时显示明确状态
- **WHEN** session 已加载但没有 entries
- **THEN** 页面 SHALL show a clear empty state
- **AND** SHALL NOT show an empty blank panel

#### Scenario: raw-events alias 跳转到 Session
- **WHEN** internal code navigates to `raw-events`
- **THEN** viewer SHALL route it to `Session`
- **AND** SHALL preserve canonical event focusing behavior

### Requirement: Tasks 页面承接任务切分
`Tasks` page SHALL provide task segmentation and task detail browsing for the current session.

#### Scenario: Tasks 页面无切分结果时显示 CTA
- **WHEN** 用户进入 `Tasks` 页面且当前 session 尚未加载
- **THEN** 页面 SHALL display a clear disabled state
- **AND** SHALL explain that a session must be selected first

#### Scenario: 已加载 session 后进入 Tasks 自动切分
- **WHEN** 用户已经选择并成功加载一个 session
- **AND** 当前 session 没有 task segmentation result
- **WHEN** 用户点击左侧 `Tasks`
- **THEN** viewer SHALL automatically request task segmentation for the current session
- **AND** 页面 SHALL show loading, success, or error state
- **AND** 页面 SHALL NOT remain blank

#### Scenario: Tasks 页面复用当前 session 切分缓存
- **WHEN** 当前 session already has a task segmentation result
- **AND** 用户点击左侧 `Tasks`
- **THEN** 页面 SHALL render cached Task List and Task Detail immediately
- **AND** SHALL NOT send an unnecessary duplicate segmentation request

#### Scenario: Tasks 页面展示 Task List 和 Task Detail
- **WHEN** task segmentation returns tasks
- **THEN** 页面 SHALL render Task List and Task Detail panes
- **AND** selecting a task SHALL update Task Detail

#### Scenario: 报告分析不阻塞任务切分
- **WHEN** a long-running session report analysis request is in progress
- **AND** 用户在 `Tasks` 页面触发 task segmentation
- **THEN** viewer server SHALL be able to process the task segmentation request without waiting for the analysis request to finish
- **AND** task segmentation SHALL NOT be serialized behind report generation by the HTTP server

#### Scenario: Task 卡片名称稳定
- **WHEN** task segmentation returns multiple tasks
- **THEN** task card title SHALL use a stable ordinal label such as `任务 1`, `任务 2`
- **AND** SHALL NOT display raw noisy event text, encoded payload fragments, or adapter-specific internal strings as the card title

#### Scenario: Task Detail 保留核心 tabs
- **WHEN** 用户查看 task detail
- **THEN** 页面 SHALL provide Overview, Evidence, Turns, Files & Diff, Commands, and Raw task tabs or equivalent sections

#### Scenario: Task evidence 跳转回 Session 页面
- **WHEN** 用户点击 task start/end/evidence navigation
- **THEN** viewer SHALL navigate to `Session`
- **AND** SHALL focus the corresponding entry when the target can be resolved
- **AND** SHALL show clear debug information when the target cannot be resolved

#### Scenario: Session 和 Tasks 往返切换不丢失页面
- **WHEN** 用户已加载 session 并停留在 `Session`
- **AND** 用户点击 `Tasks`
- **AND** 用户再点击 `Session`
- **THEN** `Session` 页面 SHALL restore the current session log list and detail area
- **AND** viewer SHALL have an active page
- **AND** 主工作区 SHALL NOT be blank

### Requirement: Session 报告分析入口
`Session` page SHALL expose the existing session report analysis workflow.

#### Scenario: Session 页面展示报告分析按钮
- **WHEN** 用户进入 `Session` 页面
- **THEN** 页面 SHALL show a report analysis button in the Session toolbar
- **AND** the button SHALL be disabled until the current session is loaded

#### Scenario: 报告分析复用已有链路
- **WHEN** 用户点击 Session 页面报告分析按钮
- **THEN** viewer SHALL open the existing report mode modal
- **AND** confirming the modal SHALL call the existing `/api/analyze` workflow
- **AND** report output SHALL be shown in the Session detail area
- **AND** viewer SHALL NOT navigate to a missing `evidence` page

### Requirement: 非核心页面降级
Non-core workbench pages SHALL NOT block the Session and Tasks migration.

#### Scenario: 非核心入口不伪装为已完成
- **WHEN** Overview, Timeline, Req / Resp, Diff, Diagnostics, Export, or Settings is visible
- **THEN** it SHALL either show a clear placeholder or a minimal existing entry point
- **AND** it SHALL NOT be required for this change's manual acceptance

### Requirement: 回归测试
The change SHALL include regression tests for the two core modules and navigation aliases.

#### Scenario: 静态结构测试
- **WHEN** tests inspect `viewer/claude-log.html`
- **THEN** they SHALL verify default `Session` navigation, `Tasks` navigation, and Session log container presence

#### Scenario: Session load tests
- **WHEN** tests inspect frontend session loading behavior
- **THEN** they SHALL verify `loadSession()` does not auto-jump away because task segmentation is missing
- **AND** it renders the current active page after session data loads

#### Scenario: Task navigation tests
- **WHEN** tests inspect task evidence navigation
- **THEN** they SHALL verify task navigation targets route to Session/raw-events alias and keep event focusing behavior

#### Scenario: Tasks 自动切分与往返测试
- **WHEN** DOM tests simulate loading a session and clicking `Tasks`
- **THEN** tests SHALL verify task segmentation is requested for the current session
- **AND** tests SHALL verify switching back to `Session` restores visible log content

#### Scenario: 并发和标题回归测试
- **WHEN** tests inspect viewer server construction
- **THEN** they SHALL verify the viewer uses a threaded HTTP server
- **WHEN** tests inspect task segmentation output
- **THEN** they SHALL verify task titles are stable ordinal labels

#### Scenario: 报告分析入口测试
- **WHEN** tests inspect frontend analysis behavior
- **THEN** they SHALL verify a visible Session report analysis button exists
- **AND** analysis code SHALL route report rendering to `Session`, not a missing `evidence` page
