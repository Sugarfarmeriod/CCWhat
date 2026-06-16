## Context

CCWhat 现有多 agent adapter 已支持 Claude、Codex 和 OpenCode。Codex adapter 从 `~/.codex/sessions` 读取 rollout JSONL，并可从 `~/.codex/state_5.sqlite` 的 `threads` 表补充 metadata；OpenCode adapter 从 `~/.local/share/opencode/opencode.db` 读取 `session`、`message`、`part` 等表，且 session 列表中已经包含 `title`。Viewer 的项目/session 选择器仍主要展示 session id，当前 `AgentAdapter` interface 也没有受控 rename 能力。

本 change 只定义和实现 Codex/OpenCode session title 的显示与 native 写回，不改变日志解析模型，不新增 Claude Code native 同步。

## Goals / Non-Goals

**Goals:**

- Viewer 在 session 列表和当前 session 区域显示可读 session 名称。
- Viewer 允许用户修改当前 session 名称，并展示保存中、成功、失败、取消等状态。
- 后端新增 session rename API，由当前 agent adapter 处理。
- Codex rename 成功后写入 `~/.codex/state_5.sqlite` 的 `threads.title`。
- OpenCode rename 成功后写入 `~/.local/share/opencode/opencode.db` 的 `session.title`。
- adapter 层明确暴露 session 是否可 rename，避免前端猜测 agent 能力。
- 测试覆盖 metadata 展示、Codex/OpenCode 写回、错误处理和 Claude unsupported。

**Non-Goals:**

- 不实现 Claude Code native title 同步，不写入 `~/.claude/projects` 下的 JSONL。
- 不做跨 agent 批量 rename。
- 不做独立 session 管理页面、搜索索引或历史名称审计。
- 不改变 Codex rollout JSONL 或 OpenCode message/part 内容。
- 不修改 export/import 或 Dataset schema。

## Decisions

### Decision 1: adapter interface 增加显式 rename 能力

`AgentAdapter` 增加两个概念：

- session metadata 中返回 `title`、`displayName` 和 `canRenameSession`。
- adapter 提供受控 rename 方法，例如 `rename_session(session_id, title)`，返回更新后的 metadata 或抛出可映射为 HTTP 错误的异常。

原因：

- Viewer 不应根据 agent 名称硬编码是否可编辑。
- 后端 API 可以统一处理校验、错误响应和 UI 反馈。
- 后续 Claude Code spike 可以在同一接口下补实现。

替代方案是只在 `viewer/server.py` 中按 agent 分支写 SQLite。放弃原因是会绕过 adapter 边界，使 Codex/OpenCode 存储细节泄漏到 server。

### Decision 2: Viewer API 使用 `POST /api/session/<sessionId>/rename`

请求体：

```json
{
  "title": "新的会话名称"
}
```

成功响应：

```json
{
  "ok": true,
  "agent": "codex",
  "sessionId": "...",
  "title": "新的会话名称",
  "displayName": "新的会话名称",
  "canRenameSession": true
}
```

失败响应应包含 `ok: false`、`error` 和稳定 `code`，例如：

- `invalid_title`
- `session_not_found`
- `rename_not_supported`
- `native_title_unavailable`
- `native_title_write_failed`

原因：

- 当前 viewer server 已主要使用 GET/POST/OPTIONS，CORS 也只声明 GET/POST/OPTIONS；使用 POST 可以减少协议面变更。
- rename 是有副作用的明确操作，不适合塞进现有 `GET /api/session/<sessionId>`。

替代方案是 `PATCH /api/session/<sessionId>`。放弃原因是需要扩展 server method 和 CORS，且本项目现有 API 风格不依赖 PATCH。

### Decision 3: displayName 是展示字段，title 是 native 字段

adapter/API 应按以下口径返回：

- `title`: native 存储中的原始标题，可能为空字符串。
- `displayName`: Viewer 展示用名称；优先使用非空 `title`，否则回退到短 session id、cwd/project basename 或现有 session id 标签。Viewer 默认可见 UI 使用 `displayName` 作为主要标签，不再额外拼接 `[shortId]` 或显示 raw session id。
- `canRenameSession`: 当前 session 是否允许通过 Viewer 写回 native title。

`GET /api/projects` 中每个 session entry 和 `GET /api/session/<sessionId>` 的 loaded session metadata 都应包含这些字段。为了兼容现有代码，原有 `id`、`sessionId`、`projectDir`、`_metadata`、`events`、`turns` 等字段继续保留。

原因：

- 前端可以稳定使用 `displayName`，但不会把 fallback 误认为 native title。
- 测试可以区分“读取 title 成功”和“无 title 时正常降级展示”。

### Decision 4: Codex 以 `threads.title` 为唯一 native 写回目标

Codex rename 流程：

1. 校验 title trim 后非空。
2. 定位 `state_5.sqlite`，默认路径为 `~/.codex/state_5.sqlite`；测试可通过 adapter 内部路径或构造参数注入临时 DB。
3. 校验 `threads` 表存在，且至少包含 `id` 和 `title` 字段。
4. 在事务中执行 `UPDATE threads SET title = ? WHERE id = ?`。
5. 若影响行数为 0，返回 session/thread 不存在错误。
6. commit 后清理 adapter 的 SQLite metadata cache，并重新读取 metadata 返回给 API。

