## 1. 上下文确认

- [x] 1.1 阅读 `docs/turn-display-redesign.md` 中 Change 2 的边界，确认本 change 只做 Trace 树双视图 UI。
- [x] 1.2 阅读已归档 `turn-view-mode-projection` change，确认可复用 `classifyTurnForDefaultView` 和 `buildTurnViewProjection`。
- [x] 1.3 梳理 `viewer/claude-log.html` 中 `renderTraceTree()`、`buildTraceNodes()`、`renderSessionPage()`、类型筛选和选择状态相关函数。
- [x] 1.4 明确不修改后端 API、不改 Task segmentation 算法、不做 Task 编辑器。

## 2. 视图模式状态与顶部控件

- [x] 2.1 新增 `traceViewMode` 状态，默认值为 `default`。
- [x] 2.2 新增 `默认视图 / 调试视图` segmented control 或等价按钮组。
- [x] 2.3 新增 `setTraceViewMode(mode)` 或等价函数，用于更新状态并重渲染 Session Trace。
- [x] 2.4 新增 `updateTraceViewModeControls()` 或等价函数，同步按钮 active 状态和类型筛选可见性。
- [x] 2.5 session 加载后保持默认视图，不自动跳到调试视图。

## 3. Trace 树接入 projection

- [x] 3.1 调整 `renderTraceTree()`，让 Turn/Step 子节点来自 `buildTurnViewProjection(traceViewMode, source)`。
- [x] 3.2 保留 Tools / Skills Snapshot 节点渲染。
- [x] 3.3 保留 Task-first 层级：`Task -> 会话 -> Step/Turn`。
- [x] 3.4 保留 Conversation-first 层级：`会话 -> Step/Turn`。
- [x] 3.5 default 模式渲染 Step node，使用 `Step N` label 和 projection displayKind。
- [x] 3.6 debug 模式渲染 Turn node，使用底层 `Turn N` label 和 kind badge。
- [x] 3.7 projection node click 后仍能通过 `underlyingTurnKey` 打开当前 Turn detail。

## 4. 默认视图降噪与调试筛选

- [x] 4.1 default 模式不得显示 ordinary internal Turn。
- [x] 4.2 default 模式必须显示 user、thinking、assistant_text、tool_use、tool_result 和 error-like promoted Turn。
- [x] 4.3 debug 模式必须显示全部 Turn，且顺序和底层 Minimal Turn 一致。
- [x] 4.4 default 模式隐藏底层类型筛选。
- [x] 4.5 debug 模式显示底层类型筛选。
- [x] 4.6 类型筛选只影响 debug 模式左侧可见节点，不修改 projection source 和 Detail 数据。
- [x] 4.7 搜索和类型筛选同时作用时不得造成页面空白，必须显示空状态。

## 5. 选择状态与空状态

- [x] 5.1 切换视图时，如果当前 selected Turn 在目标 projection 可见，则保持选中。
- [x] 5.2 切换到 default 时，如果当前 selected internal Turn 不可见，则回退到最近 Conversation 或 Task。
- [x] 5.3 对被隐藏的 internal Turn 显示提示：可切换到调试视图查看完整 Turn。
- [x] 5.4 default 模式下 Task 或 Conversation 没有 primary Step 时，显示明确空状态。
- [x] 5.5 切换视图、筛选、搜索后主工作区和左侧树不得变成空白。

## 6. 样式与可读性

- [x] 6.1 为双视图控件新增简洁样式，风格贴近当前 LangSmith-like workbench。
- [x] 6.2 Step card 与 Turn card 在视觉上可区分，但不引入重装饰。
- [x] 6.3 default 模式下 Step label、display kind、summary 排版稳定，不因长文本撑破布局。
- [x] 6.4 debug 模式下 internal Turn 应有明确 kind badge。
- [x] 6.5 空状态和隐藏提示文案简短清晰。

## 7. 测试

- [x] 7.1 更新前端静态测试，断言 `traceViewMode`、双视图控件、`setTraceViewMode`、`updateTraceViewModeControls` 存在。
- [x] 7.2 更新前端静态测试，断言 `renderTraceTree()` 使用 `buildTurnViewProjection`。
- [x] 7.3 更新前端静态测试，断言 default 模式隐藏 `typeFilters`，debug 模式显示。
- [x] 7.4 更新 DOM 测试：default 模式只显示 primary Step，不显示 ordinary internal Turn。
- [x] 7.5 更新 DOM 测试：debug 模式显示完整 Turn，包括 ordinary internal Turn。
- [x] 7.6 更新 DOM 测试：切换 default/debug 后左侧树不空白且顺序正确。
- [x] 7.7 更新 DOM 测试：选中 internal Turn 后切回 default，出现提示或回退选择。
- [x] 7.8 更新 DOM 测试：default 模式空 projection 范围显示明确空状态。

## 8. 验证

- [x] 8.1 运行 `openspec validate trace-tree-dual-view-ui --strict`。
- [x] 8.2 运行前端静态测试，例如 `uv run python -m unittest tests.test_task_segmentation_frontend`。
- [x] 8.3 运行 DOM 测试，例如 `node tests/test_task_segmentation_dom.js`。
- [x] 8.4 运行项目相关测试集，至少覆盖 viewer、task segmentation 和当前修改触达的测试。
- [x] 8.5 手动验收真实 session：默认视图可读、调试视图完整、切换不空白、类型筛选只在调试视图出现。
