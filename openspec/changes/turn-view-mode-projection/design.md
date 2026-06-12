## Context

当前前端已经有完整 minimal Turn 数据层，并且 Trace 树可以按 `Task -> 会话 -> Turn` 展示。但所有 minimal Turn 都直接进入左侧树，造成默认浏览噪声过大。

本 change 在 minimal Turn 和 UI 渲染之间增加一层 view projection：

```text
Minimal Turn（完整）
  -> buildTurnViewProjection(mode)
  -> default projection / debug projection
```

后续 UI change 只消费 projection，不直接决定哪些 Turn 应该隐藏。

## Goals / Non-Goals

**Goals:**

- 提供 `default` 和 `debug` 两种 view mode 的数据投影。
- 默认视图只输出主执行 Step。
- 调试视图输出完整 Turn 时间线。
- `thinking` 在默认视图中完整保留，作为 primary Step。
- 普通内部事件在默认视图隐藏，但顺序在调试视图完整保留。
- 保持所有底层锚点和映射稳定。

**Non-Goals:**

- 不改顶部 UI。
- 不改 Trace tree DOM。
- 不改 Detail panel。
- 不做 Step 聚合。
- 不做持久化设置。

## Decisions

### Decision 1：Projection 不修改底层 Turn

不要把 `defaultVisible` 等 UI 字段直接写回 minimal Turn。推荐生成独立 projection：

```js
{
  mode: "default",
  conversations: [
    {
      conversationKey: "...",
      nodes: [
        {
          nodeType: "step",
          key: "step:...",
          label: "Step 2",
          displayKind: "thinking",
          underlyingTurnKey: "...",
          turn,
          visibility: "primary"
        }
      ]
    }
  ]
}
```

这样可以保证完整 Turn 数据不被 UI 视图污染。

### Decision 2：默认视图中的 thinking 是 primary

`thinking / reasoning` 是理解 Agent 执行过程的重要内容。默认视图必须完整展示 thinking，不摘要、不弱化，也不折叠为内部事件。

分类规则：

```text
thinking -> primary
```

### Decision 3：普通 system 不是默认主链路

普通 system/context/hook 注入通常是运行环境或内部机制，不应该进入默认主链路。

但如果 system/context/hook 包含 error、warning、denied、failed 等明显影响执行的信号，应升级为 primary。

### Decision 4：默认视图和调试视图使用不同 label

默认视图隐藏内部事件后，可见编号必须连续：

```text
Step 1
Step 2
Step 3
```

调试视图保留完整 Turn label：

```text
Turn 1
Turn 2
Turn 3
```

底层 `turnKey`、`turn.index`、anchor 不变。

### Decision 5：投影必须保留父层级

Projection 必须保留：

- taskId / task key，如果当前有 active overlay
- conversationKey
- groupId
- underlyingTurnKey
- source entry/block anchor

这样后续 Trace 树和 Task 定位可以无缝使用。

## Classification Rules

### Primary in default mode

- `user_message`
- `thinking`
- `assistant_text`
- `tool_use`
- `tool_result`
- `tool_result` with error
- permission request / approval / denied / waiting
- system/context/hook/queue/unknown with clear error/warning/failure/denied signal

### Internal in default mode

- ordinary `permission-mode`
- `last-prompt`
- ordinary `PostToolUse:*`
- `file-history-snapshot`
- `queue-operation` without failure
- ordinary `system`
- ordinary `context`
- attachment metadata
- ordinary `unknown`

### Debug mode

Debug mode includes every minimal Turn in original order.

## Data Shape Sketch

Suggested helper:

```js
function classifyTurnForDefaultView(turn) {
  return {
    visibility: "primary" | "internal",
    displayKind: "user_request" | "thinking" | "agent_text" | "tool_call" | "tool_result" | "permission" | "internal",
    reason: "..."
  };
}

function buildTurnViewProjection(mode, source) {
  return {
    mode,
    groups: [...],
    generatedAt: Date.now()
  };
}
```

`source` can be existing `allGroupConversations` plus optional active task overlay mapping.

## Edge Cases

- A conversation with only internal turns: default projection should keep an empty conversation marker or hide it with count metadata; do not lose debug projection.
- A Task whose visible Steps are empty: default projection should still show Task node with “无默认视图 Step” or equivalent metadata.
- A hidden internal Turn is selected, then user switches to default mode: UI change will handle selection later, but projection should expose whether underlying turn is visible in default mode.
- Unknown event with error-like text should be primary.

## Migration Plan

1. Add classification helper.
2. Add projection helper for conversations.
3. Add projection helper for task-first tree source if active overlay exists.
4. Add tests for default mode and debug mode.
5. Leave current UI consuming old data until next change.
