## ADDED Requirements

### Requirement: Adapter 接口
系统 MUST 提供多 Coding Agent 日志 adapter 接口，用于统一描述 agent 名称、默认项目目录、项目列表、session 列表、session 读取、原始事件转换和 normalized event/turn 输出入口。

#### Scenario: Adapter 暴露统一能力
- **WHEN** 后端需要读取某个 agent 的历史会话
- **THEN** 系统必须通过 adapter 接口调用项目和 session 读取能力，而不是在 viewer server 中直接硬编码 agent 的目录结构

#### Scenario: 原始事件可降级保留
- **WHEN** adapter 读取到无法完整标准化的日志事件
- **THEN** 系统必须保留原始 JSON 数据，使 viewer 或后续导出逻辑仍可降级展示原始内容

#### Scenario: Adapter 输出 normalized events
- **WHEN** adapter 成功读取 session 数据
- **THEN** 系统必须在 session 数据中提供 `events` 字段，用于承载通用 Agent Log 展示模型

### Requirement: Claude Code Adapter
系统 MUST 实现 Claude Code adapter，并保持现有 Claude Code 会话展示能力不回退。

#### Scenario: 列出 Claude 项目和会话
- **WHEN** Claude Code projects 目录中存在项目子目录和 UUID 命名的 `.jsonl` session 文件
- **THEN** Claude adapter 必须返回包含 `agent: "claude"`、`projectDir` 和 `sessions` 的前端兼容项目列表

#### Scenario: 忽略非 session 文件
- **WHEN** Claude Code projects 目录中存在非 UUID 命名的 `.jsonl` 文件或其他文件
- **THEN** Claude adapter 必须忽略这些文件，不把它们作为 session 返回

#### Scenario: 读取 Claude session
- **WHEN** 请求读取一个存在的 Claude Code session id
- **THEN** Claude adapter 必须返回包含 `agent: "claude"`、`sessionId`、`projectDir`、`main`、`subagents` 和 `events` 的前端兼容 session 数据

#### Scenario: 读取 Claude subagents
- **WHEN** Claude session 目录下存在 `subagents/agent-*.jsonl` 和对应 `.meta.json`
- **THEN** Claude adapter 必须返回 subagent 的 `agentId`、`meta` 和 `entries`

#### Scenario: JSONL 解析失败降级
- **WHEN** Claude JSONL 文件中存在无法解析的行
- **THEN** Claude adapter 必须跳过该行并继续读取其他合法行，不得导致整个 session 读取失败

### Requirement: Normalized Event 和 Turn 模型
系统 MUST 为 Agent Log 页面定义轻量 normalized event/turn 模型，用于后续统一展示 Claude、Codex 和 OpenCode 的本地会话日志。

#### Scenario: Event 表示原子记录
- **WHEN** adapter 清洗用户消息、assistant 消息、工具调用、工具结果、reasoning、metadata 或 error
- **THEN** 系统必须将其表示为 normalized event，并包含 `agent`、`sessionId`、`timestamp`、`role`、`kind`、`content`、`summary`、`toolName`、`toolCallId`、`parentId`、`usage` 和 `raw` 中可获得的字段

#### Scenario: Turn 表示展示聚合
- **WHEN** 系统能识别同一轮用户输入及其后续 assistant 输出、工具调用和工具结果
- **THEN** 系统必须能将这些 events 聚合为 normalized turn，用于前端展示一轮 Agent 行为

#### Scenario: 不伪装 Claude 字段
- **WHEN** Codex 或 OpenCode adapter 后续实现
- **THEN** 系统不得把 Codex 或 OpenCode 原始记录伪装成 Claude 的 `message.content` 结构，必须通过 `events` 和 `turns` 表达通用展示数据

### Requirement: Usage 字段
系统 MUST 使用 CCWhat 通用 usage 字段表达 token 和 cache 计数，并标注字段来源和粒度。

#### Scenario: 本地日志 usage 映射
- **WHEN** 本地 agent 日志或数据库提供 token/cache 计数
- **THEN** adapter 必须优先映射到 `inputTokens`、`outputTokens`、`reasoningTokens`、`totalTokens`、`cacheReadTokens`、`cacheWriteTokens`、`cacheCreationTokens` 或 `cachedInputTokens`

#### Scenario: Usage 来源标注
- **WHEN** 系统返回 usage 数据
- **THEN** usage 必须包含 `scope` 和 `source`，用于标注该数据来自 event、turn 或 session 层级，以及来自 agent log、network capture、merged、derived 或 unknown

#### Scenario: 缺失 usage 不伪造
- **WHEN** 本地日志和可关联网络抓包都没有提供某个 usage 字段
- **THEN** 系统必须将该字段保留为空或 unknown，不得伪造数值

#### Scenario: 网络抓包作为补充
- **WHEN** 网络抓包记录能通过 session id、message id 或 turn id 与本地日志关联
- **THEN** 系统可以用网络抓包 usage 补充本地日志缺失字段，并必须将 `source` 标注为 `network_capture` 或 `merged`

#### Scenario: Cache 命中率必须是派生字段
- **WHEN** 系统展示 `cacheHitRate`
- **THEN** 系统必须同时提供 `cacheHitRateFormula`，并将 usage 来源标注为 `derived`

#### Scenario: 未定义公式时不展示 Cache 命中率
- **WHEN** CCWhat 未定义明确的 cache 命中率计算公式
- **THEN** 系统不得默认展示 `cacheHitRate`，应只展示 cache token 计数

### Requirement: Agent Registry
系统 MUST 提供 agent registry，用于规范化 agent 名称并选择对应 adapter。

