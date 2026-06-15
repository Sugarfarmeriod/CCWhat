## ADDED Requirements

### Requirement: Adapter 暴露 session title metadata
系统 MUST 通过 agent adapter 为 session 列表和已加载 session 暴露统一的 title metadata，供 Viewer 展示和判断是否可 rename。

#### Scenario: session 列表包含 title metadata
- **WHEN** 后端通过 adapter 构建 `GET /api/projects` 的 session entry
- **THEN** 每个 session entry MUST 保留原有 `id`
- **AND** 每个 session entry MUST 包含 `title`
- **AND** 每个 session entry MUST 包含 `displayName`
- **AND** 每个 session entry MUST 包含 `canRenameSession`

#### Scenario: loaded session 包含 title metadata
- **WHEN** 后端通过 adapter 读取 session 数据
- **THEN** 返回的 session 数据 MUST 包含 `sessionId`
- **AND** 返回的 session 数据 MUST 包含 `title`
- **AND** 返回的 session 数据 MUST 包含 `displayName`
- **AND** 返回的 session 数据 MUST 包含 `canRenameSession`
- **AND** 返回的 session 数据 MUST 保留既有 `_metadata` 字段中的 agent-specific metadata

#### Scenario: displayName fallback
- **WHEN** adapter 无法读取非空 native title
- **THEN** adapter MUST 返回空字符串 `title`
- **AND** adapter MUST 返回非空 `displayName`
- **AND** `displayName` MUST 基于 session id、项目目录或既有可读摘要生成，不得为空

#### Scenario: rename 能力不靠前端推断
- **WHEN** Viewer 需要判断当前 session 是否可 rename
- **THEN** Viewer MUST 使用 adapter/API 返回的 `canRenameSession`
- **AND** Viewer MUST NOT 仅根据 agent 字符串自行推断 rename 能力

### Requirement: Codex native title 写回
Codex adapter MUST 支持修改 Codex session title，并将修改同步写回 `~/.codex/state_5.sqlite` 的 `threads.title`。

#### Scenario: Codex list projects 读取 title
- **WHEN** `~/.codex/state_5.sqlite` 可读
- **AND** `threads` 表包含目标 session id 的 `title`
- **THEN** Codex adapter 的 session 列表 MUST 在对应 session entry 中返回该 `title`
- **AND** `displayName` MUST 优先使用该 `title`
- **AND** `canRenameSession` MUST 为 `true`

#### Scenario: Codex loaded session 读取 title
- **WHEN** `load_session(sessionId)` 读取到 Codex SQLite metadata 中的 `title`
- **THEN** 返回 session 数据 MUST 包含该 `title`
- **AND** 返回 session 数据 MUST 包含基于该 `title` 的 `displayName`
- **AND** 返回 session 数据 MUST 包含 `canRenameSession: true`

#### Scenario: Codex rename 写入 threads.title
- **WHEN** 调用 Codex adapter rename 方法
- **AND** `~/.codex/state_5.sqlite` 存在且可写
- **AND** `threads` 表包含字段 `id` 和 `title`
- **AND** `threads.id` 匹配目标 `sessionId`
- **THEN** adapter MUST 在 SQLite 事务中执行 `UPDATE threads SET title = ? WHERE id = ?`
- **AND** adapter MUST commit 成功后才报告 rename 成功
- **AND** adapter MUST 返回更新后的 `title` 和 `displayName`

#### Scenario: Codex session row 不存在
- **WHEN** Codex adapter rename 写入 `threads.title` 时影响行数为 0
- **THEN** adapter MUST 报告 session 不存在
- **AND** 后端 MUST 将该错误映射为 `code: "session_not_found"`

#### Scenario: Codex SQLite 不可用时 rename 失败
- **WHEN** Codex rollout JSONL 可读但 `~/.codex/state_5.sqlite` 不存在、不可读或不可写
- **THEN** Codex adapter MUST 仍允许读取 session 内容
- **AND** Codex adapter rename MUST 失败
- **AND** 后端 MUST 将该错误映射为 `code: "native_title_unavailable"` 或 `code: "native_title_write_failed"`

#### Scenario: Codex metadata cache 失效
- **WHEN** Codex adapter 成功写入 `threads.title`
- **THEN** adapter MUST 清理或刷新 SQLite metadata cache
- **AND** 后续 `list_projects()`、`list_sessions()` 和 `load_session()` MUST 返回新 title

### Requirement: OpenCode native title 写回
OpenCode adapter MUST 支持修改 OpenCode session title，并将修改同步写回 `~/.local/share/opencode/opencode.db` 的 `session.title`。

#### Scenario: OpenCode list projects 读取 title
- **WHEN** OpenCode DB 中 `session` 表包含目标 session 的 `title`
- **THEN** OpenCode adapter 的 session 列表 MUST 在对应 session entry 中返回该 `title`
- **AND** `displayName` MUST 优先使用该 `title`
- **AND** `canRenameSession` MUST 为 `true`

#### Scenario: OpenCode loaded session 读取 title
- **WHEN** `load_session(sessionId)` 读取到 OpenCode `session.title`
- **THEN** 返回 session 数据 MUST 包含该 `title`
- **AND** 返回 session 数据 MUST 包含基于该 `title` 的 `displayName`
- **AND** 返回 session 数据 MUST 包含 `canRenameSession: true`

