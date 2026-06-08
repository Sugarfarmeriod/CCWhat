## ADDED Requirements

### Requirement: Analyzer Agent 与 Observed Agent 分离
系统 MUST 区分被观察的 agent、读取日志的 Log Adapter 和生成报告的 Analyzer Adapter。

#### Scenario: target_args 不作为 analyzer command
- **WHEN** 用户运行 `ccwhat -- codex`、`ccwhat -- opencode` 或其他 target 命令
- **THEN** 系统必须只将 `target_args` 用于启动 observed agent，不得直接把 `target_args` 作为报告生成的 `analyzer_cmd`

#### Scenario: observed agent 仍用于选择 Log Adapter
- **WHEN** 用户运行 `ccwhat -- opencode`
- **THEN** 系统必须继续推断 observed agent 为 `opencode`，并使用 OpenCode Log Adapter 读取本地 session

#### Scenario: analyzer agent 可独立选择
- **WHEN** 报告生成开始
- **THEN** 系统必须通过 analyzer agent 或 analyzer command 配置选择 Analyzer Adapter，而不是直接复用 observed agent 的启动命令

### Requirement: Analyzer Registry
系统 MUST 提供 analyzer registry，用于规范化 analyzer 名称并返回对应协议配置。

#### Scenario: 选择 Claude analyzer
- **WHEN** analyzer agent 为 `claude` 或 `claude-code`
- **THEN** registry 必须返回 Claude analyzer 协议，默认命令为 `claude -p -`，输出模式为 `stdout`

#### Scenario: 选择 OpenCode analyzer
- **WHEN** analyzer agent 为 `opencode`、`open-code` 或 `open_code`
- **THEN** registry 必须返回 OpenCode analyzer 协议，默认命令为 `opencode run --format json`，输出模式为 `jsonl_text`

#### Scenario: 选择 Codex analyzer
- **WHEN** analyzer agent 为 `codex`
- **THEN** registry 必须返回 Codex analyzer 协议，并标注 `experimental: true`

#### Scenario: 未知 analyzer
- **WHEN** analyzer agent 未知
- **THEN** 系统必须返回清晰错误，说明该 analyzer 不受支持

### Requirement: Analyzer 命令配置优先级
系统 MUST 支持显式命令、环境变量和默认 analyzer 协议的优先级。

#### Scenario: 显式 analyzer command 优先
- **WHEN** 调用方显式传入 `analyzer_cmd`
- **THEN** 系统必须使用该命令，不再根据 analyzer agent 选择默认命令

#### Scenario: 环境变量 analyzer command 次优先
- **WHEN** 未显式传入 `analyzer_cmd` 且 `CCWHAT_ANALYZE_CMD` 存在
- **THEN** 系统必须解析并使用 `CCWHAT_ANALYZE_CMD`

#### Scenario: analyzer agent 环境变量
- **WHEN** 未显式传入 analyzer agent 且 `CCWHAT_ANALYZE_AGENT` 存在
- **THEN** 系统必须使用 `CCWHAT_ANALYZE_AGENT` 选择 Analyzer Adapter

#### Scenario: 默认 analyzer 可等于 observed agent
- **WHEN** 没有显式 analyzer 配置
- **THEN** 系统可以使用 observed agent 名称选择 Analyzer Adapter，但必须通过 analyzer registry 获取默认非交互协议，不得使用 `target_args`

### Requirement: Analyzer Timeout 配置
系统 MUST 支持 analyzer timeout 配置。

#### Scenario: 显式 timeout
- **WHEN** 调用方显式传入 `analyzer_timeout`
- **THEN** 系统必须使用该 timeout 运行 analyzer 子进程

#### Scenario: 环境变量 timeout
- **WHEN** 未显式传入 `analyzer_timeout` 且 `CCWHAT_ANALYZE_TIMEOUT` 为正整数
- **THEN** 系统必须使用该环境变量作为 timeout 秒数

#### Scenario: timeout 错误
- **WHEN** analyzer 子进程超过 timeout
- **THEN** 系统必须返回 `analyzer_timeout` 错误 code，并包含用户可理解的错误消息

### Requirement: Claude Analyzer 协议
系统 MUST 保持 Claude analyzer 的现有非交互能力。

#### Scenario: Claude stdout 输出
- **WHEN** 使用 Claude analyzer
- **THEN** 系统必须通过 stdin 传入 prompt，执行 `claude -p -`，并从 stdout 读取完整报告文本

