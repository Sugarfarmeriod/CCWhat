## ADDED Requirements

### Requirement: Viewer 显示 session 名称
Viewer SHALL 在项目/session 选择器和已加载 session 的主标题区域显示可读 session 名称，并保留 session id 作为可识别信息。

#### Scenario: session 列表使用 displayName
- **WHEN** 前端调用 `GET /api/projects`
- **AND** 返回的 session entry 包含非空 `displayName`
- **THEN** session 选择器 SHALL 以 `displayName` 作为主要标签
- **AND** 该选项 SHALL 保留完整 session id 供用户识别或悬停查看

#### Scenario: 无名称时回退显示
- **WHEN** session entry 的 `title` 为空或缺失
- **THEN** Viewer SHALL 使用 adapter 返回的 `displayName` 或 session id fallback 展示该 session
- **AND** Viewer SHALL NOT 显示空白选项

#### Scenario: 已加载 session 显示名称
- **WHEN** 用户成功加载一个 session
- **THEN** Viewer SHALL 在当前 session 标题区域显示该 session 的 `displayName`
- **AND** Viewer SHALL 同时保留 session id 的可见或可复制信息

#### Scenario: 长名称紧凑展示
- **WHEN** session 名称超过选择器或标题区域可用宽度
- **THEN** Viewer SHALL 在紧凑区域截断显示
- **AND** Viewer SHALL 保留完整名称用于详情、悬停标题或编辑输入

#### Scenario: 同名 session 仍可区分
- **WHEN** 同一项目或跨项目中存在多个 `displayName` 相同或相近的 session
- **THEN** Viewer SHALL 在 selector option 或 session 标题区同时展示 session id 或其可识别前缀
- **AND** Viewer SHALL NOT 仅凭 `displayName` 让用户无法区分不同 session
- **AND** 用户定位/加载 session 时 Viewer SHALL 使用 session id 而非 `displayName`

### Requirement: Backend API rename session
Viewer server SHALL 提供 `POST /api/session/<sessionId>/rename`，用于修改当前 agent 的 session title，并只在 native 写回成功后返回成功。

#### Scenario: rename 成功
- **WHEN** 前端调用 `POST /api/session/<sessionId>/rename`
- **AND** 请求 JSON 包含非空 `title`
- **AND** 当前 agent adapter 支持 rename
- **AND** native title 写回成功
- **THEN** 后端 SHALL 返回 HTTP 200
- **AND** 响应 SHALL 包含 `ok: true`
- **AND** 响应 SHALL 包含 `agent`
- **AND** 响应 SHALL 包含 `sessionId`
- **AND** 响应 SHALL 包含更新后的 `title`
- **AND** 响应 SHALL 包含更新后的 `displayName`
- **AND** 响应 SHALL 包含 `canRenameSession: true`

#### Scenario: title 为空时拒绝
- **WHEN** rename 请求缺少 `title`
- **OR** `title` trim 后为空字符串
- **THEN** 后端 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 包含 `ok: false`
- **AND** 响应 SHALL 包含 `code: "invalid_title"`
- **AND** 后端 SHALL NOT 调用 adapter native 写回

#### Scenario: session 不存在时拒绝
- **WHEN** rename 请求中的 `sessionId` 在当前 agent 数据源中不存在
- **THEN** 后端 SHALL 返回 HTTP 404
- **AND** 响应 SHALL 包含 `ok: false`
- **AND** 响应 SHALL 包含 `code: "session_not_found"`

#### Scenario: agent 不支持 rename
- **WHEN** 当前 agent adapter 返回 `canRenameSession: false`
- **OR** adapter 报告 rename unsupported
- **THEN** 后端 SHALL 返回 HTTP 501
- **AND** 响应 SHALL 包含 `ok: false`
- **AND** 响应 SHALL 包含 `code: "rename_not_supported"`
- **AND** 后端 SHALL NOT 写入任何本地-only title 缓存伪造成功

#### Scenario: native title 不可用
- **WHEN** adapter 无法定位 native title 存储
- **OR** native schema 缺少 title 写回所需表或字段
- **THEN** 后端 SHALL 返回 HTTP 500
- **AND** 响应 SHALL 包含 `ok: false`
- **AND** 响应 SHALL 包含 `code: "native_title_unavailable"`
- **AND** Viewer SHALL 保留旧名称

#### Scenario: native title 写入失败
- **WHEN** adapter 写入 native title 时遇到只读 DB、DB lock、事务失败或其他 SQLite 写入错误
- **THEN** 后端 SHALL 返回 HTTP 500
- **AND** 响应 SHALL 包含 `ok: false`
- **AND** 响应 SHALL 包含 `code: "native_title_write_failed"`
- **AND** Viewer SHALL 保留旧名称

### Requirement: Frontend rename interaction
Viewer SHALL 为可 rename 的当前 session 提供名称编辑交互，并根据后端结果更新或保留界面状态。

#### Scenario: 可 rename session 显示编辑入口
- **WHEN** 当前已加载 session 的 metadata 包含 `canRenameSession: true`
- **THEN** Viewer SHALL 显示 session 名称编辑入口
- **AND** 编辑入口 SHALL 使用当前 `title` 或 `displayName` 初始化

#### Scenario: 不可 rename session 禁用编辑
- **WHEN** 当前已加载 session 的 metadata 包含 `canRenameSession: false`
- **THEN** Viewer SHALL 禁用或隐藏 session 名称编辑入口
- **AND** Viewer SHALL 展示该 agent 暂不支持 native rename 的明确状态

#### Scenario: 取消编辑不发请求
- **WHEN** 用户进入 session 名称编辑状态后取消
- **THEN** Viewer SHALL 退出编辑状态
- **AND** Viewer SHALL 保留原名称
- **AND** Viewer SHALL NOT 调用 rename API

#### Scenario: 保存中状态
- **WHEN** 用户提交新的 session 名称
- **THEN** Viewer SHALL 调用 `POST /api/session/<sessionId>/rename`
- **AND** 保存期间 SHALL 防止重复提交同一 rename 请求
- **AND** 保存期间 SHALL 显示明确的保存中状态

#### Scenario: 保存成功后刷新当前 UI
- **WHEN** rename API 返回成功响应
- **THEN** Viewer SHALL 使用响应中的 `title` 和 `displayName` 更新当前 session 标题区域
- **AND** Viewer SHALL 更新 session selector 当前 option
- **AND** Viewer SHALL 更新内存中的项目/session 列表数据
- **AND** Viewer SHALL 退出编辑状态并显示成功反馈

#### Scenario: 保存失败时保留旧名称
- **WHEN** rename API 返回非 2xx 响应或网络错误
- **THEN** Viewer SHALL 显示可读错误
- **AND** Viewer SHALL 保留提交前的 session 名称
- **AND** Viewer SHALL 允许用户修正名称后重试
