## Context

`docs/architecture/trace-tree-redesign.md` 已经确定长期目标：

```text
Trace
  Tools / Skills Snapshot
  Task
    会话
      Turn
```

其中“会话”不是底层 session 文件，而是一次用户请求到 Agent 完成本次反馈之间的交互单元；Turn 是会话中的最小执行单位。

当前 `viewer/claude-log.html` 已经有 Turn-first 展示，但它的 Turn 更接近用户消息分组：一个 Turn 里可能包含多段 assistant text、多次 tool_use、多个 tool_result。这不符合后续树状结构需要，也会让右侧 Turn detail 无法只展示一个执行片段。

## Goals / Non-Goals

**Goals:**

- 在前端派生 `Conversation` 层。
- 将 Turn 改造成会话内的最小执行单位。
- 保留原始 entries 与派生节点之间的稳定映射。
- 为后续 Trace Tree UI、Task 注入和 Tools / Skills Snapshot 预留干净数据结构。

**Non-Goals:**

- 不实现新的树状 UI。
- 不把 Task 注入到树结构。
- 不展示 Tools / Skills Snapshot。
- 不做 Task 成功/失败评测。
- 不修改后端接口和 task segmentation 算法。

## Decisions

### Decision 1：Conversation 是前端派生节点

第一版不要求后端新增 Conversation API。前端在加载 session entries 后派生：

```js
{
  conversationKey: "main:conversation:1",
  groupId: "main",
  label: "会话 1",
  userEntryIds: [...],
  startEntryId: "...",
  endEntryId: "...",
  userMessageText: "...",
  finalAgentText: "...",
  turns: [...]
}
```

会话边界规则：

1. 遇到真实用户请求，开始新会话。
2. 后续 assistant text、thinking、tool_use、tool_result、system/context 归入当前会话。
3. 遇到下一条真实用户请求，结束上一会话并开始新会话。
4. 首个真实用户请求前的 system/context entries 可归入 preamble conversation 或 group metadata，但不参与普通会话编号。

真实用户请求应排除：

- 纯 `tool_result` user entry
- `<system-reminder...`
- `<local-command...`
- last-prompt / queue / permission 等非用户主动请求
- 与上一真实用户请求重复且中间无有效 assistant 响应的镜像 entry

### Decision 2：Turn 是最小执行单位

Turn 从 Conversation 内派生，每个 Turn 只对应一个执行片段。

建议 Turn 结构：

```js
{
  turnKey: "main:conversation:1:turn:3",
  conversationKey: "main:conversation:1",
  groupId: "main",
  label: "Turn 3",
  kind: "tool_use",
  sourceEntryId: "...",
  contentIndex: 2,
  toolUseId: "...",
  toolName: "Read",
  text: "...",
  raw: {...}
}
```

Turn kind 第一版支持：

- `user_message`
- `thinking`
- `assistant_text`
- `tool_use`
- `tool_result`
- `context`
- `system`
- `unknown`

如果一个 assistant entry 的 `message.content` 中包含多个 block，必须拆成多个 Turn：

```text
assistant entry
  text
  tool_use Read
  tool_use Bash

派生为：
  Turn 1: assistant_text
  Turn 2: tool_use Read
  Turn 3: tool_use Bash
```

### Decision 3：tool_use 和 tool_result 不强行合并

第一版不把 tool_use 和 tool_result 合并成一个 Turn。它们是两个执行片段：

```text
Turn N: tool_use Bash
Turn N+1: tool_result Bash
```

这样符合“Turn 是最小执行单位”的定义，也便于后续右侧详情只展示当前 Turn 的内容。

可以通过 `toolUseId` 建立关联，但不改变最小 Turn 边界。

### Decision 4：稳定锚点必须同时支持 entry 和 block

旧逻辑主要以 entry 为定位单位。minimal Turn 需要支持 entry 内 block 级定位。

建议锚点：

```js
entryAnchor = "main:42"
blockAnchor = "main:42#content:2"
```

导航索引至少支持：

- entry id / uuid / message id -> Conversation + Turn
- file anchor -> Conversation + Turn
- block anchor -> Conversation + Turn
- turnKey -> Turn
- conversationKey -> Conversation

### Decision 5：先提供数据层，不强迫 UI 一次改完

这个 change 完成后，现有 UI 可以先临时映射到新的 Conversation/Turn 数据：

- 左侧仍可展示 Turn card。
- 但这些 Turn 应来自 minimal Turn，而不是旧的用户消息分组。
- 右侧细节可以继续使用现有容器，后续 Change 2 再改成树状 UI 和简化卡片。

## Risks / Trade-offs

- [Risk] 不同 Agent 的日志格式差异大，真实用户请求识别可能有误。  
  → Mitigation：将用户请求判断抽成 helper，并用 Claude/Codex/OpenCode fixture 覆盖常见格式。

- [Risk] block 级 Turn 会让 Turn 数量显著增加。  
  → Mitigation：这是期望行为；Turn 是执行片段，不再等同于用户消息轮次。

- [Risk] 旧 Task Segment 的 start/end eventId 还是 entry 级。  
  → Mitigation：第一版保留 entry -> Conversation/Turn 映射，后续 Task 注入可先映射到 entry 所属的第一个/最后一个 Turn。

- [Risk] UI 暂时仍沿用旧结构，用户可能看不出完整树状变化。  
  → Mitigation：本 change 明确只做数据层，Change 2 再做 Trace Tree UI。

## Migration Plan

1. 新增 Conversation / minimal Turn 派生 helper。
2. 用新数据层替代旧 `buildTurns()` 的核心输出，或保留兼容 wrapper。
3. 更新导航索引，使其支持 conversationKey、turnKey、entry anchor 和 block anchor。
4. 更新现有 Turn 展示所需字段，避免破坏当前页面。
5. 补充静态测试和 DOM 行为测试。
6. 用真实 session 手动确认：一个会话包含多个 minimal Turns，单个 Turn 不再包含多个 tool_use。

## Open Questions

- preamble entries 第一版是否在 UI 中显示为“会话 0”，还是隐藏到 group metadata。建议先隐藏到 metadata，避免干扰普通会话编号。
- user message 是否也作为一个 Turn 展示。建议是，因为它是会话中的第一个最小执行片段。
