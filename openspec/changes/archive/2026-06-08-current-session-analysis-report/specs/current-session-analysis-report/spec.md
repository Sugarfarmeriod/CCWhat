## ADDED Requirements

### Requirement: 当前 session 分析接口
系统 SHALL 提供 `POST /api/analyze` 接口，用于对当前 Claude session 生成一次性分析报告。

#### Scenario: 成功分析当前 session
- **WHEN** 前端向 `/api/analyze` 提交有效 `sessionId`
- **THEN** 后端读取该 session 的 main 日志和 subagent 日志
- **AND** 使用 `deep_ai_analysis/assets/analyze_prompt.md` 模板构造完整 prompt
- **AND** 通过 `mc --code -p -` 从 stdin 注入 prompt
- **AND** 返回 JSON，包含 `ok: true`、`report` 和 `elapsedMs`

#### Scenario: session 不存在
- **WHEN** 前端向 `/api/analyze` 提交不存在的 `sessionId`
- **THEN** 接口以 404 响应
- **AND** 返回 JSON，包含 `ok: false` 和错误信息

#### Scenario: 请求范围限制为当前 session
- **WHEN** 前端调用 `/api/analyze`
- **THEN** 请求体 SHALL 只需要 `sessionId`
- **AND** 第一版 SHALL NOT 支持 turns、筛选结果、跨 session 或多 session 分析参数

### Requirement: 临时调用 mc 生成报告
后端 SHALL 临时调用本机 `mc` CLI 生成报告，不持久化分析对话或分析结果。

#### Scenario: mc 命令成功返回报告
- **WHEN** `mc --code -p -` 以退出码 0 返回非空 stdout
- **THEN** 接口返回 stdout 作为 `report`
- **AND** 不将报告写入 session 日志、导出包或缓存文件

#### Scenario: mc 命令不可用
- **WHEN** 本机找不到 `mc` 命令
- **THEN** 接口以 500 响应
- **AND** 返回 JSON，说明 `mc` 命令不可用

#### Scenario: mc 命令执行失败或超时
- **WHEN** `mc` 返回非零退出码、stdout 为空或执行超时
- **THEN** 接口以 500 响应
- **AND** 返回 JSON，包含可读错误信息

### Requirement: 前端展示并缓存当前 session 分析报告
Claude Log 页面 SHALL 提供当前 session 分析按钮，并在页面内展示临时报告。前端 SHALL 按 `sessionId` 在页面内存中缓存报告，以便用户在当前页面生命周期内反复查看。

#### Scenario: session 加载后可以启动分析
- **WHEN** 用户成功加载一个 session
- **THEN** 页面显示可点击的"分析当前 Session"按钮

#### Scenario: 分析进行中展示 loading
- **WHEN** 用户点击"分析当前 Session"
- **THEN** 前端向 `/api/analyze` 提交当前 `sessionId`
- **AND** 按钮进入 disabled 状态
- **AND** 页面展示分析中的状态

#### Scenario: 分析成功后展示报告
- **WHEN** `/api/analyze` 返回成功报告
- **THEN** 前端在页面内渲染该 Markdown 报告
- **AND** 报告保存到当前页面内存缓存，key 为当前 `sessionId`
- **AND** 报告不写入后端文件、session 日志、导出包或浏览器持久化存储

#### Scenario: 分析失败后展示错误
- **WHEN** `/api/analyze` 返回错误
- **THEN** 前端恢复按钮可点击状态
- **AND** 页面展示错误原因

#### Scenario: 点击日志详情后可以重新查看报告
- **WHEN** 当前 session 已生成分析报告
- **AND** 用户点击左侧任意日志条目使 detail panel 显示日志详情
- **THEN** 分析报告仍保留在前端内存缓存中
- **AND** 页面主按钮显示"查看分析报告"
- **AND** 用户点击该按钮后 detail panel 重新显示缓存报告

#### Scenario: 切换 session 时按 session 恢复报告状态
- **WHEN** 用户切换到另一个 session
- **THEN** 页面 SHALL 根据该 session 是否已有缓存报告更新主按钮文案
- **AND** 若该 session 已有缓存报告，点击"查看分析报告"可恢复报告
- **AND** 若该 session 没有缓存报告，主按钮显示"分析当前 Session"

#### Scenario: 刷新页面后报告可以丢弃
- **WHEN** 用户刷新浏览器页面
- **THEN** 前端内存缓存可以清空
- **AND** 页面不要求恢复刷新前生成的分析报告

### Requirement: 当前 session 报告支持重新分析
Claude Log 页面 SHALL 允许用户对已有报告的当前 session 重新发起分析，并用成功的新报告替换旧报告。

#### Scenario: 已有报告时可以重新分析
- **WHEN** 当前 session 已生成分析报告
- **THEN** 报告视图中显示"重新分析"入口

#### Scenario: 重新分析成功后覆盖旧报告
- **WHEN** 用户点击"重新分析"
- **AND** `/api/analyze` 返回新的成功报告
- **THEN** 前端用新报告覆盖当前 session 的旧缓存报告
- **AND** 页面显示新报告及新的生成时间

#### Scenario: 重新分析失败时保留旧报告
- **WHEN** 用户点击"重新分析"
- **AND** `/api/analyze` 返回错误
- **THEN** 前端保留当前 session 的旧缓存报告
- **AND** 页面展示重新分析失败原因

### Requirement: 当前 session 分析报告 Markdown 渲染
Claude Log 页面 SHALL 将当前 session 分析报告渲染为可读的 Markdown 报告视图，而不是展示未格式化的 Markdown 源文本。

#### Scenario: 分析报告包含结构化 Markdown
- **WHEN** `/api/analyze` 返回包含标题、段落、列表、表格和代码块的报告
- **THEN** 前端报告视图渲染对应的标题、段落、列表、表格和代码块元素
- **AND** 表格具备表头、边框和横向滚动能力

#### Scenario: 分析报告包含 Mermaid 代码块
- **WHEN** 报告包含 fenced code block 且语言为 `mermaid`
- **THEN** 前端 SHALL 在 Mermaid 渲染库可用时将其渲染为 Mermaid 图形
- **AND** Mermaid 源内容 SHALL 先作为文本转义写入页面，不能执行报告中的 HTML 或脚本

#### Scenario: Mermaid 渲染不可用或失败
- **WHEN** 报告包含 Mermaid 代码块
- **AND** Mermaid 渲染库不可用或渲染失败
- **THEN** 前端 SHALL 回退为带语言标签的可读代码块

#### Scenario: Markdown 内容包含 HTML 特殊字符
- **WHEN** 报告正文或代码块包含 `<`、`>` 或 `&`
- **THEN** 前端 SHALL 转义这些字符
- **AND** 不执行报告中的 HTML 或脚本
