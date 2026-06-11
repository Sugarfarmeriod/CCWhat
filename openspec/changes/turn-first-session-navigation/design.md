## Context

`viewer/claude-log.html` 现在已经有 App Shell 和独立 `Session` / `Tasks` 导航。`Tasks` 页面可以展示规则切分结果，但 Task detail 仍主要暴露 `startEventId` / `endEventId`，例如 UUID 或 `main:242` 这类机器锚点。用户想核对任务边界时，需要从 Task 跳回原始 session，但当前定位按钮无法稳定驱动左侧导航，也没有一个面向人的 Turn 层作为中间锚点。

这次设计把两种视角明确分开：

- `Session` 页面是原始执行事实视角，按 `Turn 1 / Turn 2 / Turn 3` 浏览。
- `Tasks` 页面是任务切分和诊断视角，按 `Task 1 / Task 2 / Task 3` 浏览。

两者通过稳定导航索引关联：Task 起止事件先映射到 Turn，再由 Turn 定位到 Session 页面。

## Goals / Non-Goals

**Goals:**

- 在前端基于已加载 session entries 派生稳定 Turn 列表。
- `Session` 页面默认展示 Turn 列表和 Turn detail，不再把原始 event ID 作为主导航语言。
- `Tasks` 页面展示 `Turn N` 起止范围，并支持一键跳转到对应 Session Turn。
- 建立 `eventId`、`uuid`、`_gid:_fileLine`、`turnKey` 等锚点到 Turn 的统一映射。
- 在定位失败或目标被筛选隐藏时给出明确反馈，而不是静默无反应。
- 保留 Raw JSON / Raw Events 作为调试入口。

**Non-Goals:**

- 不修改 task segmentation 算法。
- 不修改 `/api/session` 或 `/api/task-segments` 后端协议。
- 不引入数据库、持久化标注或本地缓存格式变化。
- 不重做完整视觉品牌，不把 Task 页面合并进 Session 页面。
- 不实现人工修正 Task 边界；本 change 只解决展示和定位。

## Decisions

### Decision 1：Turn 作为前端派生模型

前端在 session 加载后基于完整 group entries 构建 Turn 列表，而不是要求后端返回 Turn。

Turn 模型建议包含：

```js
{
  turnKey: "main:turn:1",
  groupId: "main",
  label: "Turn 1",
  index: 1,
  rootEntryId: "main:10",
  startEntryId: "main:10",
  endEntryId: "main:18",
  entries: [...],
  userSummary: "...",
  assistantSummary: "...",
  toolCount: 5,
  errorCount: 1,
  taskIds: ["task-001"]
}
```

Turn 边界第一版按现有日志树语义派生：主会话和每个 subagent group 独立计数；每个非 tool-result 的 user message 作为一个 Turn root，直到下一个 Turn root 前的 entries 属于当前 Turn。没有明确 user root 的前置系统/元数据 entries 归入 `Turn 0` 或显示在 group metadata 中，避免打乱用户可读轮次。

### Decision 2：Session 页面采用三段式 Turn 浏览

`Session` 页面工作区保留当前 App Shell，但中间主列表改成 Turn List：

```text
Session
  Turn List
    Turn 1  用户摘要  [Task 1]  tools 4 errors 1
    Turn 2  用户摘要  [Task 1]  tools 2
    Turn 3  用户摘要  [Task 2]

  Turn Detail
    Overview
    User Text
    Assistant Text
    Tool Calls / Results
    Errors
    Raw JSON
```

这样 `Session` 页面回答“原始执行过程是什么”，`Tasks` 页面回答“这些过程被切成了哪些任务”。

### Decision 3：Task detail 隐藏机器 ID，优先展示 Turn range

Task 起止信息展示为：

```text
开始：Turn 3
结束：Turn 8
```

如果能映射到具体 entry，再在折叠调试信息中展示：

```text
startEventId: main:42
endEventId: main:91
```

