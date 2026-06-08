## ADDED Requirements

### Requirement: LangSmith 风格工作台布局
系统 MUST 将 Agent Log Viewer 展示为 LangSmith 风格的深色诊断工作台，并保持 CCWhat 自身产品身份。

#### Scenario: 页面包含清晰工作台区域
- **WHEN** 用户打开 Agent Log Viewer
- **THEN** 页面必须包含左侧导航、顶部上下文操作栏、主日志/trace 区域和详情区域

#### Scenario: 不复制 LangSmith 品牌
- **WHEN** 页面采用 LangSmith 风格
- **THEN** 页面不得使用 LangSmith 名称、Logo、商标、专有文案或品牌资产

#### Scenario: 信息密度适合诊断
- **WHEN** 页面展示 project、session、turn、event 或 tool call
- **THEN** 页面必须优先使用紧凑表格、列表、badge、细边框和低圆角，而不是营销页式大卡片或大面积装饰

### Requirement: 多 Agent 上下文展示
系统 MUST 在重设计后的 Viewer 中明确展示当前 agent、project 和 session 上下文。

#### Scenario: 展示当前 agent
- **WHEN** Viewer 成功加载项目或 session 数据
- **THEN** 页面必须展示当前 agent 类型，并能区分 Claude Code、Codex 和 OpenCode

#### Scenario: 选择 project 和 session
- **WHEN** 后端返回项目和 session 列表
- **THEN** 页面必须允许用户选择 project 和 session，并保持现有加载流程可用

#### Scenario: Agent 数据为空
- **WHEN** 当前 agent 没有可展示 session
- **THEN** 页面必须显示清晰空状态，而不是只显示空白或无上下文的 failed to fetch

### Requirement: Trace / Turn / Event 展示
系统 MUST 支持以 tracing 工作流展示本地 Agent Log。

#### Scenario: 展示 normalized turns
- **WHEN** session 数据包含 `turns`
- **THEN** 页面必须能以 turn 为主展示用户输入、assistant 输出、工具调用、reasoning 和 usage 摘要

#### Scenario: 展示 normalized events
- **WHEN** session 数据没有可用 `turns` 但包含 `events`
- **THEN** 页面必须能以 event 列表展示 role、kind、summary、timestamp、toolName 和 usage 摘要

#### Scenario: 展示 Claude 兼容 main entries
- **WHEN** session 数据包含 Claude Code 的 `main`
- **THEN** 页面必须继续支持现有 Claude 原始日志展示能力

#### Scenario: 选择事件查看详情
- **WHEN** 用户点击 turn、event 或 Claude entry
- **THEN** 页面必须在详情区域展示 content、tool call、usage、metadata 和 raw JSON 中可获得的信息

### Requirement: Usage 和 Cache 展示约束
系统 MUST 展示本地日志中可获得的 token/cache 计数，并避免展示没有定义公式的 cache hit rate。

#### Scenario: 展示 usage 计数
- **WHEN** turn、event 或 session 数据包含 `usage`
- **THEN** 页面必须展示 input、output、reasoning、total、cache read、cache write、cache creation 或 cached input 中可获得的字段

#### Scenario: 不默认展示 cache hit rate
- **WHEN** usage 数据没有 `cacheHitRate` 和 `cacheHitRateFormula`
- **THEN** 页面不得默认展示 Cache 命中率

#### Scenario: 标注 usage 来源
- **WHEN** usage 数据包含 `source` 或 `scope`
- **THEN** 页面必须能展示或保留该来源信息，便于区分 agent log、network capture、merged 或 derived

### Requirement: Raw Req/Resp 页面独立
系统 MUST 保持 Raw Req/Resp 页面作为独立诊断入口。

#### Scenario: 提供 Raw Req/Resp 入口
- **WHEN** 用户在 Agent Log Viewer 中查看 session
- **THEN** 页面必须提供清晰的 Raw Req/Resp 跳转入口

#### Scenario: 不融合两个页面
- **WHEN** 本次重设计 Agent Log Viewer
- **THEN** 系统不得把 Raw Req/Resp 的请求响应列表直接融合进 Agent Log 主页面

### Requirement: 现有操作保留
系统 MUST 在重设计后保留现有 Viewer 的关键操作能力。

#### Scenario: 搜索和过滤可用
- **WHEN** 用户输入搜索词或切换类型过滤
- **THEN** 页面必须继续过滤当前 session 的可见日志项

#### Scenario: 导出可用
- **WHEN** 用户点击导出
- **THEN** 页面必须继续支持导出当前或所选 session 的日志和请求响应

#### Scenario: 分析入口可用
- **WHEN** 当前 session 可分析
- **THEN** 页面必须保留分析当前 Session 的入口和禁用状态逻辑

#### Scenario: 错误清晰
- **WHEN** API 加载失败或 adapter 返回错误
- **THEN** 页面必须显示清晰错误信息，并保留刷新或重新选择入口

### Requirement: 使用既有 Open Design 设计稿
系统 MUST 使用已经生成的 Open Design artifact 作为本次 Viewer 重设计的视觉和信息架构输入。

#### Scenario: 读取既有 artifact
- **WHEN** 执行 Agent 开始实现本 change
- **THEN** 必须优先读取 Open Design project `71acf6a9-38cc-40b4-bb00-f7200b01cdf4` 中的 `ccwhat-viewer.html`

#### Scenario: 不重复生成设计
- **WHEN** 用户没有明确要求重新设计
- **THEN** 执行 Agent 不得再次启动 Open Design 生成流程，只能消费既有设计稿并实现

#### Scenario: 设计稿作为参考而非替换
- **WHEN** 执行 Agent 将设计稿落地到 `viewer/claude-log.html`
- **THEN** 必须保留现有真实数据加载、session 展示、导出、搜索、过滤和 Raw Req/Resp 跳转逻辑，不得直接用静态 mock 页面替换现有 Viewer
