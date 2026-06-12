## 1. 上下文确认

- [x] 1.1 阅读 `docs/turn-display-redesign.md` 中 Change 3 的目标，确认本 change 只做 Detail 完整性与调试筛选。
- [x] 1.2 阅读已归档 `turn-view-mode-projection` 和 `trace-tree-dual-view-ui`，确认 Step/Turn projection、`underlyingTurnKey`、`traceViewMode` 的现有行为。
- [x] 1.3 梳理 `viewer/claude-log.html` 中 `selectTraceNode()`、`renderTurnDetailInPanel()`、`buildTurnDetailHtml()`、`buildMinimalTurnDetailHtml()`、`renderAgentResponseContent()`。
- [x] 1.4 明确不修改后端 API、不修改 Task segmentation 算法、不实现 Task 编辑器、不改变左侧 projection 分类。
- [x] 1.5 梳理当前 Task-first 回归：确认 `buildTraceNodes()` 和 `getProjectionSource()` 是否只消费 confirmed task data。

## 2. Task-first Trace 闭环

- [x] 2.1 新增或整理 active task source helper，优先使用 confirmed task data，否则使用当前 session 的 cached/generated task segmentation result。
- [x] 2.2 修改 `getProjectionSource()`，让 projection 在有 active task data 时消费 `taskNodes`。
- [x] 2.3 修改 `buildTraceNodes()`，让 Session Trace 在有 active task data 时渲染 `Task -> 会话 -> Step/Turn`，确认状态只影响 UI badge。
- [x] 2.4 确保 unassigned conversations 在 Task-first 下仍有 projection，可展开为默认视图 Step 或调试视图 Turn。
- [x] 2.5 任务切分成功或重新切分后刷新 Session Trace，并展开 Task 节点。
- [x] 2.6 修复 OpenCode/Codex adapter normalized event id 随机生成问题，确保 `/api/session` 与 `/api/task-segments` 多次读取同一 session 时 Task 边界能稳定映射回 Trace Turn。

## 3. 移除 Detail 对左侧筛选的依赖

- [x] 3.1 修改 Minimal Turn Detail 渲染路径，确保 `buildMinimalTurnDetailHtml()` 不因 `entryMatchesFilter(e)` 为 false 而提前返回隐藏提示。
- [x] 3.2 保留左侧调试筛选对 Trace 树节点可见性的影响，但不让它影响已选中 Turn 的右侧 Detail。
- [x] 3.3 检查 legacy Turn Detail 路径，如仍被使用，避免右侧 Detail 只展示 `visibleTurnEntries` 而丢失完整 raw entries。
- [x] 3.4 切换默认视图 / 调试视图后，如果选中节点仍可见，Detail 不应被清空或降级为摘要。

## 4. 构建完整证据渲染 helper

- [x] 4.1 新增或整理 `buildTurnEvidenceModel(turn, entry)` 或等价 helper，收集 turn、entry、content block、metadata、anchor 信息。
- [x] 4.2 新增或整理 `renderTurnEvidenceSections(model)` 或等价 helper，统一渲染主证据区域。
- [x] 4.3 新增或整理 `renderRawEvidenceJson(model)` 或等价 helper，确保 raw JSON 包含 entry 核心字段和 content block。
- [x] 4.4 Detail header 中展示 turn label、kind、conversation key/group id、entry index、file line、block anchor 等可用定位信息。

## 5. 各类 Turn 的完整 Detail

- [x] 5.1 `user_message` Detail 展示完整用户文本和原始 content。
- [x] 5.2 `assistant_text` Detail 展示完整文本，不使用左侧 summary 截断。
- [x] 5.3 `thinking` Detail 展示完整 thinking/reasoning 内容，不摘要、不弱化为单行。
- [x] 5.4 `tool_use` Detail 展示工具名、完整 id/tool_use_id、完整 input JSON、content block raw JSON。
- [x] 5.5 `tool_result` Detail 展示完整 result content、`tool_use_id`、`is_error`，长结果用滚动或折叠控制布局，不截断内容。
- [x] 5.6 `context`、`system`、`unknown` Detail 展示可提取文本或 structured payload，并始终提供 raw JSON fallback。
- [x] 5.7 `permission-mode`、`file-history-snapshot`、`queue-operation` 等 internal entry 展示完整结构化字段和 raw JSON。

## 6. Step 与 Turn 选择一致性

- [x] 6.1 默认视图 Step 点击时，通过 `underlyingTurnKey` 定位底层 Minimal Turn，并复用同一套 Detail 渲染。
- [x] 6.2 调试视图 Turn 点击时，展示同一底层 Minimal Turn 的完整 Detail。
- [x] 6.3 同一 underlying Turn 在默认视图 Step 和调试视图 Turn 中打开时，主证据内容保持一致。
- [x] 6.4 如果某 selected internal Turn 切回默认视图后不可见，保留已有回退提示，但不删除底层证据能力。

## 7. 样式与可读性

- [x] 7.1 为长文本、tool input、tool result、raw JSON 使用可滚动或可折叠容器，避免撑破右侧面板。
- [x] 7.2 保持当前 LangSmith-like workbench 风格，不引入大面积新视觉设计。
- [x] 7.3 Detail 中的定位 metadata 使用轻量 badge 或 key/value 行，避免遮挡主证据。

## 8. 测试

- [x] 8.1 更新前端静态测试，断言存在 active task source helper，且 `getProjectionSource()` / `buildTraceNodes()` 消费 active task data 而不是 confirmed-only data。
- [x] 8.2 更新 DOM 测试：任务切分成功但未确认时，Session Trace 已经以 Task 作为一级节点。
- [x] 8.3 更新 DOM 测试：Task-first 下 Unassigned 会话可展开，并显示 Step/Turn。
- [x] 8.4 更新前端静态测试，断言 Detail 渲染不再依赖 `entryMatchesFilter()` 的提前返回裁剪逻辑。
- [x] 8.5 更新前端静态测试，断言存在完整证据 helper 或等价结构化渲染函数。
- [x] 8.6 更新 DOM 测试：默认视图点击 tool_use Step 后，Detail 包含完整 tool input 和 raw JSON。
- [x] 8.7 更新 DOM 测试：调试视图点击 permission/system/internal Turn 后，Detail 包含完整 raw JSON。
- [x] 8.8 更新 DOM 测试：选中 Turn 后修改类型筛选使其在左侧隐藏，Detail 仍保留完整内容。
- [x] 8.9 更新 DOM 测试：长 tool_result 在 Detail 中不被 `trunc()` 裁剪。
- [x] 8.10 更新 DOM 测试：默认视图 Step 与调试视图 Turn 指向同一 underlying Turn 时，Detail 主证据一致。
- [x] 8.11 更新 adapter 测试：OpenCode/Codex raw normalize 与 load_session 连续读取时 event id / turn id 保持稳定。

## 9. 验证

- [x] 9.1 运行 `openspec validate turn-detail-complete-evidence --strict`。
- [x] 9.2 运行前端静态测试，例如 `uv run python -m unittest tests.test_task_segmentation_frontend`。
- [x] 9.3 运行 DOM 测试，例如 `node tests/test_task_segmentation_dom.js`。
- [x] 9.4 运行项目相关测试集，至少覆盖 viewer、task segmentation 和当前修改触达的测试。
- [x] 9.5 手动验收真实 session：任务切分后 Session 树立即 Task-first，默认视图 Step Detail 完整、调试视图 internal Turn Detail 完整、筛选不裁剪 Detail、Raw JSON 可展开。
