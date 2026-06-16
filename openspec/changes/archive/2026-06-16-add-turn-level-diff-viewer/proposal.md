## Why

当前 Viewer 的 `Diff` 入口只汇总 task evidence 中的已读/已改文件，无法帮助用户在 Session 观测界面里理解相邻 turn 之间发生了什么变化。用户需要的是面向阅读和调试的 turn-level diff，而不是 Dataset 导出阶段的 task-level 文件改动证据。

## What Changes

- 将主 Viewer 中的 `Diff` 定义为 turn-level observability 功能，比较当前 turn 与前一个可比较 turn 的可读变化。
- 在 `Session` 观测界面的 Turn/Step 详情操作区提供 `Diff with Prev` 入口，点击后打开弹层卡片，而不是把 diff 常驻嵌入详情。
- 弹层采用固定槽位对照体验：顶部显示 `Turn A -> Turn B`、上一组/下一组导航、baseline 选择器和关闭按钮；正文始终按 `thinking`、`text`、`tool call`、`tool result` 四个槽位从上到下展示。
- 每个槽位都固定展示左侧 baseline 和右侧 current；即使某个槽位无变化或为空也保留该行，避免用户每次重新理解版式。
- 对修改内容使用左右 `OLD` / `NEW` 对照和行级高亮；新增、删除、修改内容使用清晰的颜色和 badge；无变化内容不染色，左右照常展示。
- 槽位内容不得用省略号或截断作为最终展示；长 thinking、text、tool call 或 tool result 必须通过块内滚动或展开方式完整可读。
- 默认 diff 不展示 metadata、parameters、system prompt、commands、files 或 errors 等噪声字段；这些内容保留在原始 JSON / debug 视图中查看。
- 左侧 `Diff` 页面从 task 文件汇总升级为当前 session 的 turn diff 入口/总览，点击条目应打开对应 Turn 的 diff 弹层或跳转到对应 Turn 后打开弹层。
- 保留 `req-resp.html` 中的 network messages diff，不纳入本 change。
- 保留 Task Dataset 的 `changes` / `patches` 导出证据，不把前端 turn diff 建立在 Dataset 构建链路上。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 增加主 Viewer 的 turn-level diff 展示要求，并明确该 diff 不依赖 task segmentation 或 Task Dataset。

## Impact

- 主要影响 `viewer/claude-log.html` 的 Session 详情操作区、diff 弹层渲染、左侧 `Diff` 页面和前端状态计算。
- 可能新增或调整前端静态/DOM 回归测试，覆盖 `Diff with Prev` 按钮、弹层、左右对照、baseline 选择、空态和不依赖 Dataset 的行为。
- 不新增后端 API；第一版基于当前 session 已加载的前端事件/turn projection 计算 diff。
- 不修改 `ccwhat/task_dataset/*` 的 Dataset 构建、保存、导出格式。
