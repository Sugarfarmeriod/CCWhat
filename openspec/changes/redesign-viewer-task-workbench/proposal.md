## Why

当前 viewer 仍以原始日志树为中心，已经无法承载从 Session 到 Task 的核心工作流。V1 需要把多轮 Agent session 自动拆成真实 coding task，并围绕 task 展示边界、证据、文件改动、命令、测试、错误和诊断结果，因此需要把界面从 Session Log Viewer 升级为 Task-first 的 Agent Session Workbench。

## What Changes

- 将 Claude Log viewer 重构为桌面端 App Shell：左侧一级功能导航、顶部全局上下文栏、主工作区按功能页面切换。
- 默认进入当前 Session 的 `Tasks` 页面，而不是 Raw Events 页面。
- 左侧导航改为一级功能导航，包含 `Tasks`、`Overview`、`Timeline`、`Sessions`、`Raw Events`、`Req / Resp`、`Diff`、`Diagnostics`、`Export`、`Settings`。
- 顶部只保留全局上下文：Agent、Project、Session、Search、Refresh；具体功能按钮进入对应页面。
- Tasks 页面采用 Task List + Task Detail 的主工作区布局，展示任务拆分结果、边界依据、证据链、turn 摘要、文件 diff、命令测试、原始事件跳转和调试 JSON。
- 引入 canonical navigation target 模型，使 task 的 start/end、evidence、turn、command、error 都能稳定定位到 Raw Events / Diff / Req-Resp 等证据视图。
- 保留现有 V0 能力：原始日志、工具调用、Subagent 日志、原始请求响应、Diff、Export，但将它们收敛为 Task-first 工作台中的证据页面。
- 吸收并取代 `improve-task-segmentation-navigation` 中的旧界面局部修补需求；后续不再基于旧 Raw Event Tree 全局布局继续修补。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `session-viewer`: 将现有 viewer 从日志查看器重构为 Task Trace Workbench，新增 task-first 页面结构、稳定证据定位模型和多页面工作台导航。

## Impact

- 影响代码：主要是 `viewer/claude-log.html` 的布局、导航、Task 页面、Overview、Raw Events、Diff、Diagnostics、Export 视图，以及必要的前端状态与导航 helper。
- 影响测试：需要新增/更新前端静态测试和必要 DOM 交互测试，覆盖默认页面、导航结构、Tasks 页面、canonical navigation target、Raw Events 定位、Diff/Diagnostics/Export 页面入口。
- 设计参考：`/Users/elon-ge/Downloads/index.html` 中的 OpenDesign 原型，作为布局、信息架构和视觉密度参考，不要求逐像素复刻。
- 行为边界：不修改 task segmentation 规则算法；不引入离线 eval runner；不实现 Dataset Builder 的完整流程；不展示完整 V2-V7 路线，只为 V0→V1 做界面升级。
