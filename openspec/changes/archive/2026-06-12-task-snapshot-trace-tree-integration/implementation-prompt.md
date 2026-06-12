# 修复 Prompt：Task 必须注入 Trace 树一级结构

## 背景

用户手动验收 `task-snapshot-trace-tree-integration` 时发现：确认 Task 切分后，`Session` 页面的 Trace 树仍然是：

```text
Tools / Skills Snapshot
会话
  Turn 1  [Task 1]
  Turn 2  [Task 1]
会话
  Turn 5  [Task 2]
```

这不符合本 change 的目标。确认切分后必须变成：

```text
Tools / Skills Snapshot
Task 1
  会话 1
    Turn 1
    Turn 2
Task 2
  会话 2
    Turn 5
```

`Task N` badge 只能作为未确认预览状态的辅助信息，不能作为 confirmed Task Trace 的结构替代。

## 已定位的问题

重点检查 `viewer/claude-log.html`：

1. `buildTraceNodes()` 现在的注释和实现是 `Snapshot -> Group -> Task -> Conversation -> Turn`，但 spec 要求 confirmed 后是 `Snapshot -> Task -> 会话 -> Turn`。source group 只能作为元信息或视觉标签，不能成为 Snapshot 和 Task 中间的树层。

2. `mapTaskSegmentsToTraceNodes()` 自己构造了 `turnByEventId`，只索引 `_eventId` 和 `uuid`。Task Segment 的 `startEventId/endEventId` 可能是 `main:<line>`、subagent file anchor、block anchor 或 message id。这里应该复用现有统一 lookup，例如 `lookupTurnByEventId()` / `turnNavigationIndex`，不要自建窄索引。

3. `mapTaskSegmentsToTraceNodes()` 用 `turn.index` 比较范围，并遍历所有 `allGroupTurns`。这会跨 group 污染，也会在不同 conversation 中产生错误范围。应该按目标 group 的 flat Turn 顺序计算 start/end 位置。

4. `renderTraceTree()` 的 standalone conversation 分支仍会给 Turn 渲染 `.turn-task-badge`。confirmed 后，Task 覆盖的 Turn 不应该通过 badge 表达所属 Task；应该出现在 Task 节点下面。

5. 当前 DOM 测试没有强断言 confirmed 后的真实树层级，所以这种错误能通过测试。

## 修复要求

请按 OpenSpec 更新后的 `task-snapshot-trace-tree-integration` 执行，尤其完成 tasks 9.1-9.10。

核心修复：

1. confirmed 后 `buildTraceNodes()` 必须生成：

```text
snapshot node
task node
  conversation node
    turn node
task node
  conversation node
    turn node
```

不要在 snapshot 和 task 之间插入 group 节点。group 可作为 `taskNode.groupLabels`、`conversationNode.groupId` 或节点副标题展示。

2. 如果存在 confirmed task segments，即使某个 Task 无法完整映射，也必须显示 Task 节点，并在 Task detail 中显示 degraded/unmappable 提示。不要因为映射失败就回退成 `会话 -> Turn + Task badge`。

3. Task 起止锚点解析必须支持：

- event id
- uuid
- message id
- block anchor
- `main:<line>`
- subagent file anchor

优先复用 `lookupTurnByEventId()` 或 `turnNavigationIndex` 已有索引。

4. Task 范围计算必须按 group 内 flat Turn 顺序做。若 start/end 在同一 group，取该 group 内 start/end 之间的 Turn；若跨 group，第一版可以标记 degraded，并按可映射部分展示。

5. confirmed 后，Task 覆盖的 Turn 行内不要再显示 `.turn-task-badge`。未确认预览时可以保留 badge 作为辅助跳转。

6. Task 定位开始/结束 Turn 时：

- confirmed：展开目标 Task + 目标会话，滚动并高亮 Task 下的 Turn。
- unconfirmed：使用普通 `会话 -> Turn` 定位。

## 必加测试

至少补以下 DOM 回归测试：

1. confirmed 后树结构中 Snapshot 后直接出现 Task 节点，Task 节点下有会话和 Turn。
2. confirmed 后被 Task 覆盖的 Turn 不只是显示 `Task N` badge；应在 Task 节点下面。
3. Task start/end 为 `main:<line>` file anchor 时，仍能映射出 Task 下的会话和 Turn。
4. confirmed 后 Task 覆盖的 standalone conversation 不再出现在 Task 外部；未覆盖会话可以进入 `Unassigned` 或等价区域。
5. Task 定位开始/结束 Turn 会展开 Task 和会话，并高亮目标 Turn。

完成后运行：

```bash
openspec validate task-snapshot-trace-tree-integration --strict
node tests/test_task_segmentation_dom.js
python3 -m pytest -q
```

如果某个测试命令不是当前项目实际命令，请使用项目已有等价命令，并在总结中说明。