#### Scenario: Claude 兼容回归
- **WHEN** 运行现有 Claude 报告分析测试
- **THEN** 测试必须继续通过

### Requirement: OpenCode Analyzer 协议
系统 MUST 支持 OpenCode 的非交互式报告生成协议。

#### Scenario: OpenCode 默认命令
- **WHEN** 使用 OpenCode analyzer 且未显式覆盖命令
- **THEN** 系统必须执行 `opencode run --format json`

#### Scenario: OpenCode prompt 走 stdin
- **WHEN** 使用 OpenCode analyzer
- **THEN** 系统必须通过 stdin 传入报告 prompt，而不是把超长 prompt 拼接成 shell 字符串

#### Scenario: OpenCode JSONL 文本提取
- **WHEN** OpenCode analyzer 输出 JSONL
- **THEN** 系统必须从 `type == "text"` 或 `part.type == "text"` 的事件中提取文本并拼接为最终报告

#### Scenario: OpenCode usage 元数据
- **WHEN** OpenCode JSONL 包含 `step_finish` 或 `part.type == "step-finish"` 且包含 tokens
- **THEN** 系统必须尽量保留 analyzer usage metadata，至少不影响报告文本返回

#### Scenario: 裸 opencode 不得作为默认 analyzer
- **WHEN** 用户通过 `ccwhat -- opencode` 启动 observed agent
- **THEN** 报告生成不得默认执行裸 `opencode`

### Requirement: Codex Analyzer 协议
系统 MUST 将 Codex analyzer 纳入协议层，并标记为 experimental。

#### Scenario: Codex experimental 标记
- **WHEN** 使用 Codex analyzer
- **THEN** 响应 metadata 或 analyzer spec 必须包含 `experimental: true`

#### Scenario: Codex JSONL 默认候选
- **WHEN** 使用 Codex analyzer 且未显式覆盖命令
- **THEN** 系统默认候选命令必须为 `codex exec --json --ephemeral --ignore-user-config -`

#### Scenario: Codex prompt 走 stdin
- **WHEN** 使用 Codex analyzer
- **THEN** 系统必须通过 stdin 传入报告 prompt

#### Scenario: Codex JSONL 文本提取
- **WHEN** Codex analyzer 输出 JSONL
- **THEN** 系统必须从 JSONL 中提取最终 assistant/agent 文本作为报告内容

#### Scenario: Codex last-message 备用协议
- **WHEN** 使用 Codex last-message 协议
- **THEN** 系统必须创建临时文件，执行 `codex exec --output-last-message <tmpfile> --ephemeral --ignore-user-config -`，并从临时文件读取最终报告文本

### Requirement: Analyze API 返回 Analyzer 状态
系统 MUST 在报告生成 API 响应中暴露 analyzer 状态，便于前端和用户理解失败原因。

#### Scenario: 成功返回 analyzer metadata
- **WHEN** `/api/analyze` 成功生成报告
- **THEN** 响应必须包含 analyzer agent、output mode、experimental 状态和 elapsed time 中可获得的信息

#### Scenario: 失败返回明确 code
- **WHEN** analyzer 命令不存在、协议不支持、输出为空、JSONL 无法解析或超时
- **THEN** 响应必须返回明确 code，例如 `analyzer_not_found`、`analyzer_not_supported`、`empty_report`、`analyzer_output_parse_error` 或 `analyzer_timeout`

### Requirement: Analyzer 测试
系统 MUST 为 Analyzer Adapter 协议补充测试。

#### Scenario: target_args 不进入 analyzer_cmd
- **WHEN** 测试模拟 `ccwhat -- opencode`
- **THEN** 必须验证 Viewer Server 收到的 analyzer command 不是 `("opencode",)` 或原始 target args

#### Scenario: OpenCode JSONL 解析
- **WHEN** 测试传入 OpenCode JSONL stdout，其中包含 text 事件和 step_finish tokens
- **THEN** parser 必须返回最终报告文本，并保留可用 usage metadata

#### Scenario: Codex JSONL 解析
- **WHEN** 测试传入 Codex JSONL stdout，其中包含最终 assistant/agent 文本事件
- **THEN** parser 必须返回最终报告文本

#### Scenario: Codex last-message 解析
- **WHEN** 测试使用 Codex last-message 输出模式
- **THEN** parser 必须从临时文件读取最终报告文本

#### Scenario: Claude 回归
- **WHEN** 运行现有 current session analysis 测试
- **THEN** Claude stdout analyzer 相关测试必须继续通过
