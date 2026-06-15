## 1. Adapter interface 与 metadata

- [x] 1.1 扩展 `AgentAdapter` rename 能力：定义 `rename_session(session_id, title)` 入口或等价接口，并定义 `rename_not_supported`、`native_title_unavailable`、`native_title_write_failed`、`session_not_found` 等可映射错误。
- [x] 1.2 增加统一 session title metadata 生成逻辑，确保 session entry 和 loaded session 都包含 `title`、`displayName`、`canRenameSession`。
- [x] 1.2.1 确保 session id 仍是所有程序路径（API、`load_session`、export/import、调试日志、错误响应）的唯一主键；`title/displayName` 仅用于展示，不作为查找键或持久化引用键。
- [x] 1.3 更新 Claude adapter：保留既有读取行为，返回 `canRenameSession: false`，rename 调用必须报告 unsupported，不写入 Claude JSONL 或本地-only title 缓存。
- [x] 1.4 更新 Codex/OpenCode adapter 返回字段，保持既有 `id`、`sessionId`、`projectDir`、`events`、`turns`、`usage` 和 `_metadata` 兼容。

## 2. Codex native title 写回

- [x] 2.1 更新 Codex session 列表和 loaded session metadata，从 `state_5.sqlite` 的 `threads.title` 读取 `title`，并优先作为 `displayName`。
- [x] 2.2 实现 Codex `rename_session`：定位 `~/.codex/state_5.sqlite`，校验 `threads.id/title` schema，在事务中执行 `UPDATE threads SET title = ? WHERE id = ?`。
- [x] 2.3 处理 Codex 错误分支：SQLite 缺失/不可读/不可写、`threads` schema 缺失、目标 row 不存在、DB lock 或 commit 失败。
- [x] 2.4 Codex rename 成功后清理或刷新 SQLite metadata cache，确保后续 `list_projects()`、`list_sessions()`、`load_session()` 返回新 title。
- [x] 2.5 确认 Codex rename 不修改 rollout JSONL、events、turns 或 usage 数据。

## 3. OpenCode native title 写回

- [x] 3.1 更新 OpenCode session 列表和 loaded session metadata，确保 `session.title` 同步到 `title/displayName`，并返回 `canRenameSession: true`。
- [x] 3.2 实现 OpenCode `rename_session`：沿用当前 DB 路径解析，在事务中执行 `UPDATE session SET title = ? WHERE id = ?`。
- [x] 3.3 处理 OpenCode 错误分支：DB 缺失/不可写、`session` schema 缺失、目标 row 不存在、DB lock 或 commit 失败。
- [x] 3.4 确认 OpenCode rename 不修改 `message`、`part`、`session_message`、usage 或 transcript 数据。

## 4. Viewer server API

- [x] 4.1 在 `viewer/server.py` 增加 `POST /api/session/<sessionId>/rename` 路由，解析 JSON body 并校验 `sessionId` 和 trim 后的 `title`。
- [x] 4.2 rename 前确认目标 session 存在，并通过当前 adapter 的 rename 能力执行 native 写回。
- [x] 4.3 成功响应返回 `ok`、`agent`、`sessionId`、`title`、`displayName`、`canRenameSession`。
- [x] 4.4 将 adapter 错误映射为稳定 HTTP 状态和 `code`：`invalid_title`、`session_not_found`、`rename_not_supported`、`native_title_unavailable`、`native_title_write_failed`。
- [x] 4.5 更新 `GET /api/projects` 和 `GET /api/session/<sessionId>` 的返回 metadata，确保前端无需按 agent 猜测 rename 能力。

## 5. Viewer 前端

- [x] 5.1 更新 session selector label：优先显示 `displayName`，并保留完整 session id 供悬停或识别。
- [x] 5.1.1 当多个 session `displayName` 相同或相近时，selector option 或标题区同时展示 session id 前缀，确保用户仍能区分；定位/加载 session 必须使用 session id。
- [x] 5.2 在已加载 session 的主标题区域显示 `displayName`、session id 和 rename 能力状态。
- [x] 5.3 为 `canRenameSession: true` 的 session 增加编辑入口、输入框、保存、取消和保存中状态。
- [x] 5.4 对 `canRenameSession: false` 的 session 禁用或隐藏编辑入口，并显示该 agent 暂不支持 native rename。
- [x] 5.5 保存成功后用 API 响应更新当前标题、session selector option 和 `allProjects` 内存数据。
- [x] 5.6 保存失败或网络错误时显示可读错误，保留旧名称，并允许用户修改后重试。
- [x] 5.7 处理长名称展示：紧凑区域截断，完整名称保留在详情、悬停标题或编辑输入中。

## 6. 测试覆盖

- [x] 6.1 新增/更新 adapter interface 测试，覆盖 `title/displayName/canRenameSession` 字段和 Claude rename unsupported。
- [x] 6.1.1 新增测试验证 session id 仍是 API、`load_session`、export 引用和错误响应中的唯一标识，rename 不把 `title/displayName` 提升为查找键。
- [x] 6.2 新增 Codex SQLite fixture 测试：读取 `threads.title`、成功写回、row 不存在、schema 缺失、DB 不可写或写入失败、cache 刷新。
- [x] 6.3 新增 OpenCode SQLite fixture 测试：读取 `session.title`、成功写回、row 不存在、schema 缺失、DB 不可写或写入失败。
- [x] 6.4 新增 viewer server API 测试：Codex/OpenCode rename 成功，invalid title 返回 400，session missing 返回 404，Claude unsupported 返回 501，native 写回失败返回稳定错误 code。
- [x] 6.5 新增前端静态或 DOM 冒烟测试：selector 使用 `displayName`、当前 session 标题存在、rename endpoint 调用存在、`canRenameSession` 控制编辑入口、成功/失败状态处理存在。
- [x] 6.6 运行既有 Codex/OpenCode adapter、viewer server、task segmentation/frontend 静态测试，确认非 rename 行为不回退。

## 7. 验证与交接

- [x] 7.1 运行 `pytest tests/test_adapters.py`。
- [x] 7.2 运行包含 rename API 的 viewer server 测试；如新增独立测试文件，运行该文件。
- [x] 7.3 运行前端静态/DOM 相关测试，至少覆盖 `tests/test_task_segmentation_frontend.py` 或新增 rename 前端测试。
- [x] 7.4 运行 `openspec validate rename-codex-opencode-sessions --strict`。
- [x] 7.5 在实现交接中明确 Claude Code native title 同步未实现，只作为后续 spike，不得在本 change 中补做。
