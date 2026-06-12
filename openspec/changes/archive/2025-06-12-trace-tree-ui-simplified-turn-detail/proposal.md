## Why

Change 1 已经将数据层调整为 `Trace -> 会话 -> minimal Turn`。现在需要把 Session 页面从平铺 Turn 卡片升级为左侧树状 Trace UI，并把右侧详情收敛成极简可观察内容，避免继续展示过多诊断字段和混合执行片段。

本 change 是 Trace 树重构的第二步：只做 `Trace -> 会话 -> Turn` 的 UI 表达和 Turn 右侧简化卡片，不做 Task 注入，不做 Tools / Skills Snapshot。

## What Changes

- Session 页面左侧主区域改为 Trace 树。
- 树中展示 group、会话、minimal Turn 三层结构。
- 会话节点可展开/折叠，展示会话 label、用户请求摘要、Turn 数量。
- Turn 节点展示 Turn label、kind badge、简短内容摘要。
- 点击会话节点，右侧展示会话级摘要。
- 点击 Turn 节点，右侧只展示两个核心区块：
  - Agent 响应
  - 原始 JSON
- Turn detail 必须只展示当前 minimal Turn 的内容，不混入同一会话或同一原始 entry 的其他 Turn 内容。
- 保留现有 type filter/search 的基本行为，但它们只影响树中节点的可见/隐藏状态，不改变会话和 Turn 的稳定编号。
- 不新增 Task 树顶层、不展示 Tools / Skills Snapshot、不做复杂 evidence/diagnostics。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 将 Session 页面从平铺 Turn 列表改为基于 Conversation/minimal Turn 数据层的 Trace 树 UI，并简化右侧 Turn detail。

## Impact

- 主要影响 `viewer/claude-log.html` 的 Session 页面渲染、左侧节点选中状态、右侧 detail 渲染和导航/定位。
- 需要更新前端静态测试和 DOM 行为测试，覆盖树结构、会话折叠、Turn 选中、右侧极简详情和搜索/filter 行为。
- 不修改后端 API、不修改 task segmentation 算法、不实现 Task 注入和 Tools / Skills Snapshot。
