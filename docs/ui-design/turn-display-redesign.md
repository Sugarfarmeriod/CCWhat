# Turn 展示降噪与双视图改造方案

## 背景

当前 CCWhat 的 Session Trace 已经进入 `Task -> 会话 -> Turn` 的树状结构。Turn 被设计为最小执行单位，用来还原 Agent 在一次会话中的真实执行过程。

但在 Claude / Codex / OpenCode 这类 Agent 的真实日志中，最小执行单位会包含大量内部事件：

- `last-prompt`
- `permission-mode`
- `PostToolUse:*`
- `file-history-snapshot`
- `queue-operation`
- system / context 注入
- attachment metadata
- hook 产生的内部 prompt

这些事件对调试有价值，但默认全部展示会带来明显问题：

- 主执行链路被内部机制淹没。
- 用户很难快速看到“用户说了什么、Agent 做了什么、工具跑了什么、结果是什么”。
- Task 树中 Turn 数量膨胀，任务边界可读性下降。
- 但如果把内部事件统一折叠到底部，又会破坏时间顺序，失去可观测性。

因此本次改造目标不是删除内部事件，而是引入两种 Trace 展示模式：

```text
默认视图：降噪后的主执行链路
调试视图：完整时序的所有 Turn
```

## 核心原则

### 1. 底层 Turn 不丢失

底层仍保留完整 minimal Turn 数据。任何原始 event、block anchor、file anchor、raw JSON 都不能因为默认视图而丢失。

```text
Raw Trace
  -> Conversation
  -> Minimal Turn（完整）
  -> View Projection（默认视图 / 调试视图）
```

### 2. 视图模式只影响左侧 Trace 树

视图模式只控制左侧树中哪些节点可见，以及节点 label 如何展示。

右侧 Detail 不跟随模式降级。

```text
左侧 Trace 树：
  默认视图：只展示主执行 Step
  调试视图：展示完整 Turn 时间线

右侧 Detail：
  永远展示当前选中节点的完整内容
```

### 3. 内部事件不能统一堆到底部

内部事件的位置本身就是证据。调试视图中必须按原始时间 / entry / block 顺序展示所有 Turn。

默认视图可以隐藏内部事件，但不能改变调试视图的原始时序。

### 4. Task / 会话边界不因视图变化而改变

Task、会话和底层 Turn 的边界仍基于完整数据。

默认视图只是一个 projection：

```text
Task 边界：完整 Turn 数据
默认视图：只显示该 Task 下的主执行 Step
调试视图：显示该 Task 下的全部 Turn
```

## 术语

### Minimal Turn

底层最小执行单位。用于完整可观测性和定位。

例如：

- user message
- assistant text
- thinking / reasoning
- tool_use
- tool_result
- permission-mode
- PostToolUse hook
- file-history-snapshot
- queue-operation
- system / context

### Visible Step

默认视图中的可见执行步骤。

Step 不是新的底层数据结构，而是对 Minimal Turn 的展示投影。它用于表达用户真正关心的主执行链路。

### Debug Turn

调试视图中的完整 Turn。它与 Minimal Turn 一一对应，按原始顺序展示。

## 两种视图模式

### 默认视图

默认视图目标：快速看清 Agent 的主执行链路。

默认展示：

- 用户请求
- thinking / reasoning，完整展示，和其他主执行 Step 平级
- Agent 文本回复
- 工具调用
- 工具结果
- 错误结果
- 明确影响执行的权限事件，例如等待授权、拒绝、权限变化

默认隐藏：

- 普通 permission-mode 状态
- last-prompt
- PostToolUse hook
- file-history-snapshot
- queue-operation
- system prompt 注入
- context injection
- attachment metadata
- 纯内部 lifecycle event

默认视图示例：

```text
Task 1
  会话 1
    Step 1  用户请求       帮我修复导出报错
    Step 2  Thinking      我需要先复现导出错误，然后检查 export 模块...
    Step 3  工具调用       Bash: npm test
    Step 4  工具结果       失败：TypeError ...
    Step 5  工具调用       Edit: export.ts
    Step 6  Agent 回复     已修复并通过测试
```

### 调试视图

调试视图目标：完整还原执行时序。

调试视图展示所有 Minimal Turn：

- user
- assistant text
- thinking
- tool_use
- tool_result
- system
- context
- permission-mode
- hook
- file-history-snapshot
- queue-operation
- attachment
- unknown

调试视图示例：

