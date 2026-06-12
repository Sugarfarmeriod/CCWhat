## 1. 上下文梳理

- [x] 1.1 梳理当前 `viewer/claude-log.html` 中 Trace tree builder、node selection、detail render、Task segmentation state 和 task locate 函数。
- [x] 1.2 确认现有 Task Segment 返回字段：task id、title/user intent、task type、status、confidence、start/end event id、boundary reason、evidence。
- [x] 1.3 确认前端可从现有 session 数据中提取 Tools 列表和 Skills 列表的来源；如果只能部分提取，需要定义 empty/unknown 展示。
- [x] 1.4 标记不应修改的范围：`ccwhat/task_segments` 切分算法、后端 API、复杂评测逻辑。

## 2. Tools / Skills Snapshot

- [x] 2.1 新增 `extractToolsSkillsSnapshot` 或等价 helper，从当前 session/group entries 中提取初始 Tools 和 Skills 列表。
- [x] 2.2 在 Trace tree node 派生结果最顶部插入唯一 `snapshot` 节点。
- [x] 2.3 新增 `renderToolsSkillsSnapshotDetail` 或等价函数，右侧展示 Tools 列表、Skills 列表、来源说明和空状态。
- [x] 2.4 确保 Snapshot 节点不出现在 Task 内部，也不因 Task 数量增加而重复。

## 3. Task Trace 确认状态

- [x] 3.1 新增当前 session 级 Task Trace 确认状态，例如 `taskTraceConfirmedBySession` 或等价结构。
- [x] 3.2 在 `Tasks` 页面切分结果预览中加入"确认切分"入口。
- [x] 3.3 用户确认后，将当前 task segment result 标记为该 session 的 confirmed Task Trace。
- [x] 3.4 重新切分时取消当前 session 的确认状态，新的切分结果先进入预览，不自动注入 Trace 树。
- [x] 3.5 切换 session 时确认状态、选中节点、展开状态必须按 session 隔离或安全重置。

## 4. Task 到 Conversation / Turn 映射

- [x] 4.1 新增 `mapTaskSegmentsToTraceNodes` 或等价 helper，基于 start/end event id 和现有导航索引映射 Task 覆盖的会话和 Turn。
- [x] 4.2 支持 Task 起止锚点无法映射时的 degraded state，保留 Task 节点但标记无法完整定位。
- [x] 4.3 支持一个会话被多个 Task 覆盖的情况：每个 Task 下只展示自身范围覆盖的 Turn。
- [x] 4.4 保持会话 label 和 Turn label 使用原始 Trace 稳定编号，不因 Task 分组重新编号。

## 5. Task-first Trace Tree 渲染

- [x] 5.1 扩展 Trace node 类型支持 `snapshot`、`task`、`conversation`、`turn`。
- [x] 5.2 未确认 Task Trace 时，树结构为 `Snapshot -> 会话 -> Turn`。
- [x] 5.3 确认 Task Trace 后，树结构为 `Snapshot -> Task -> 会话 -> Turn`。
- [x] 5.4 新增 Task 节点样式、展开/折叠状态、计数和摘要展示。
- [x] 5.5 扩展统一选择逻辑，确保 Snapshot、Task、会话、Turn 四类节点都能唯一选中。
- [x] 5.6 Task 下点击会话和 Turn 时复用 Change 2 的会话详情和 Turn 极简详情。

## 6. Task Detail 与定位

- [x] 6.1 新增 `renderTaskTraceDetail` 或等价函数，展示 Task label、title/user intent、type、status、confidence、起止 Turn、覆盖会话列表和 boundary reason。
- [x] 6.2 Task detail 中提供跳转到首个会话、首个 Turn、开始 Turn、结束 Turn 的入口。
- [x] 6.3 Task Trace 已确认时，定位应展开目标 Task 和目标会话，并选中、高亮目标 Turn。
- [x] 6.4 Task Trace 未确认时，定位继续使用 `会话 -> Turn` 树，不自动确认切分。
- [x] 6.5 不可定位时展示明确提示，不抛脚本错误，不静默无反应。

## 7. 筛选、搜索和状态一致性

