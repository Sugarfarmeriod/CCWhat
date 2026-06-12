## Context

`conversation-minimal-turn-data-layer` 已经提供 Conversation 和 minimal Turn 数据层。当前 Session 页面仍偏向卡片列表式展示，尚未形成用户预期的树状 Trace 浏览体验。

本 change 只消费已有数据层，把 UI 表达改成：

```text
Trace
  会话 1
    Turn 1
    Turn 2
  会话 2
    Turn 1
```

后续 Change 3 才会加入：

```text
Trace
  Tools / Skills Snapshot
  Task
    会话
      Turn
```

## Goals / Non-Goals

**Goals:**

- Session 页面左侧使用树状结构展示会话和 minimal Turn。
- 支持会话节点展开/折叠、Turn 节点选中和高亮。
- 右侧 Turn detail 只展示 `Agent 响应` 和 `原始 JSON`。
- 点击会话节点时展示轻量会话摘要。
- 保持现有搜索/type filter、Task 起止 Turn 定位和 Raw JSON 调试能力不崩。

**Non-Goals:**

- 不实现 Task 作为树顶层分组。
- 不实现 Tools / Skills Snapshot 节点。
- 不实现 Tools / Skills Changed Turn。
- 不做 task outcome、failure diagnosis、diff、req/resp、test evidence。
- 不修改后端 API。

## Decisions

### Decision 1：Session 页面使用 Trace Tree，但不引入 Task 层

左侧树第一版只展示：

```text
Group / Trace root
  会话
    Turn
```

如果有 main group 和 subagent group，可以先按 group 分段展示。group 不是本次产品术语中的“会话”，只是日志来源分组。

### Decision 2：树节点类型显式化

建议节点数据结构：

```js
{
  nodeType: "conversation" | "turn",
  key: "...",
  label: "...",
  groupId: "main",
  conversationKey: "...",
  turnKey: "...",
  kind: "tool_use",
  summary: "Read auth.py"
}
```

UI 不需要新建复杂状态机，但应至少维护：

```js
selectedTraceNodeKey
expandedConversationKeys
```

### Decision 3：会话节点右侧只做轻量摘要

点击会话节点，右侧展示：

- 会话 label
- 用户请求原文或摘要
- Agent 最终反馈摘要
- Turn 数量
- 起止锚点

不展示 evidence、diagnosis、diff。

### Decision 4：Turn detail 极简展示

点击 Turn 节点，右侧只展示两个区块：

```text
Agent 响应
原始 JSON
```

`Agent 响应` 根据 minimal Turn kind 渲染当前 Turn 的内容：

- `user_message`：展示用户消息内容
- `thinking`：展示 thinking/reasoning 内容
- `assistant_text`：展示 assistant 文本
- `tool_use`：展示工具名和 input
- `tool_result`：展示结果内容和错误状态
- `system/context/unknown`：展示对应文本或摘要

`原始 JSON` 折叠展示当前 Turn 对应的原始 entry/block。不要在主卡片中展示整个会话或整个原始 entry 的其他 block。

### Decision 5：搜索和类型筛选不改变树结构编号

搜索/type filter 可以影响节点可见状态或显示 filter-empty，但不能重新切分会话，也不能重新编号 Turn。

推荐行为：

- 会话节点始终保留，除非搜索明确过滤到没有任何匹配内容。
- Turn 节点可根据 filter/search 标记为空或隐藏；第一版可以继续保留节点并显示隐藏提示，避免树跳动过大。
- 如果选中 Turn 被 filter 隐藏，右侧显示“当前筛选隐藏了该 Turn”。

### Decision 6：现有 Task 定位继续可用

虽然 Task 不进入树顶层，但 Task detail 中“定位开始/结束 Turn”仍应能跳到 Session 页对应树节点：

1. 切换到 Session 页面。
2. 展开目标会话。
3. 选中目标 Turn。
4. 滚动并高亮目标节点。

## Risks / Trade-offs

- [Risk] 单文件 HTML 继续变复杂。  
  → Mitigation：将 Trace Tree 相关 helper 命名清晰，例如 `renderTraceTree()`、`selectTraceNode()`、`renderConversationDetail()`、`renderMinimalTurnDetail()`。

- [Risk] 搜索/filter 行为和树结构语义冲突。  
  → Mitigation：第一版优先保持结构稳定，使用隐藏提示而不是重切编号。

- [Risk] 用户可能期待 Task 也出现在树里。  
  → Mitigation：明确本 change 只做 Change 2；Task 注入由 Change 3 实现。

## Migration Plan

1. 保留 Conversation/minimal Turn 数据层。
2. 新增 Trace Tree 渲染函数替代当前平铺 Turn card 渲染。
3. 新增会话节点选中和折叠状态。
4. 改造 Turn detail 为 `Agent 响应 + 原始 JSON` 两区块。
5. 调整 Task 定位逻辑，使其选中树中的 Turn 节点。
6. 更新测试。

## Open Questions

- group header 是否显示为 `Trace / Main / Subagent`，还是仅作为视觉分段。第一版建议显示为视觉分段，不把它当产品层级。
- `user_message` Turn 的右侧区块标题是否仍叫 `Agent 响应`。为保持当前需求统一，第一版可以统一使用该标题，后续再改成更准确的 `Turn 内容`。