```text
Task 1
  会话 1
    Turn 1   user                 帮我修复导出报错
    Turn 2   permission-mode      acceptEdits
    Turn 3   thinking             我需要先复现问题...
    Turn 4   tool                 Bash: npm test
    Turn 5   hook                 PostToolUse:Bash
    Turn 6   result               TypeError ...
    Turn 7   file-history         snapshot
    Turn 8   tool                 Edit: export.ts
    Turn 9   result               edited
    Turn 10  text                 已修复并通过测试
```

## 编号策略

默认视图和调试视图不应该共用可见编号。

原因：默认视图隐藏内部事件后，如果继续显示 `Turn 1 -> Turn 7 -> Turn 22`，用户会感到断裂。

建议：

```text
默认视图：Step 1、Step 2、Step 3
调试视图：Turn 1、Turn 2、Turn 3
```

底层仍保留真实 `turnKey` 和原始 `turn.index`，用于定位和导出。

### 默认视图 label

默认视图使用人类可读的 Step label：

```text
Step 1 用户请求
Step 2 Thinking
Step 3 工具调用
Step 4 工具结果
Step 5 Agent 回复
```

### 调试视图 label

调试视图保留完整 Turn label：

```text
Turn 1 user
Turn 2 permission-mode
Turn 3 think
Turn 4 tool
```

## 顶部控制设计

当前顶部的原始类型筛选：

```text
user / assistant / system / attachment / perm / fhs / queue / other
```

不适合作为主交互。它更像调试筛选。

建议主入口改成：

```text
[默认视图] [调试视图]
```

调试视图下可以保留高级筛选：

```text
调试筛选：
user / assistant / system / attachment / perm / fhs / queue / other
```

默认视图下不展示这些低层类型筛选，避免用户被内部类型干扰。

## 左侧 Trace 树行为

### 默认视图树

```text
Tools / Skills Snapshot

Task 1
  会话 1
    Step 1 用户请求
    Step 2 Thinking
    Step 3 工具调用
    Step 4 工具结果
    Step 5 Agent 回复
```

特点：

- 只展示主执行 Step。
- 隐藏内部事件。
- Step 编号按当前可见主链路连续编号。
- Task / 会话层级不变。

### 调试视图树

```text
Tools / Skills Snapshot

Task 1
  会话 1
    Turn 1 user
    Turn 2 permission-mode
    Turn 3 think
    Turn 4 tool
    Turn 5 hook
    Turn 6 result
    Turn 7 file-history
    Turn 8 text
```

特点：

- 展示全部 Minimal Turn。
- 严格保持原始时序。
- 可以使用原始类型筛选辅助调试。
- 不重排、不聚合到底部。

## 右侧 Detail 行为

右侧 Detail 永远展示完整内容。

视图模式不改变 Detail 的完整性。

### 用户在默认视图点击 Step

例如点击：

```text
Step 2 工具调用 Bash: npm test
```

右侧应展示：

- 工具名
- 完整 input
- 关联 tool_result，如果当前 Step 表示的是 tool_use/result 配对
- 错误状态
- 相关 metadata
- 原始 JSON

### 用户在调试视图点击 Turn

例如点击：

```text
Turn 2 permission-mode
```

右侧应展示：

- permission-mode 的完整内容
- 来源 entry / block
- metadata
- 原始 JSON

### 关键规则

```text
左侧负责降噪导航。
右侧负责完整证据。
```

默认视图不是裁剪证据，只是隐藏部分节点。

## 默认视图分类规则

第一版可以用规则分类，不需要 LLM。

### Primary Step

默认视图展示。

| Minimal Turn 类型 | 默认视图分类 | 说明 |
|---|---|---|
| user_message | primary | 用户真实请求 |
| thinking | primary | Agent 推理过程，默认视图完整展示，不摘要、不弱化 |
| assistant_text | primary | Agent 对用户的文本反馈 |
| tool_use | primary | 工具调用 |
| tool_result | primary | 工具结果 |
| tool_result is_error | primary | 错误结果，必须展示 |
| permission request / denied / approval | primary | 影响执行的权限事件 |

### Internal Turn

默认视图隐藏，调试视图展示。

| Minimal Turn 类型 | 默认视图分类 | 说明 |
|---|---|---|
| last-prompt | internal | 内部 prompt |
| permission-mode 普通状态 | internal | 普通状态噪声 |
| PostToolUse hook | internal | hook 注入 |
| file-history-snapshot | internal | 文件历史快照 |
| queue-operation | internal | 队列内部事件 |
| system | internal | 系统注入 |
| context | internal | 上下文注入 |
| attachment metadata | internal | 附件元数据 |
| unknown | internal | 默认调试视图展示 |

### 重要例外

有些事件类型平时是 internal，但出现异常时应升为 primary：

- permission denied
- tool error
- hook error
- queue failure
- unknown event with error-like text

## 数据模型建议

