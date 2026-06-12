## 1. 上下文梳理

- [x] 1.1 梳理 `viewer/claude-log.html` 中 Conversation/minimal Turn 派生、Trace tree builder、Task overlay mapping 和当前 type filter 的数据流。
- [x] 1.2 确认 minimal Turn 的 kind 枚举、source entry/block anchor、turnKey、conversationKey、groupId 和 task mapping 字段。
- [x] 1.3 标记当前 UI 渲染入口，但本 change 不替换 UI 数据源。

## 2. 分类规则

- [x] 2.1 新增 `classifyTurnForDefaultView` 或等价 helper。
- [x] 2.2 将 `user_message` 分类为 primary，displayKind 为 user request。
- [x] 2.3 将 `thinking` / reasoning 分类为 primary，完整保留内容，不摘要、不弱化、不隐藏。
- [x] 2.4 将 `assistant_text` 分类为 primary，displayKind 为 Agent reply。
- [x] 2.5 将 `tool_use` 和 `tool_result` 分类为 primary，tool error 必须 primary。
- [x] 2.6 将执行相关 permission request / approval / denied / waiting 分类为 primary。
- [x] 2.7 将普通 system/context/hook/last-prompt/file-history-snapshot/queue/attachment/unknown 分类为 internal。
- [x] 2.8 为 internal turn 的 error/warning/failed/denied/rejected/blocked 等内容增加 primary promotion 规则。

## 3. View Projection 数据层

- [x] 3.1 新增 `buildTurnViewProjection(mode, source)` 或等价 helper，支持 `default` 和 `debug`。
- [x] 3.2 `default` projection 只输出 primary Step 节点。
- [x] 3.3 `debug` projection 输出全部 minimal Turn，保持原始顺序。
- [x] 3.4 projection node 保留 underlyingTurnKey、turn、groupId、conversationKey、taskId/taskKey、event/block/file anchor。
- [x] 3.5 projection 不向 minimal Turn 对象写入 view-only 字段，避免污染底层数据。
- [x] 3.6 支持无 active task overlay 时的 Conversation projection。
- [x] 3.7 支持有 active task overlay / confirmed task trace 时的 Task-first projection。

## 4. Label 与空状态

- [x] 4.1 default projection 在每个展示范围内生成连续 `Step N` label。
- [x] 4.2 debug projection 保留底层 `Turn N` label。
- [x] 4.3 默认视图隐藏 internal Turn 时不得造成 Step 编号断裂。
- [x] 4.4 Task 或 Conversation 没有 primary Step 时，projection 输出明确 empty metadata。

## 5. 测试

- [x] 5.1 更新前端静态测试，断言 classification helper 和 projection helper 存在。
- [x] 5.2 新增 DOM/JS 测试：default projection 包含 user、thinking、assistant text、tool use、tool result。
- [x] 5.3 新增 DOM/JS 测试：thinking 在 default projection 中完整保留，不摘要、不隐藏。
- [x] 5.4 新增 DOM/JS 测试：普通 system/context/hook/snapshot/queue 在 default projection 中隐藏，但 debug projection 保留。
- [x] 5.5 新增 DOM/JS 测试：error-like internal Turn 被提升为 primary。
- [x] 5.6 新增 DOM/JS 测试：default Step label 连续，debug Turn label 保持原编号。
- [x] 5.7 新增 DOM/JS 测试：projection 不 mutate minimal Turn 对象。
- [x] 5.8 新增 DOM/JS 测试：Task / Conversation / Turn anchor 在 projection 中保留。

## 6. 验证

- [x] 6.1 运行 `openspec validate turn-view-mode-projection --strict`。
- [x] 6.2 运行前端 DOM/JS 测试命令，例如 `node tests/test_task_segmentation_dom.js` 或项目等价命令。
- [x] 6.3 运行 `python3 -m pytest -q` 或项目当前全量测试命令。
- [x] 6.4 手动检查一个真实 session 的 projection：default 中 thinking 可见，internal 事件隐藏；debug 中全部 Turn 按时序保留。
