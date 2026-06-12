# Trace 树状结构重构设计

## 背景

当前 CCWhat 的 Session 页面已经开始从原始日志列表转向 Turn-first 展示，但现有层级仍不够准确：

- 现在的 Turn 更像“用户消息分组”，不是最小执行单位。
- 缺少“会话”这一层：一次用户请求到 Agent 完成本次反馈之间的完整过程。
- Task 切分结果仍在独立 Task 页面中展示，没有进入主 Trace 树。
- Tools / Skills 列表没有稳定的展示位置。

这次改造目标是把左侧主导航从“日志列表”升级为统一的 Trace 树状结构。

## 核心术语

### Trace

当前完整日志视图的根节点。它代表一次完整 Agent session 的可观察执行记录。

### Tools / Skills Snapshot

当前 Trace 开始时 Agent 可用的工具和技能列表。

它永远放在 Trace 树的最顶部，不属于某个 Task，也不属于某个会话。

如果执行过程中 Tools / Skills 发生变化，则在对应位置插入一个特殊 Turn 展示变化。

### Task

从完整 Trace 中切分出的真实 coding 任务。

例如：

- 修复某个 bug
- 新增一个功能
- 更新文档
- 调整前端交互

Task 是目标层，不是原始日志容器。

### 会话

一次用户请求到 Agent 完成本次反馈之间的交互单元。

例如用户发送：

> 帮我修复这个 bug

直到 Agent 最终回复：

> 已修复，测试已通过

这一整段就是一个会话。

一个 Task 可以包含多个会话，因为用户可能多次反馈、追问、要求继续修改。

### Turn

会话中的最小执行单位。

一个 Turn 应尽量只表示一种执行片段，例如：

- 一段 thinking / reasoning
- 一次 tool_use
- 一次 tool_result
- 一段 assistant text
- 一条 user message
- 一条 context / system 信息

Turn 不应该再包含多次工具调用。如果原始 assistant message 里有多个 `tool_use` block，展示层应该拆成多个 Turn。

## 目标树结构

未切分 Task 前：

```text
Trace
  Tools / Skills Snapshot

  会话 1
    Turn 1
    Turn 2
    Turn 3

  会话 2
    Turn 1
    Turn 2
```

切分并确认 Task 后：

```text
Trace
  Tools / Skills Snapshot

  Task 1
    会话 1
      Turn 1
      Turn 2
    会话 2
      Turn 1

  Task 2
    会话 1
      Turn 1
      Turn 2
```

如果中途 Tools / Skills 发生变化：

```text
Trace
  Tools / Skills Snapshot

  Task 1
    会话 1
      Turn 1
      Turn 2
      Turn 3: Tools / Skills Changed
      Turn 4
```

## 改造任务

### 1. 原始 JSON / Trace 页面加入“会话”层级

当前页面不应该直接展示：

```text
Session
  Turn 1
  Turn 2
```

而应该展示：

```text
Trace
  会话 1
    Turn 1
    Turn 2
  会话 2
    Turn 1
```

会话边界由用户请求开始，到 Agent 本次最终反馈结束。

Turn 是会话内部的最小执行单位。

第一版需要完成：

- 从原始 entries 中派生会话列表。
- 每个会话下派生最小 Turn 列表。
- 保持原始 JSON 可查看，但不再作为左侧主结构。
- 保留稳定锚点，支持后续 Task 定位到具体会话和 Turn。

### 2. 右侧详情卡片简化

当前右侧不再做复杂诊断卡片。

点击具体 Turn 后，右侧只保留两个核心区块：

```text
Agent 响应
原始 JSON
```

其中：

- `Agent 响应` 展示当前 Turn 对应的内容。
- `原始 JSON` 折叠展示当前 Turn 对应的原始 JSON。

如果当前 Turn 是 tool_use，就展示工具调用内容。

如果当前 Turn 是 tool_result，就展示工具返回内容。

如果当前 Turn 是 thinking，就展示 thinking 内容。

如果当前 Turn 是 assistant text，就展示 assistant 文本。

如果当前 Turn 是 user message，也可以放在 `Agent 响应` 区块中按当前 Turn 内容展示，后续可再改名。

第一版不展示：

- 任务状态
- 失败诊断
- diff
- 测试覆盖
- req / resp 关联
- 复杂 evidence cards

这些能力后续再加。

### 3. 左侧改成统一树状结构

左侧主区域改为 Trace 树，而不是平铺 Turn 卡片。

树节点类型：

```text
Tools / Skills Snapshot
Task
会话
Turn
Tools / Skills Changed Turn
```

点击不同节点，右侧展示不同详情：

- 点击 `Tools / Skills Snapshot`：展示全局 Tools 列表和 Skills 列表。
- 点击 `Task`：展示 Task 标题、任务范围和基础摘要。
- 点击 `会话`：展示本次用户请求、Agent 最终反馈和包含的 Turn 列表。
- 点击 `Turn`：展示 Agent 响应和原始 JSON。
- 点击 `Tools / Skills Changed Turn`：展示 Tools / Skills 的新增、删除或变化。