不要改底层 Minimal Turn，只增加展示投影字段。

```js
{
  turnKey: "...",
  kind: "tool_use",
  debugLabel: "Turn 8",
  view: {
    defaultVisible: true,
    defaultLabel: "Step 2",
    displayKind: "tool_call",
    noiseClass: "primary" | "internal",
    hiddenReason: null
  }
}
```

或者单独生成 projection：

```js
{
  mode: "default",
  nodes: [
    {
      nodeType: "step",
      key: "step:...",
      underlyingTurnKey: "turn:...",
      label: "Step 2",
      displayKind: "tool_call"
    }
  ]
}
```

推荐第二种：projection 不污染底层数据。

## 与 Task Trace Overlay 的关系

Task Trace Overlay 仍基于完整 Turn 范围。

视图模式只影响 overlay 下的可见节点。

```text
Overlay Task 1 覆盖 Turn 1 - Turn 10

默认视图：
  显示 Step 1、Step 2、Step 3、Step 4

调试视图：
  显示 Turn 1 ... Turn 10
```

人工调整 Task 边界时建议进入调试视图，或者允许在默认视图选择 Step 后映射到底层 Turn。

## 建议拆分为几个 Change

这次改造建议分 3 个 change 执行，避免一次性同时改分类、树渲染、右侧 detail 和编辑器。

### Change 1：Turn View Mode 数据投影

建议名称：

```text
turn-view-mode-projection
```

目标：

- 新增默认视图 / 调试视图模式状态。
- 基于完整 Minimal Turn 生成 view projection。
- 给每个 Turn 分类为 primary / internal。
- 默认视图生成连续 Step label。
- 调试视图保留完整 Turn label。
- 不大改 UI，只先确保数据投影正确。

验收重点：

- 默认视图只包含 primary Step。
- 调试视图包含全部 Turn。
- 内部事件顺序在调试视图中保持原样。
- Step label 连续，Turn label 保持底层编号。
- Task / 会话 / Turn 锚点不丢。

### Change 2：Trace 树双视图 UI

建议名称：

```text
trace-tree-dual-view-ui
```

目标：

- 顶部主筛选改成 `默认视图 / 调试视图`。
- 默认视图隐藏原始类型筛选。
- 调试视图保留原始类型筛选作为高级调试筛选。
- 左侧 Trace 树根据当前 view projection 渲染。
- Task / 会话层级保持不变。

验收重点：

- 切换默认 / 调试视图时，左侧树节点变化符合预期。
- 默认视图不显示 hook、snapshot、permission-mode 普通状态等内部事件。
- 调试视图严格按时序显示全部事件。
- 内部事件不被统一移动到底部。
- 切换视图不破坏当前选中节点；如果节点在默认视图不可见，应给出提示或切到最近可见父节点。

### Change 3：Detail 完整性与调试筛选

建议名称：

```text
turn-detail-complete-evidence
```

目标：

- 右侧 Detail 永远展示当前选中节点的完整内容。
- 默认视图中的 Step 点击后，Detail 展示 underlying Turn 的完整 input/result/raw JSON。
- 调试视图中的内部 Turn 点击后，Detail 展示完整内部事件和 raw JSON。
- 调试视图中低层类型筛选只影响左侧节点可见性，不裁剪 Detail 内容。

验收重点：

- 默认视图不会裁剪 Detail。
- 调试视图可以查看 permission-mode / hook / snapshot 的完整内容。
- Raw JSON 始终可展开。
- 视图模式只影响左侧树，不影响右侧证据完整性。

## 后续可选 Change

如果前三个 change 稳定后，可以再考虑：

### Change 4：默认视图摘要优化

- tool_use + tool_result 在默认视图中是否可以显示为一个 Step，但仍保留 underlying Turn 映射。
- 错误结果优先高亮。
- 会话标题显示 primary/internal 数量。

### Change 5：Task 编辑器与默认视图联动

- 默认视图中调整 Task 边界时，明确映射到底层 Turn。
- 调试视图提供更精确边界调整。
- 手动创建 Task 时可选择 Step 或 Turn。

## 推荐优先级

当前最优先应该做：

```text
Change 1: turn-view-mode-projection
Change 2: trace-tree-dual-view-ui
Change 3: turn-detail-complete-evidence
```

不要先做复杂 Step 聚合，也不要先做拖拽编辑。先把“默认视图降噪、调试视图完整、Detail 完整”这条产品主线做稳。

## 最终设计一句话

CCWhat 的 Turn 展示应从“所有内部事件默认铺开”改为“双视图投影”：

```text
默认视图用于阅读主执行链路；
调试视图用于完整时序可观测；
右侧 Detail 永远保留完整证据。
```