#### Scenario: OpenCode rename 写入 session.title
- **WHEN** 调用 OpenCode adapter rename 方法
- **AND** OpenCode DB 存在且可写
- **AND** `session` 表包含字段 `id` 和 `title`
- **AND** `session.id` 匹配目标 `sessionId`
- **THEN** adapter MUST 在 SQLite 事务中执行 `UPDATE session SET title = ? WHERE id = ?`
- **AND** adapter MUST commit 成功后才报告 rename 成功
- **AND** adapter MUST 返回更新后的 `title` 和 `displayName`

#### Scenario: OpenCode session row 不存在
- **WHEN** OpenCode adapter rename 写入 `session.title` 时影响行数为 0
- **THEN** adapter MUST 报告 session 不存在
- **AND** 后端 MUST 将该错误映射为 `code: "session_not_found"`

#### Scenario: OpenCode DB schema 缺失
- **WHEN** OpenCode DB 缺少 `session` 表、`session.id` 字段或 `session.title` 字段
- **THEN** OpenCode adapter rename MUST 失败
- **AND** 后端 MUST 将该错误映射为 `code: "native_title_unavailable"`
- **AND** 系统 MUST NOT 静默创建替代表或本地-only title 存储

#### Scenario: OpenCode 写入失败
- **WHEN** OpenCode DB 只读、被锁或事务 commit 失败
- **THEN** OpenCode adapter rename MUST 失败
- **AND** 后端 MUST 将该错误映射为 `code: "native_title_write_failed"`
- **AND** 后续读取 MUST 保持 native DB 中的原 title

### Requirement: session id 保持唯一标识
系统 MUST 保持 session id 作为 session 的唯一程序标识，rename 引入的 `title` 和 `displayName` MUST 仅用于展示，不得取代 session id 成为任何程序路径的主键。

#### Scenario: API 继续以 session id 寻址
- **WHEN** 前端或外部调用 `GET /api/session/<sessionId>` 或 `POST /api/session/<sessionId>/rename`
- **THEN** 系统 MUST 以 session id 作为寻址主键
- **AND** 系统 MUST NOT 使用 `title` 或 `displayName` 作为 API 路径参数或查找键

#### Scenario: load session 继续使用 session id
- **WHEN** adapter 执行 `load_session(session_id)`
- **THEN** adapter MUST 以 session id 定位 session
- **AND** adapter MUST NOT 通过 `title` 或 `displayName` 解析目标 session

#### Scenario: export 继续使用 session id
- **WHEN** 导出或加载已导出 session 数据集
- **THEN** 导出标识 MUST 保留 session id
- **AND** 系统 MUST NOT 用 `title` 或 `displayName` 作为导出/导入或 Dataset 的唯一引用键

#### Scenario: 调试与重名区分使用 session id
- **WHEN** 两个或多个 session 拥有相同或相近的 `displayName`
- **THEN** 系统 MUST 能通过 session id 唯一区分这些 session
- **AND** 调试、日志、API 错误响应 MUST 携带 session id 而非 `displayName` 作为定位信息
- **AND** rename API 的成功/失败响应 MUST 始终包含原始 `sessionId`

#### Scenario: displayName 不得持久化为引用键
- **WHEN** 系统需要持久化对某 session 的引用
- **THEN** 持久化引用 MUST 存储 session id
- **AND** 持久化引用 MUST NOT 存储 `displayName` 或 `title` 作为查找键

### Requirement: Rename title 一致性
系统 MUST 保证 rename 成功响应与 native title 写回一致，避免 Viewer 显示本地伪成功。

#### Scenario: 成功前不更新为已保存
- **WHEN** adapter native 写回尚未成功 commit
- **THEN** 后端 MUST NOT 返回 `ok: true`
- **AND** 前端 MUST NOT 将新名称标记为已保存

#### Scenario: title trim 后写入
- **WHEN** rename 请求的 `title` 前后包含空白字符
- **THEN** 后端或 adapter MUST 使用 trim 后的 title 执行 native 写回
- **AND** 成功响应中的 `title` MUST 等于写入 native DB 的值

#### Scenario: 不修改非 title 数据
- **WHEN** Codex 或 OpenCode rename 成功
- **THEN** adapter MUST NOT 修改 session transcript、message、part、rollout JSONL 或 usage 字段
- **AND** adapter MUST 只修改 native title 所需字段

#### Scenario: 读取接口反映最新 title
- **WHEN** rename API 成功返回
- **THEN** 后续 `GET /api/projects` MUST 返回新 title
- **AND** 后续 `GET /api/session/<sessionId>` MUST 返回新 title

### Requirement: Claude Code native title 同步后续 spike
系统 MUST 明确排除 Claude Code native title 同步，本 change 不得向 Claude Code 日志写入 session title。

#### Scenario: Claude adapter 不支持 rename
- **WHEN** 当前 agent 为 Claude Code
- **THEN** adapter MUST 返回 `canRenameSession: false`
- **AND** rename API MUST 返回 `code: "rename_not_supported"`

#### Scenario: 不写入 Claude JSONL
- **WHEN** 用户尝试 rename Claude Code session
- **THEN** 系统 MUST NOT 修改 `~/.claude/projects` 下的 session JSONL
- **AND** 系统 MUST NOT 写入本地-only title 缓存伪造 native 同步

#### Scenario: 后续 spike 保留
- **WHEN** 用户需要 Claude Code native title 同步
- **THEN** 本 change 的设计和任务 MUST 将其记录为后续 spike
- **AND** Executor MUST NOT 在本 change 中实现 Claude Code native title 写回
