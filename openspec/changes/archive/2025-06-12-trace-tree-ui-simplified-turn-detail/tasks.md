## 1. 上下文梳理

- [x] 1.1 梳理 `viewer/claude-log.html` 中当前 `Session` 页面渲染入口、页面切换状态、type filter、search 和 task 定位函数。
- [x] 1.2 确认已归档 change 提供的 Conversation/minimal Turn 数据结构，包括 `allGroupConversations`、conversation key、turn key、kind 和 block anchor。
- [x] 1.3 标记当前平铺 Turn card 渲染、Turn detail 渲染和 event/Turn lookup 中需要替换或复用的函数。

## 2. Trace Tree 状态和渲染

- [x] 2.1 新增或整理 Trace 树 UI 状态：`selectedTraceNodeKey`、`expandedConversationKeys`、临时高亮节点和隐藏提示状态。
- [x] 2.2 新增 Trace node 派生 helper，将 Conversation/minimal Turn 数据转换为稳定的 group、conversation、turn 节点结构。
- [x] 2.3 将 `Session` 页面主列表改为 Trace 树渲染，按 group 展示会话节点和会话下的 Turn 节点。
- [x] 2.4 会话节点展示会话 label、用户请求摘要、Turn 数量，并支持展开/折叠。
- [x] 2.5 Turn 节点展示稳定 Turn label、kind badge、简短摘要，并支持点击选中。
- [x] 2.6 保证选中状态唯一，切换节点时同步左侧高亮和右侧详情。

## 3. 右侧详情简化

- [x] 3.1 新增 `renderConversationDetail` 或等价函数，展示会话 label、group、用户请求、Agent 最终反馈摘要、Turn 数量和起止锚点。
- [x] 3.2 新增或改造 `renderMinimalTurnDetail`，右侧 Turn detail 只保留 `Agent 响应` 和 `原始 JSON` 两个区块。
- [x] 3.3 按 Turn kind 渲染当前 minimal Turn 内容：`user_message`、`thinking`、`assistant_text`、`tool_use`、`tool_result`、`system`、`context`、`unknown`。
- [x] 3.4 `原始 JSON` 只绑定当前 Turn 的原始 entry 或 block anchor，默认折叠，不展示整个会话或相邻 Turn。
- [x] 3.5 移除或隐藏本 change 范围外的 Turn detail 内容：evidence、files、diff、commands、tests、diagnostics、task boundary 字段。

## 4. 筛选、搜索和定位

- [x] 4.1 调整 type filter 和 search 行为，使其只影响节点可见状态或隐藏提示，不重新切分会话、不重新编号 Turn。
- [x] 4.2 当当前选中 Turn 被筛选隐藏时，右侧详情展示明确提示，不静默清空、不自动跳到其他 Turn。
- [x] 4.3 更新 Task 起止 Turn 定位逻辑：从 `Tasks` 页面跳转时切到 `Session` 页面，展开目标会话，选中并滚动高亮目标 Turn。
- [x] 4.4 保留现有 event/uuid/file anchor 到 Turn 的 lookup 能力，确保定位仍基于完整 session 数据而不是当前 DOM 可见节点。
- [x] 4.5 确保本 change 不新增 Task 顶层树结构，也不新增 Tools/Skills Snapshot 节点。

## 5. 测试与验证

- [x] 5.1 更新前端静态测试，断言 Trace Tree 相关状态、渲染函数、选择函数、会话详情函数和极简 Turn detail 函数存在。
- [x] 5.2 更新 DOM 行为测试，覆盖默认树结构、会话展开/折叠、点击会话、点击 Turn、唯一选中状态。
- [x] 5.3 更新 DOM 行为测试，覆盖 Turn detail 只展示 `Agent 响应` 和 `原始 JSON`，且 Raw JSON 只对应当前 Turn。
- [x] 5.4 更新 DOM 行为测试，覆盖 type filter/search 不改变会话编号和 Turn 编号，以及选中 Turn 被隐藏时的提示。
- [x] 5.5 更新 DOM 行为测试，覆盖从 Task detail 定位开始/结束 Turn 时能展开会话、选中 Turn、滚动并高亮。
- [x] 5.6 运行 `python3 -m pytest -q` 或项目当前全量测试命令，并记录结果。
- [x] 5.7 运行前端 DOM 测试命令，例如 `node tests/test_task_segmentation_dom.js` 或当前项目等价命令，并记录结果。
- [x] 5.8 运行 `openspec validate trace-tree-ui-simplified-turn-detail --strict` 并修复所有规格问题。
- [x] 5.9 用真实 session 手动验收：默认进入 `Session` 页面时显示 `Trace -> 会话 -> Turn` 树，点击会话/Turn 右侧详情正确，Task 定位按钮能跳到对应 Turn。
