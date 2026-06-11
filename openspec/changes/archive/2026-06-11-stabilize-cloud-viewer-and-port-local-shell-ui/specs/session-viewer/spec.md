## ADDED Requirements

### Requirement: Viewer 初始化入口唯一且非递归
`viewer/claude-log.html` SHALL 只有一个真实页面初始化入口，页面打开后 SHALL 自动加载项目列表并初始化 workbench 状态。初始化流程 MUST NOT 通过函数声明提升导致 `init()` 调用自身。

#### Scenario: 页面自动初始化
- **WHEN** 用户打开 viewer 页面
- **THEN** 前端调用项目列表加载逻辑
- **AND** 页面不会出现 `Maximum call stack size exceeded`

#### Scenario: 初始化函数非递归
- **WHEN** 前端测试执行 `init()`
- **THEN** `init()` 至多进入一次顶层初始化流程
- **AND** 不会通过 `_origInit` 或等价包装调用自身

### Requirement: Viewer 默认进入 Session 页面
Workbench SHALL 默认展示 `Session` 页面，`Session` 页面内部展示当前 session 的 turns/events 列表和详情。选择或加载 session 后，前端 SHALL 刷新当前页面，但 MUST NOT 自动跳转到 `Tasks` 页面。

#### Scenario: 首屏默认 Session
- **WHEN** viewer 初次加载完成
- **THEN** 左侧导航中 `Session` 处于 active 状态
- **AND** 主工作区展示 session/raw events 相关内容或选择 session 的提示

#### Scenario: 加载 session 不自动进入 Tasks
- **WHEN** 用户选择一个 session 并完成加载
- **THEN** 当前页面仍为 `Session`
- **AND** `Tasks` 页面不会自动运行任务切分

### Requirement: Tasks 页面由用户手动进入
`Tasks` 页面 SHALL 作为左侧一级导航入口存在。任务切分 SHALL 仅在用户点击 `Tasks` 页面或任务切分按钮后触发或展示缓存结果。

#### Scenario: 用户点击 Tasks
- **WHEN** 用户点击左侧 `Tasks`
- **THEN** 主工作区切换到 `Tasks` 页面
- **AND** 若当前 session 已加载，页面展示任务切分入口、加载状态、缓存结果或任务列表

#### Scenario: 未加载 session 时点击 Tasks
- **WHEN** 用户尚未选择 session 并点击 `Tasks`
- **THEN** 页面显示需要先选择 session 的提示
- **AND** 不发送 `/api/task-segments` 请求

### Requirement: 左侧导航作为一级功能入口
Viewer SHALL 使用左侧一级导航展示产品级功能入口，而不是把全局左栏固定为 turn 树。导航 SHALL 至少包含 `Session`、`Tasks`、`Overview`、`Timeline`、`Req / Resp`、`Diff`、`Diagnostics`、`Export`、`Settings`。

#### Scenario: 左侧导航入口齐全
- **WHEN** viewer 页面渲染完成
- **THEN** 左侧导航展示所有 required 功能入口
- **AND** turn/event 列表只在 `Session` 页面内部展示

#### Scenario: 未完成页面有占位
- **WHEN** 用户点击尚未完整实现的数据页面
- **THEN** 主工作区显示清晰的开发中、空状态或需要选择 session 的占位
- **AND** 页面不能空白

### Requirement: 本地 App Shell 视觉迁移
Viewer SHALL 采用本地 App Shell 的视觉方向：左侧导航分组、顶部上下文栏、紧凑按钮、开发者工具风格和高信息密度布局。该视觉迁移 MUST NOT 改变云端已有的数据加载、server、adapter 和 task segmentation API 行为。

#### Scenario: 顶部只承载全局上下文
- **WHEN** viewer 页面渲染完成
- **THEN** 顶部区域展示 Agent、Project、Session、Search、Refresh 等全局上下文控件
- **AND** 页面级操作放在对应页面内部

#### Scenario: 不直接复制设计稿
- **WHEN** 实现 App Shell 视觉迁移
- **THEN** 页面使用真实 API 和当前 viewer 状态
- **AND** 不以静态设计稿或 mock 数据替代真实 session 数据

### Requirement: Agent badge 使用真实 agent
Viewer 的 agent badge SHALL 从后端返回的真实 agent 信息设置。初始 DOM MAY 使用中性占位，但加载完成后 MUST NOT 硬编码为 `claude`，除非后端真实返回的 agent 就是 `claude`。

#### Scenario: 显示真实 agent
- **WHEN** `/api/projects` 或 `/api/viewer/status` 返回 `agent: "opencode"`
- **THEN** agent badge 显示 `opencode`
- **AND** 不显示硬编码的 `claude`

### Requirement: 任务证据定位保持稳定
Task 详情中的开始事件、结束事件、命令、错误和其他 evidence 跳转 SHALL 使用 canonical navigation target 定位到 `Session` 页面内部的对应 turn/event。视觉迁移 MUST NOT 破坏已有 `startEventId` / `endEventId` 定位能力。

#### Scenario: 定位开始事件
- **WHEN** 用户在 Task 详情点击定位开始事件
- **THEN** workbench 切换或保持在 `Session` 页面
- **AND** 左侧或页面内部的对应 turn/event 被滚动到可见位置并高亮

#### Scenario: 未知事件显示可解释状态
- **WHEN** Task evidence 的 event id 无法映射到当前 session entries
- **THEN** 定位按钮禁用或显示无法定位的提示
- **AND** 不抛出 JavaScript 异常