### 4. Task 切分确认后进入树结构

Task 不再只存在于独立 Task 页面。

交互流程：

1. 用户点击“切分 Task”。
2. 页面展示切分预览。
3. 用户点击“确认切分”。
4. 左侧 Trace 树切换为 Task-first 结构：

```text
Trace
  Tools / Skills Snapshot
  Task 1
    会话 1
      Turn 1
      Turn 2
  Task 2
    会话 1
      Turn 1
```

注意：

- Tools / Skills Snapshot 仍然位于 Trace 最顶部。
- Task 是会话的上层分组。
- 会话是 Turn 的上层分组。
- Turn 是最小执行单位。

### 5. Tools / Skills Snapshot 独立放在 Trace 最顶部

Tools / Skills Snapshot 不放在 Task 顶部，也不放在每个会话顶部。

正确位置：

```text
Trace
  Tools / Skills Snapshot
  Task 1
  Task 2
```

点击该节点后，右侧展示：

```text
Tools
- Bash
- Read
- Edit

Skills
- openspec-propose
- openspec-apply-change
```

如果中途 Tools / Skills 发生变化，不修改顶部 Snapshot，而是在对应会话位置插入特殊 Turn：

```text
Turn N: Tools / Skills Changed
```

## 第一版不做的事情

第一版暂不做：

- 自动判断 Task 成功 / 失败。
- 复杂 evidence / diagnosis 面板。
- 每个 Turn 的 diff、测试、req-resp 深度关联。
- Tools / Skills 变化的复杂版本 diff。
- 人工拖拽调整 Task / 会话 / Turn 边界。

第一版重点是把层级和交互打正：

```text
Trace -> Task -> 会话 -> Turn -> 原始 JSON
```

## 后续实现建议

建议单独开一个 OpenSpec change，例如：

```text
trace-tree-conversation-turn-redesign
```

## 推荐拆分计划

这次改造不建议一次性完成。它同时涉及数据层级、Turn 定义、左侧树结构、右侧详情和 Task 注入，如果全部放进一个 change，验收和回归定位都会很困难。

推荐拆成 3 个 change 执行。

### Change 1: Conversation + 最小 Turn 数据层

目标：

```text
Trace -> 会话 -> Turn
```

改造内容：

- 引入“会话”层级。
- 会话定义为：一次用户请求到 Agent 完成本次反馈。
- 将 Turn 从“用户消息分组”改为“最小执行单位”。
- Turn 类型可以先保持简单，例如：
  - user message
  - thinking / reasoning
  - assistant text
  - tool_use
  - tool_result
  - context / system
- 保留现有 UI，先不急着重构左侧树。

验收重点：

- 一个会话可以包含多个 Turn。
- 一个 Turn 不再包含多次工具调用。
- 原始 JSON 能稳定映射到会话和 Turn。

### Change 2: Trace Tree UI + 右侧简化卡片

目标：

```text
Trace
  会话
    Turn
```

改造内容：

- 左侧主区域改成树状结构。
- 树中先展示会话和 Turn，不接入 Task。
- 点击会话节点，右侧展示会话级摘要。
- 点击 Turn 节点，右侧只展示：
  - Agent 响应
  - 原始 JSON
- 保持右侧卡片极简，不引入诊断、diff、测试、req/resp 等复杂字段。

验收重点：

- 左侧树展开 / 折叠 / 选中稳定。
- 点击不同 Turn，右侧内容正确切换。
- 右侧只展示当前 Turn 对应内容，不混入多个执行步骤。

### Change 3: Task 注入 + Tools / Skills Snapshot

目标：

```text
Trace
  Tools / Skills Snapshot
  Task
    会话
      Turn
```

改造内容：

- 在 Trace 树顶部增加 `Tools / Skills Snapshot` 节点。
- 点击该节点，右侧展示当前 Trace 初始可用 Tools 和 Skills 列表。
- 用户点击“切分 Task”后先展示预览。
- 用户点击“确认切分”后，将 Task 注入左侧树的会话上层。
- Tools / Skills Snapshot 永远保留在 Trace 最顶部，不放进 Task 内。
- 如果中途 Tools / Skills 发生变化，则在对应会话位置插入特殊 Turn。

验收重点：

- 未切分时：`Trace -> Tools / Skills Snapshot -> 会话 -> Turn`。
- 确认切分后：`Trace -> Tools / Skills Snapshot -> Task -> 会话 -> Turn`。
- Task 不再只存在于独立页面，而是进入主 Trace 树。
- Tools / Skills Snapshot 不因 Task 切分而重复。

## 执行顺序

建议按以下顺序实施：

1. 先实现会话层派生。
2. 再把 Turn 改成最小执行单位。
3. 再改左侧树结构。
4. 再把确认后的 Task 注入树顶层。
5. 最后加入 Tools / Skills Snapshot 节点。

对应到推荐的 3 个 change：

```text
Change 1: Conversation + 最小 Turn 数据层
Change 2: Trace Tree UI + 右侧简化卡片
Change 3: Task 注入 + Tools / Skills Snapshot
```
