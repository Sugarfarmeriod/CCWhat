## Context

`turn-first-session-navigation` 引入了 `Session` 页的 Turn-first 展示。后续修复已经把 type filter click handler 改成调用 `renderPage(workbenchState.activeView)`，但 Turn 渲染函数仍使用完整 `allTurnEntries` 输出内容：

- `renderTurnList()` 的 meta badge 使用 `turn.entryCount / turn.toolCount / turn.errorCount`，这些是未筛选计数。
- `buildTurnDetailHtml()` 虽然计算了 `visibleCount` 并显示 hint，但用户消息、助手回复、工具调用和错误仍来自完整 Turn entries。

因此用户点击 `user / assistant / system / ...` 后，页面结构重渲染了，但可见内容基本不变。

## Goals / Non-Goals

**Goals:**

- 让 type filter 在 Turn-first Session 页面中产生清晰、可见、可预测的效果。
- 保持 Turn 结构稳定，不因筛选改变 Turn 编号或边界。
- 让 Turn detail 的主体内容严格使用当前筛选后的 visible entries。
- 在全部类型取消或某个 Turn 被完全隐藏时给出明确提示。
- 增加行为测试覆盖真实点击筛选场景。

**Non-Goals:**

- 不把 `Turn` 做成 `user/assistant/system` 同级 filter。
- 不改变 Turn 边界算法。
- 不改变 Raw Events 页面筛选行为。
- 不引入新的视图模式切换控件。

## Decisions

### Decision 1：Turn 结构不被 type filter 删除

Turn 是 Session 的结构层，type filter 是 Turn 内 event 的显示层。即使当前筛选没有任何 event 可见，Turn card 仍保留，避免用户误以为 session 消失。

### Decision 2：所有 Turn detail 主体内容基于 visible entries

`buildTurnDetailHtml()` 中的用户消息、助手回复、工具调用、错误区块均从：

```js
const visibleTurnEntries = allTurnEntries.filter(entryMatchesFilter)
```

派生。Raw JSON 继续保留完整 entries，但标题明确显示 full/raw 语义。

### Decision 3：Turn card 使用筛选后的可见计数

Turn card 显示：

- visible entries 数
- visible tools 数
- visible errors 数
- hidden entries 数

这样用户点击 filter 后，即使 Turn card 仍存在，也能看到计数变化。

### Decision 4：筛选为空时显示空态提示

当某个 Turn 的 `visibleTurnEntries.length === 0` 时，Turn detail 不展示完整用户/助手/工具内容，而是展示“当前筛选隐藏了该 Turn 的全部事件”。这解决“按钮点了没变化”的核心体验问题。

## Risks / Trade-offs

- [Risk] Turn card 保留但内容为空，用户可能误解为 filter 没有移除 Turn。  
  → Mitigation：在卡片和 detail 上显示 hidden count / hidden hint，明确筛选只作用于 event 内容。

- [Risk] Raw JSON 仍展示完整 entries，与筛选后的 detail 不一致。  
  → Mitigation：Raw JSON 放在折叠区，并标注完整原始 entries，用于调试而非主阅读。

- [Risk] 现有 DOM 测试只检查函数存在，无法防止行为回归。  
  → Mitigation：新增点击 filter 的 DOM 行为测试，断言 detail 内容真实变化。
