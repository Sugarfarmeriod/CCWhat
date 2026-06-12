## 1. 现状梳理与测试基线

- [x] 1.1 梳理 `viewer/claude-log.html` 当前 `groups`、`allEntries`、`buildTurns()`、`turnNavigationIndex` 和 Task 定位相关数据流。
- [x] 1.2 梳理 Claude / Codex / OpenCode 三类 session entry 结构，确认 user、assistant、tool_use、tool_result、thinking/reasoning 的常见字段。
- [x] 1.3 增加最小 fixture：一个真实用户请求、assistant text、多个 tool_use、多个 tool_result、最终 assistant text。
- [x] 1.4 增加重复/非真实 user fixture：system-reminder、local-command、tool_result-only user、重复镜像 user。

## 2. Conversation 派生数据层

- [x] 2.1 新增 `buildConversations(entries, groupId)` 或等价 helper，输出稳定 Conversation 列表。
- [x] 2.2 新增 `isRealUserRequest(entry, previousConversation)` 或等价 helper，排除 tool_result-only、system-reminder、local-command、last-prompt、queue、permission、重复镜像 user。
- [x] 2.3 为每个 Conversation 生成 `conversationKey`、label、start/end anchor、user message text、final agent text 和原始 entry 范围。
- [x] 2.4 处理首个真实用户请求前的 preamble entries，避免影响普通会话编号。
- [x] 2.5 在 session 加载后构建并保存 `allGroupConversations` 或等价状态。

## 3. Minimal Turn 派生数据层

- [x] 3.1 新增 `buildMinimalTurns(conversation)` 或等价 helper，将 Conversation 内 entries 拆成最小 Turn。
- [x] 3.2 为真实用户请求创建 `user_message` Turn。
- [x] 3.3 为 thinking/reasoning 创建 `thinking` Turn。
- [x] 3.4 为 assistant 普通 text block 创建 `assistant_text` Turn。
- [x] 3.5 为每个 `tool_use` block 创建独立 `tool_use` Turn，并记录 tool name、tool_use_id、input 和 block anchor。
- [x] 3.6 为每个 `tool_result` block 创建独立 `tool_result` Turn，并记录 tool_use_id、结果摘要、错误状态和 block anchor。
- [x] 3.7 确保一个 assistant entry 中多个 content block 会拆成多个 Turn，且一个 Turn 不包含多次 tool_use。
- [x] 3.8 为 system/context/metadata 创建 `system`、`context` 或 `unknown` Turn，保持原始信息可追溯。

## 4. 稳定锚点与兼容层

- [x] 4.1 为 Conversation 建立 `conversationKey -> conversation` 索引。
- [x] 4.2 为 minimal Turn 建立 `turnKey -> turn` 索引。
- [x] 4.3 为 uuid、message id、event id、file anchor 建立 entry 到 Conversation / Turn 的映射。
- [x] 4.4 为 entry 内 content block 建立 block anchor 到唯一 Turn 的映射，例如 `main:42#content:2`。
- [x] 4.5 保留旧 `lookupTurnByEventId()` 或提供兼容 wrapper，使 Task 起止 entry anchor 仍能定位到对应 minimal Turn。
- [x] 4.6 保证现有 Task 定位、filter、Raw JSON 查看不因数据层变化出现脚本错误。

## 5. 临时 UI 兼容

- [x] 5.1 现有 Session 页面可以先继续沿用当前样式，但数据源应来自 Conversation / minimal Turn。
- [x] 5.2 当前 Turn card label 可以继续显示 `Turn N`，但编号应为会话内 minimal Turn 编号或清晰展示所属会话。
- [x] 5.3 点击 Turn 时，右侧应能展示该 minimal Turn 的内容和原始 JSON，不再混入多个执行片段。
- [x] 5.4 不在本 change 中实现 Trace 树、Task 顶层注入或 Tools / Skills Snapshot 节点。

## 6. 测试与验证

- [x] 6.1 更新前端静态测试，断言 Conversation helper、minimal Turn helper 和新索引存在。
- [x] 6.2 增加 DOM/行为测试：一个用户请求到最终回复派生为一个 Conversation。
- [x] 6.3 增加 DOM/行为测试：一个 assistant entry 中多个 tool_use block 被拆成多个 `tool_use` Turn。
- [x] 6.4 增加 DOM/行为测试：tool_use 和 tool_result 不被合并为一个 Turn。
- [x] 6.5 增加 DOM/行为测试：非真实 user entry 不开启新 Conversation。
- [x] 6.6 增加 DOM/行为测试：entry anchor 和 block anchor 能定位到对应 Conversation / Turn。
- [x] 6.7 运行 `node tests/test_task_segmentation_dom.js` 或新增等价 DOM 测试。
- [x] 6.8 运行 `python3 -m pytest -q tests/test_task_segmentation_frontend.py`。
- [x] 6.9 运行 `python3 -m pytest -q`。
- [x] 6.10 运行 `openspec validate conversation-minimal-turn-data-layer --strict`。
- [ ] 6.11 使用至少一个真实 session 手动验收：会话层正确、Turn 为最小执行单位、单个 Turn 不包含多个工具调用。