rename 不修改 rollout JSONL。读取 session 时即使 SQLite 不可用仍可展示 rollout 内容；但 rename 必须写入 SQLite，因此 SQLite 不可用时应失败并提示 native title 不可用。

### Decision 5: OpenCode 以 `session.title` 为唯一 native 写回目标

OpenCode rename 流程：

1. 校验 title trim 后非空。
2. 定位 OpenCode DB，沿用当前 adapter 对 `projects_dir` 的语义：可以是 DB 文件，也可以是 DB 所在目录。
3. 校验 `session` 表存在，且至少包含 `id` 和 `title` 字段。
4. 在线程锁保护下使用事务执行 `UPDATE session SET title = ? WHERE id = ?`。
5. 若影响行数为 0，返回 session 不存在错误。
6. commit 后重新读取 session metadata 返回给 API。

rename 不修改 `message`、`part` 或 `session_message`。如果 DB 被锁、只读或 schema 缺失，API 不得报告成功。

### Decision 6: Claude Code native 同步明确排除

Claude adapter 在本 change 中应返回 `canRenameSession: false`，rename API 对 Claude session 返回 `501` 或等价 unsupported 响应，`code` 为 `rename_not_supported`。

原因：

- Claude Code 的本地 JSONL 没有与 Codex/OpenCode 等价的明确 title 字段。
- 本阶段需求只要求保留为后续 spike，避免做本地-only 标题导致用户误以为已同步到 Claude Code。

### Decision 7: 前端成功后以服务端返回为准

前端 rename 成功后必须用 API 返回的 `title/displayName/canRenameSession` 更新：

- 当前 session 标题区。
- session selector 当前 option。
- 内存中的 `allProjects` 对应 session entry。

失败时保留旧名称，不得 optimistic 地当成已保存。取消编辑不发送请求。

### Decision 8: session id 保持唯一程序标识，title/displayName 只用于展示，默认可见 UI 不显示 session id

rename 只新增展示字段，不改变 session 的寻址模型：

- API 路径（`GET /api/session/<sessionId>`、`POST /api/session/<sessionId>/rename`）继续以 session id 为参数。
- adapter `load_session(session_id)` 继续以 session id 查找，不通过 title/displayName 解析目标。
- export/import 和 Dataset 引用继续存储 session id。
- 调试日志、错误响应、rename 成功/失败响应始终携带原始 `sessionId`。
- 当多个 session 的 displayName 相同或相近时，前端在 selector option / 标题区同时展示非 id 区分信息（如时间范围、agent、项目路径摘要），不再使用 raw session id 或 short session id 作为可见区分信息。
- Codex adapter 从 SQLite `threads.created_at` / `threads.updated_at` 向 session entry 的 `firstTimestamp` / `lastTimestamp` 传播时间，使同名 session 可通过时间区分。

原因：

- title 可重名、可被用户反复修改、可回退到 fallback 摘要，不能作为稳定主键。
- 用 displayName 作为查找键会让 export、API 和调试链路在 rename 后失效或错位。
- 保持 session id 为唯一标识是本次 rename 改造的安全边界，避免「改名导致会话无法加载」。
- 默认可见 UI 不显示 session id 可提升可读性；时间、项目路径等非 id 信息足以区分同名 session。

## Risks / Trade-offs

- [Risk] Codex `state_5.sqlite` schema 或 table 名随版本变化。→ Mitigation：写前检查 `threads.id/title`，缺失时返回清晰错误，不尝试猜测其他表。
- [Risk] OpenCode DB 被其他进程锁住。→ Mitigation：捕获 SQLite lock/write 错误，返回 `native_title_write_failed`，前端保留旧 title。
- [Risk] 成功写回后 adapter cache 仍显示旧 title。→ Mitigation：rename 成功后必须清理相关 metadata cache 或重新查询。
- [Risk] 长 title 影响 selector/topbar 布局。→ Mitigation：存储完整 title，紧凑 UI 中截断展示，并通过 `title` 属性或详情区保留完整值。
- [Risk] Claude 用户看到编辑入口但无法保存。→ Mitigation：前端依据 `canRenameSession` 禁用或隐藏编辑入口，并显示 unsupported 说明。

## Migration Plan

1. 扩展 adapter session metadata 和 rename interface。
2. 为 Codex/OpenCode adapter 实现 native title 写回。
3. 为 viewer server 增加 `POST /api/session/<sessionId>/rename`，并更新 `/api/projects` 与 `/api/session/<sessionId>` metadata。
4. 更新 Viewer 前端显示和编辑 session 名称。
5. 补充后端和前端测试。
6. 运行 adapter、viewer server、前端静态/DOM 相关测试以及 OpenSpec 校验。

本 change 不需要迁移已有数据。回滚时应仅移除 CCWhat rename API/UI 和 adapter rename 方法；已写入 native DB 的 title 是用户显式修改结果，不应由回滚自动还原。

## Open Questions

- Claude Code native title 的真实写回目标需要后续 spike 确认；本 change 不做假设。
- 是否需要后续为 rename 操作增加审计记录或 undo，本 change 不处理。