#### Scenario: 选择 Claude adapter
- **WHEN** 用户指定 `claude` 或 `claude-code`
- **THEN** registry 必须返回 Claude adapter

#### Scenario: 标记 Codex 预留状态
- **WHEN** 用户指定 `codex`
- **THEN** registry 必须识别该 agent 名称，并返回清晰的未实现状态或错误，不得假设 Codex 日志格式与 Claude 相同

#### Scenario: 标记 OpenCode 预留状态
- **WHEN** 用户指定 `opencode`、`open-code` 或 `open_code`
- **THEN** registry 必须识别该 agent 名称，并返回清晰的未实现状态或错误，不得假设 OpenCode 日志格式与 Claude 相同

#### Scenario: 未知 agent
- **WHEN** 用户指定未知 agent 名称
- **THEN** registry 必须返回清晰错误，说明该 agent 不受支持

### Requirement: Web 命令 Agent 参数
系统 MUST 让 `ccwhat web` 支持按 agent 选择 viewer 日志 adapter，并保留显式项目目录覆盖能力。

#### Scenario: 使用 Claude agent 默认目录
- **WHEN** 用户运行 `ccwhat web --agent claude` 且未传入 `--projects-dir`
- **THEN** 系统必须使用 Claude adapter 的默认 projects 目录启动 viewer

#### Scenario: 显式 projects-dir 优先
- **WHEN** 用户运行 `ccwhat web --agent claude --projects-dir <path>`
- **THEN** 系统必须使用用户传入的 `<path>`，而不是 Claude adapter 的默认 projects 目录

#### Scenario: Web 命令遇到未实现 agent
- **WHEN** 用户运行 `ccwhat web --agent codex` 或 `ccwhat web --agent opencode`
- **THEN** 系统必须给出清晰错误提示，说明该 agent 的日志 adapter 尚未实现

### Requirement: Run 模式 Agent 推断
系统 MUST 在 `ccwhat -- <target>` 启动模式下根据目标命令推断 agent 类型，并把该类型传给 viewer 后端。

#### Scenario: 推断 Claude
- **WHEN** 用户运行 `ccwhat -- claude` 或 `ccwhat -- claude-code`
- **THEN** 系统必须推断 agent 为 `claude`

#### Scenario: 推断 Codex
- **WHEN** 用户运行 `ccwhat -- codex`
- **THEN** 系统必须推断 agent 为 `codex`

#### Scenario: 推断 OpenCode
- **WHEN** 用户运行 `ccwhat -- opencode`、`ccwhat -- open-code` 或 `ccwhat -- open_code`
- **THEN** 系统必须推断 agent 为 `opencode`

#### Scenario: 未实现 agent 不阻塞目标命令
- **WHEN** 用户通过 run 模式启动尚未实现日志 adapter 的 agent
- **THEN** 系统必须避免因 viewer adapter 未实现而使目标命令崩溃，并必须输出清晰 warning 或 fallback 提示

### Requirement: Viewer API 兼容性
系统 MUST 通过 adapter 改造 viewer API，同时保持现有前端所需字段兼容。

#### Scenario: Projects API 返回 agent
- **WHEN** 前端请求 `/api/projects`
- **THEN** 系统必须返回包含 agent 信息的项目列表，同时保留 `projectDir` 和 `sessions` 字段

#### Scenario: Session API 返回 agent
- **WHEN** 前端请求 `/api/session/<sessionId>`
- **THEN** 系统必须返回包含 agent 信息的 session 数据，同时保留 `sessionId`、`projectDir`、`main` 和 `subagents` 字段，并提供 `events` 字段

#### Scenario: Adapter 不支持时返回明确错误
- **WHEN** viewer 后端无法为当前 agent 提供 session 数据
- **THEN** API 必须返回明确错误，前端必须能展示该错误

### Requirement: 前端最小改动
系统 MUST 在 viewer 页面展示当前 agent 类型和 adapter 错误状态，同时保持现有 session 展示、搜索、导出和分析入口尽量不变。

#### Scenario: 展示当前 agent
- **WHEN** viewer 成功加载项目或 session 数据
- **THEN** 页面必须展示当前 agent 类型

#### Scenario: 展示 adapter 错误
- **WHEN** viewer API 返回 agent adapter 不支持或未实现错误
- **THEN** 页面必须展示清晰错误信息

#### Scenario: 不合并 Req/Resp 页面
- **WHEN** 实现多 Agent Log Adapter v0.1
- **THEN** 系统必须保持 Agent Log 页面和 Req/Resp 页面独立，不得把两个页面融合成一个页面

### Requirement: 回归测试
系统 MUST 补充测试覆盖多 agent adapter 架构，并保证既有导出导入能力不被破坏。

#### Scenario: Adapter 测试覆盖 Claude
- **WHEN** 测试使用临时 Claude projects 目录和 session 文件
- **THEN** 测试必须验证 Claude adapter 能列出 session 并读取 session 数据

#### Scenario: Registry 测试覆盖预留 agent
- **WHEN** 测试请求 `claude`、`codex` 和 `opencode`
- **THEN** 测试必须验证 registry 返回正确 adapter 或明确未实现状态

#### Scenario: CLI 测试覆盖参数优先级
- **WHEN** 测试运行 `ccwhat web --agent claude` 和显式 `--projects-dir`
- **THEN** 测试必须验证 agent 默认路径和显式路径优先级符合要求

#### Scenario: 现有导出导入测试继续通过
- **WHEN** 运行现有 export/import 相关测试
- **THEN** 测试必须继续通过，证明 Claude Code 兼容路径未回退
