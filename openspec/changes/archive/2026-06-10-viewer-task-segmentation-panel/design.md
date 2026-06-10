## Context

`viewer/claude-log.html` 当前以左侧日志树 + 右侧 detail panel 展示 Claude session，并已有“分析当前 Session”按钮调用 `/api/analyze` 生成报告。第一版规则 Task 切分已经提供 `POST /api/task-segments`，返回 `tasks`、`summary`、`debugBoundaries`、evidence、file weights 和 boundary reasons。

本 change 的目标是把这个结构化结果展示到前端，用于真实 session 观察和规则调参。它不是算法 change，也不引入新的评测结论。

## Goals / Non-Goals

**Goals:**

- 在 Claude Log 页面提供“任务切分”入口。
- 对当前 session 调用 `/api/task-segments`，并在页面内存中按 `sessionId` 缓存结果。
- 在 detail panel 展示任务概览、task cards、task detail、evidence 和 boundary reasons。
- 支持重新切分，成功后覆盖缓存；失败时保留旧结果。
- 支持从 task detail 定位到起止事件附近的原始日志条目。
- 以调试和人工校准为核心，清楚展示规则为什么切分。

**Non-Goals:**

- 不修改 `ccwhat.task_segments` 切分算法。
- 不做 success/failed/partial_success 评测；显示 API 返回的 `status`，第一版通常为 `unevaluated`。
- 不把 task segment 结果写入后端文件、localStorage 或导出包。
- 不重构整个 viewer 布局，不替换现有日志树。
- 不新增外部 JS 依赖。

## Decisions

### Decision 1：复用 detail panel 承载任务视图

第一版不新建三栏页面，也不重构左侧日志树。点击“任务切分”后，右侧 `detailPanel` 显示：

```text
Task Segmentation Header
  summary / actions

Task Cards
  task title / type / status / evidence counts / ambiguity

Selected Task Detail
  overview
  evidence panel
  boundary reasons
  file weights
  debug / raw JSON
```

这样可以和现有“分析报告展示”“日志详情展示”共存：用户点击日志条目时 detail panel 回到原始日志详情；再次点击“任务切分”恢复缓存视图。

### Decision 2：新增独立 task segmentation 前端状态

前端新增：

```js
const taskSegmentReports = {};
let taskSegmentsInFlight = false;
let selectedTaskSegmentId = null;
```

缓存 key 使用 `sessionId`。缓存仅存在当前页面生命周期，不写入 `localStorage`。切换 session 时按钮文案根据缓存状态更新。

### Decision 3：按钮行为与分析报告分开

新增按钮 `taskSegmentsBtn`，不复用 `analyzeBtn`。按钮状态：

- 没有 session：disabled，文案“任务切分”
- 有 session、无缓存：文案“任务切分”
- 有 session、有缓存：文案“查看任务切分”
- 请求中：disabled，文案“切分中…”

报告分析和任务切分是两个不同入口，避免用户混淆“LLM 分析报告”和“规则切分结果”。

### Decision 4：Task card 以 evidence counts 为主

Task card 只展示最关键的可扫描信息：

- task id / title
- task type
- status
- filesChanged count
- commands/testCommands count
- errors count
- subagentIds count
- finalClaim 是否存在
- ambiguous badge

第一版不在 card 中展示长文本，避免把右侧 detail panel 变成日志堆积。

### Decision 5：Task detail 分为固定区块

点击 task card 后，详情区展示：

1. **Overview**：起止事件、类型、状态、final claim。
2. **Evidence**：filesRead、filesChanged、commands、testCommands、errors、subagentIds、todosUser。
3. **Boundary Reasons**：逐条展示 `boundaryReasons`，保留原始分数字符串。
4. **File Weights**：按权重降序展示文件权重。
5. **Raw JSON**：折叠展示该 task 原始 JSON。

每个区块使用现有 `mkSection` 折叠组件风格，保持页面一致。

### Decision 6：定位原始日志使用 event id best-effort

API 返回 `startEventId` / `endEventId`，如 `main:12` 或 `agent-abc:4`。前端基于现有 `allEntries` 做 best-effort 映射：

- `main:<line>` → `_gid === "main"` 且 `_fileLine === line`
- `agent-<id>:<line>` → subagent group 中 `_fileLine === line`

详情中提供“定位开始事件”“定位结束事件”按钮。若找不到对应条目，按钮 disabled 或显示不可定位提示。

### Decision 7：错误和空结果要可理解

请求失败时显示错误状态，并保留旧缓存；空结果显示“未识别到任务片段”。这对真实 session 调参很重要，不能只静默失败。

### Decision 8：测试以静态回归为主

当前前端是单 HTML 文件，第一版继续采用静态回归测试，断言：

- 按钮存在。
- 请求 `POST /api/task-segments` 且 body 只包含 `sessionId`。
- 存在缓存对象和 in-flight 状态。
- 存在 task card/detail/evidence/boundary rendering 函数。
- 存在定位 event id 的 helper。
- 不写入 localStorage。

## Risks / Trade-offs

- 右侧 detail panel 承载较多内容，复杂 session 可能较长 → 使用可扫描 card + 折叠区块，避免一次性展开全部细节。
- event id 与前端日志条目映射可能失败 → best-effort 定位，并在失败时明确显示不可定位。
- 真实 session 结果可能暴露切分算法问题 → 这是本 change 的目的；保留 debug boundaries 和 raw JSON 以支持调参。
- 与分析报告入口并存可能增加按钮数量 → 文案明确区分“任务切分”和“分析当前 Session”。

## Migration Plan

1. 在 `viewer/claude-log.html` 顶栏新增任务切分按钮。
2. 新增 task segment 前端状态、缓存、请求和重新切分逻辑。
3. 新增任务概览、task card、task detail、evidence、boundary reasons 和 raw JSON 渲染。
4. 新增 event id 到日志条目的定位 helper。
5. 新增样式和静态回归测试。
6. 用本地 server + 真实 session 手动观察 `/api/task-segments` 前端展示。

## Open Questions

- 是否需要在后续 change 中把任务视图升级为左侧独立 Tab，而不是复用 detail panel。
- 是否需要后续支持人工标注“切分正确/错误”并导出为规则校准样本。