按钮文案使用“定位开始 Turn”“定位结束 Turn”。用户不需要理解 UUID 才能完成观察。

### Decision 4：统一导航索引，不依赖当前可见 DOM

加载 session 后创建导航索引：

```js
navigationIndex = {
  byEventId: Map,
  byUuid: Map,
  byFileAnchor: Map,
  byTurnKey: Map
}
```

每个索引值指向：

```js
{
  groupId,
  turnKey,
  turnIndex,
  entryId,
  entryIndex,
  rawEventId,
  isSubagent
}
```

定位时先查索引，再更新应用状态：

1. 切换到 `Session` 页面。
2. 展开目标 group。
3. 选中目标 Turn。
4. 滚动并高亮 Turn header。
5. 如果具体 entry 当前可见，则再滚动并高亮 entry；否则提示被筛选隐藏。

这样定位不会因为搜索、类型筛选或 DOM 尚未渲染而失效。

### Decision 5：Task 与 Turn 双向标注

前端根据 task 的 `startEventId` / `endEventId` 映射出 turn range 后，为范围内 Turn 补充 `taskIds`。

- 在 `Session` 页面，Turn card 展示关联 Task badge。
- 在 `Tasks` 页面，Task detail 的 `Turns` tab 展示包含的 Turn 列表。
- 点击 Turn 中的 Task badge 可切到 `Tasks` 页面并选中对应 Task。

这不是合并页面，而是两个并行视角之间建立双向跳转。

### Decision 6：Raw Events 作为调试层保留

Raw Events 不消失，但优先级降低：

- `Session` 页面 Turn detail 中提供折叠 Raw JSON。
- 现有 Raw Events 入口继续用于查看原始 entries。
- Task detail 中的 Raw tab 继续展示原始 task JSON 和锚点。

这样既满足普通观察，又保留调试能力。

## Risks / Trade-offs

- [Risk] 现有 entries 格式来自 Claude Code / Codex / OpenCode，Turn root 判断可能不完全一致。  
  → Mitigation：第一版只做前端派生和 best-effort 映射；无法归类的 entries 放入 metadata/unknown turn，并在测试里覆盖 Claude 常见结构。

- [Risk] Task 边界可能落在 Turn 中间，展示为 Turn range 会降低精度。  
  → Mitigation：主展示用 Turn，折叠调试信息保留具体 `startEventId` / `endEventId`；定位时先到 Turn，再高亮具体 entry。

- [Risk] 搜索/类型筛选下目标 entry 不可见，用户可能误以为定位失败。  
  → Mitigation：定位到 Turn header，并显示“目标事件被当前筛选隐藏”的可见提示。

- [Risk] 单文件 HTML 继续增长，维护成本上升。  
  → Mitigation：本 change 不引入构建链，但要求把 Turn 构建、导航索引、渲染函数命名清晰，并增加静态回归测试锁住关键函数。

## Migration Plan

1. 新增 Turn 派生和导航索引 helper，不先替换 UI。
2. 改造 `Session` 页面渲染为 Turn List + Turn Detail。
3. 将 Task 起止事件映射为 Turn label，并替换 Task detail 的主展示文案。
4. 实现 Task-to-Turn 定位状态流转和高亮。
5. 为 Turn badge、定位失败提示、筛选隐藏提示补充 UI 状态。
6. 更新静态测试和 DOM 行为测试。
7. 本地手动验收：加载真实 session，切到 Tasks，点击开始/结束定位，确认跳到 Session 对应 Turn。

## Open Questions

- 是否需要把 `Turn 0` 暴露给用户，还是只作为内部容器承载系统/元数据 entries。
- `Session` 页面是否默认显示主会话 group，subagent group 作为可展开分组；第一版建议这样做。
- Turn label 使用中文“轮次 1”还是英文 `Turn 1`；第一版建议保留 `Turn 1`，与开发者工具风格一致。
