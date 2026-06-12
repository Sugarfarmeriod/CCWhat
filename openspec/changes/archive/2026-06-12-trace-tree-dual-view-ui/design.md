## Context

当前前端已经具备三层数据：

```text
Raw entries / normalized events
  -> Conversation / Minimal Turn
  -> buildTurnViewProjection(default|debug)
```

`turn-view-mode-projection` 已经完成分类和 projection helper，但 UI 仍在很多地方直接渲染完整 Turn。这个 change 只负责把左侧 Session Trace 树接入 projection，并调整顶部控制的交互层级。

## Goals / Non-Goals

**Goals:**

- 默认进入 `default` 视图，展示主执行 Step。
- 提供 `default/debug` 双视图切换。
- 默认视图隐藏普通 internal Turn。
- 调试视图展示完整 Turn 时间线，且不重排、不聚合到底部。
- 原始类型筛选只在调试视图中显示。
- Task-first 树和 Conversation-first 树都消费同一个 projection 数据形态。
- 切换视图后主工作区不能空白，当前选择应尽量保持或有明确回退提示。

**Non-Goals:**

- 不重写 Detail panel。
- 不做 Step 聚合。
- 不做 Task Trace Overlay 编辑。
- 不做后端持久化。

## Decisions

### Decision 1：视图模式是 Session Trace 的 UI 状态

新增状态建议：

```js
let traceViewMode = 'default'; // 'default' | 'debug'
```

该状态只影响左侧 Trace 树的可见节点和 label。底层 `allGroupConversations`、Task Segment、Turn anchors 不变。

### Decision 2：Trace 树只消费 projection

`renderTraceTree()` 不再直接循环 `node.turns` 生成卡片，而是：

```js
const projection = buildTurnViewProjection(traceViewMode, {
  allGroupConversations,
  taskNodes
});
```

再根据 projection 渲染：

- `mode=default`：渲染 Step node，label 为 `Step N`。
- `mode=debug`：渲染 Turn node，label 为原始 `Turn N`。

### Decision 3：默认视图隐藏底层类型筛选

顶部保留两个层级：

```text
[默认视图] [调试视图]

调试视图展开：
user / assistant / system / attachment / perm / fhs / queue / other
```

默认视图不显示低层类型筛选，避免用户误以为这是主操作。

调试视图中的类型筛选仍只影响左侧节点可见性；本 change 不改变右侧 Detail。

### Decision 4：切换视图时选择状态必须可恢复或可解释

如果当前选中节点在新视图中仍可见：

- 保持选中。
- 保持 detail panel。

如果当前选中的是 internal Turn，切换到默认视图后不可见：

- 左侧回退选中最近的 Conversation 或 Task。
- Detail panel 可以保留原 detail，但必须显示提示：当前 Turn 在默认视图中隐藏，可切换到调试视图查看。

第一版可使用更简单策略：

- 清除不可见 turn selection。
- 选中其父 Conversation。
- 在 detail 顶部显示提示。

### Decision 5：空 projection 不是空白页

如果某个 Task 或 Conversation 在默认视图没有 primary Step：

- 仍显示 Task / Conversation 节点。
- 子节点区域显示“默认视图无主执行 Step，切换调试视图查看完整 Turn”。

不得渲染为空白列表。

## UI Shape

顶部控件建议：

```html
<div class="trace-view-mode">
  <button data-trace-view="default">默认视图</button>
  <button data-trace-view="debug">调试视图</button>
</div>
```

类型筛选容器建议添加模式 class：

```html
<div id="typeFilters" class="debug-filter-strip">
```

由 `updateTraceViewModeControls()` 控制显示。

## Rendering Flow

```text
loadSession()
  -> rebuildAllGroupTurns()
  -> renderPage(activeView)
     -> renderSessionPage()
        -> renderTraceTree()
           -> buildTraceNodes()
           -> buildTurnViewProjection(traceViewMode, source)
           -> render Task / Conversation / Step-or-Turn nodes
```

`buildTraceNodes()` 可以继续负责 snapshot 和 task/conversation source 构造，但最终 Turn/Step 可见节点必须来自 projection。

## Edge Cases

- 没有 task segmentation：Conversation-first projection 渲染。
- 已确认 Task Trace：Task-first projection 渲染。
- default 视图某 Conversation 只有 internal Turn：保留 Conversation 节点和空状态提示。
- debug 视图启用类型筛选后，某 Conversation 被筛空：保留 Conversation 节点和筛选空状态提示。
- 当前选中 internal Turn 后切回 default：提示该 Turn 已隐藏。
- 搜索框和类型筛选同时存在时：搜索仍可过滤可见节点，但不得影响底层 projection。

## Test Strategy

- 静态测试：
  - 断言 `traceViewMode` 状态存在。
  - 断言双视图切换控件存在。
  - 断言 `renderTraceTree()` 使用 `buildTurnViewProjection`。
  - 断言默认视图隐藏 `typeFilters`，调试视图显示。

- DOM 测试：
  - 构造包含 user/thinking/tool/system/hook/snapshot 的 session。
  - 默认视图只显示 Step，不显示 ordinary internal。
  - 调试视图显示 Turn 和 internal。
  - 切换视图后不出现空白。
  - 选中 internal 后切回默认视图时出现提示或回退选择。

## Rollout

1. 先接入 UI 状态和双视图控件。
2. 再让 `renderTraceTree()` 消费 projection。
3. 最后处理筛选显示和选择回退。
4. 保持旧 Detail 逻辑可用，避免扩大本 change 范围。
