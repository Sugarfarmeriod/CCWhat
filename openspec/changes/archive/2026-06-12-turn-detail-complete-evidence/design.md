## Context

`turn-view-mode-projection` 已经提供默认视图 / 调试视图的数据投影，`trace-tree-dual-view-ui` 已经让左侧 Trace 树消费 projection。当前剩余风险在右侧 Detail：它仍可能依赖 `entryMatchesFilter()`、简化摘要或截断文本，导致用户虽然能在左侧定位 Step/Turn，却无法在右侧看到完整证据。

本 change 的设计原则是延续文档里的分工，并补齐当前实现里已经暴露出的 Task-first 闭环回归：

```text
左侧 Trace 树：负责降噪导航和筛选
右侧 Detail：负责完整证据和 raw JSON
```

## Goals / Non-Goals

**Goals:**

- Task segmentation 生成结果后，Session Trace 立即进入 `Task -> 会话 -> Step/Turn` 结构，不需要额外点击确认。
- 默认视图点击 Step 后，Detail 展示 underlying Minimal Turn 的完整内容。
- 调试视图点击 internal Turn 后，Detail 展示完整内部事件、metadata 和 raw JSON。
- 类型筛选只影响左侧树，不影响当前选中 Turn 的 Detail。
- tool_use / tool_result / thinking / assistant_text / user_message / system/context/unknown 都有稳定、可读、可展开的 Detail。
- Raw JSON 始终可展开，并包含足够定位信息：entry index、file line、event id、block anchor、message/content block。

**Non-Goals:**

- 不实现 Task 编辑器、Task-first 闭环或 overlay 持久化。
- 不实现 Task 编辑器或 overlay 持久化。
- 不修改后端 API。
- 不修改 Minimal Turn 派生规则和 projection 分类规则。
- 不做 tool_use 与 tool_result 的复杂跨 Turn 聚合；第一版只保证当前 Turn 本身完整，若已有可定位关联则展示关联锚点。
- 不重写整个前端页面。

## Decisions

### Decision 1：Detail 渲染不调用左侧筛选逻辑

`buildMinimalTurnDetailHtml()` 不应因为 `entryMatchesFilter(e)` 为 false 而返回“当前筛选隐藏了该 Turn”。类型筛选是左侧导航筛选，不是证据裁剪。

替代方案是保留当前行为并提示用户调整筛选，但这会违背“右侧 Detail 永远完整”的产品原则。

### Decision 1.5：Task-first 使用 active task data，而不是 confirmed-only data

Session Trace 的树结构应消费当前 session 的 active task segmentation result：

```text
confirmed task data > cached/generated task data > no task data
```

`confirmTaskTraceForSession()` 只记录“用户确认过”的状态和 UI badge，不再决定 Session 树是否进入 Task-first。这样用户在 Tasks 页面完成切分后，回到 Session 页面即可看到 Task-first 树。

替代方案是继续要求用户点击“确认切分”，但这会让 Task 页面和 Session 页面状态割裂，也是当前手动测试暴露的问题。

### Decision 2：引入 Detail evidence helper，而不是继续堆叠摘要分支

建议新增或整理 helper：

- `buildTurnEvidenceModel(turn, entry)`
- `renderTurnEvidenceSections(model)`
- `renderRawEvidenceJson(model)`

第一版也可以不抽象成完整 class，但应把“完整证据字段”和“展示 HTML”分清，避免每个 kind 各自截断或丢字段。

### Decision 3：按 kind 展示主证据，同时保留 raw JSON 兜底

不同 kind 的主证据不同：

- `user_message`：完整用户文本、content block、entry metadata。
- `assistant_text`：完整文本，不只显示摘要。
- `thinking`：完整 thinking/reasoning 内容，不摘要。
- `tool_use`：完整 tool name、id、input JSON、content block。
- `tool_result`：完整 result content、`tool_use_id`、`is_error`。
- `context/system/unknown`：完整 entry type/subtype、文本或 structured payload、metadata。

无论主证据是否识别成功，底部都必须有 raw JSON 展开项。

### Decision 4：默认视图 Step 仍映射到底层 Turn

默认视图中的 Step 不是新数据实体。点击 Step 时应通过 `underlyingTurnKey` 找到底层 Minimal Turn，然后复用同一套 Detail 渲染。

因此 default/debug 的差异只在左侧 label 和可见节点；右侧 Detail 不需要区分 Step/Turn 两套证据模型。

### Decision 5：保留必要截断只用于列表，不用于 Detail 主证据

左侧 summary 可以截断；右侧 Detail 的主证据应完整展示，并通过 `<details>`、`max-height`、滚动容器等方式控制页面可读性。

## Risks / Trade-offs

- [Risk] 大型 tool_result 或 raw JSON 会让 Detail 很长。  
  → Mitigation：主证据使用可滚动 `<pre>` 或折叠 `<details>`，但不丢内容。

- [Risk] 某些 Agent 的本地日志结构与 Claude 不同，entry 字段不稳定。  
  → Mitigation：Detail helper 先使用通用字段和 raw JSON 兜底，不假设所有 agent 都有 Claude 风格 `message.content`。

- [Risk] 移除 `entryMatchesFilter()` 对 Detail 的影响后，用户可能看到左侧已过滤掉的类型内容。  
  → Mitigation：这是预期行为；如果节点已经被选中，右侧就是证据面板，不受导航筛选裁剪。

- [Risk] 未确认的 task result 进入 Task-first 后，用户可能误以为算法结果已人工确认。  
  → Mitigation：保留 `预览中 / 已确认` badge；Task-first 只表示当前 active task view，不表示人工确认。

- [Risk] 现有测试可能只检查摘要字段，无法发现内容裁剪。  
  → Mitigation：新增 DOM 测试覆盖“筛选隐藏后 Detail 仍完整”“长 tool_result 不被 `trunc()` 裁剪”“internal Turn raw JSON 可展开”。