- [x] 7.1 保持 search/type filter 不改变 Task、会话、Turn 的稳定编号。
- [x] 7.2 筛选隐藏当前选中节点时，右侧展示明确提示，不自动选中无关节点。
- [x] 7.3 确认 Task Trace 后，Task 节点计数应根据当前可见/完整数据清晰展示，避免和筛选结果混淆。
- [x] 7.4 确保 Snapshot 节点在筛选下仍可访问，除非搜索明确排除且有可理解的提示。

## 8. 测试与验证

- [x] 8.1 更新前端静态测试，断言 Snapshot helper、Task confirm state、Task mapping helper、Task detail render 和四类 node selection 存在。
- [x] 8.2 更新 DOM 行为测试：未确认状态显示 `Snapshot -> 会话 -> Turn`，不显示 Task 分组。
- [x] 8.3 更新 DOM 行为测试：确认切分后显示 `Snapshot -> Task -> 会话 -> Turn`，Snapshot 不重复且不进入 Task 内。
- [x] 8.4 更新 DOM 行为测试：点击 Snapshot 展示 Tools/Skills 详情。
- [x] 8.5 更新 DOM 行为测试：点击 Task 展示 Task 基础摘要，点击 Task 下会话/Turn 复用对应详情。
- [x] 8.6 更新 DOM 行为测试：重新切分会取消确认状态，新结果未确认前不注入 Trace 树。
- [x] 8.7 更新 DOM 行为测试：Task 已确认时开始/结束 Turn 定位会展开 Task 和会话并高亮 Turn。
- [x] 8.8 运行 `python3 -m pytest -q` 或项目当前全量测试命令，并记录结果。
- [x] 8.9 运行前端 DOM 测试命令，例如 `node tests/test_task_segmentation_dom.js` 或当前项目等价命令，并记录结果。
- [x] 8.10 运行 `openspec validate task-snapshot-trace-tree-integration --strict` 并修复所有规格问题。
- [x] 8.11 用真实 session 手动验收：切分前、切分预览、确认切分、重新切分、Snapshot 点击、Task 点击、Task 定位全部符合预期。

## 9. Review Fix：Task 必须成为 Trace 一级树层

- [x] 9.1 修复 `mapTaskSegmentsToTraceNodes`：使用统一 `lookupTurnByEventId` / navigation index 解析 Task 起止锚点，覆盖 event id、uuid、message id、block anchor、`main:<line>` 和 subagent file anchor。
- [x] 9.2 修复 Task 覆盖范围计算：按目标 group 的 flat Turn 顺序计算 start/end 范围，不要只比较 `turn.index` 且不要跨 group 污染。
- [x] 9.3 修复 `buildTraceNodes`：Task Trace confirmed 后，树结构必须是 `Snapshot -> Task -> 会话 -> Turn`；source group 只能作为元信息或视觉标签，不能插在 Snapshot 和 Task 之间。
- [x] 9.4 修复 confirmed 状态的回退行为：只要存在 confirmed task segments，就必须渲染 Task 节点；即使某个 Task 锚点无法映射，也显示 degraded Task 节点和错误提示，不能退回到 `会话 -> Turn + Task badge`。
- [x] 9.5 修复 Turn badge 行为：未确认预览时可以保留 `Task N` badge；Task Trace confirmed 后，Task 所属关系必须由树层级表达，Task 覆盖的 Turn 行内不再显示 `Task N` badge。
- [x] 9.6 修复 Task 定位：从 Task detail 定位开始/结束 Turn 时，应展开目标 Task 和会话，滚动到 Task 下的 Turn 节点；如果未确认，则才使用普通 `会话 -> Turn` 定位。
- [x] 9.7 增加 DOM 回归测试：confirmed 后 `entryList` 中 Snapshot 后直接出现 `.trace-task-card` / `[data-task-key]`，且 covered Turn 不再只显示 `.turn-task-badge`。
- [x] 9.8 增加 DOM 回归测试：Task start/end 使用 `main:<line>` file anchor 时仍能映射并生成 Task 下的会话/Turn。
- [x] 9.9 增加 DOM 回归测试：confirmed 后不存在被 Task 覆盖的 standalone conversation 节点；未覆盖会话可以保留在 `Unassigned` 或等价分组。
- [x] 9.10 运行 `openspec validate task-snapshot-trace-tree-integration --strict`、前端 DOM 测试和项目全量测试，并记录结果。
