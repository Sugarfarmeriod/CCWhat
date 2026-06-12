## Why

当前 viewer 已经有独立的 `Tasks` 页面，但 `Session` 页面仍偏向原始 event/UUID 展示，用户在任务切分结果和原始执行过程之间对照时成本很高。尤其是 Task detail 中展示 `startEventId` / `endEventId` 这类机器 ID，且定位按钮无法稳定跳到左侧对应轮次，导致“任务分析视角”和“原始事实视角”没有形成闭环。

这次 change 的目标是把 `Session` 页面升级为 Turn-first 的原始执行浏览器，并让 `Tasks` 页面用人类可读的 Turn 作为定位锚点：Task 负责诊断，Session 负责核对证据，两者并行但强关联。

## What Changes

- `Session` 页面改为以 `Turn 1 / Turn 2 / Turn 3` 为主列表，而不是优先暴露原始 event 编号或 UUID。
- 每个 Turn 汇总展示用户消息、助手回复、工具调用数量、错误数量、关联 Task badge 和条目数量。
- 点击 Turn 后，右侧展示该 Turn 的详情，包括用户文本、助手文本、工具调用、工具结果、错误、元数据和折叠 Raw JSON。
- `Tasks` 页面中的起止位置展示为 `Turn N`，原始 `eventId` 仅作为调试信息折叠展示。
- `Tasks` 页面定位按钮改为“定位开始 Turn / 定位结束 Turn”，点击后切换到 `Session` 页面，展开并高亮对应 Turn，必要时再高亮 Turn 内具体 event。
- 前端维护稳定的 `eventId/uuid/turnKey -> group/turn/entry` 导航索引，定位不依赖当前搜索或类型筛选后的可见列表。
- 保留 Raw Events 能力，但它成为 `Session` 页面里的调试层或独立 Raw Events 入口，不再作为用户默认理解 session 的主路径。
- 不改变后端 task segmentation 算法，不改变 `/api/task-segments` 返回格式；本 change 只在前端派生 Turn 视图和导航映射。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 修改 viewer 的 Session/Tasks 交互契约，新增 Turn-first session 浏览、Task-to-Turn 定位和人类可读 Turn 标签。

## Impact

- 主要影响 `viewer/claude-log.html` 的前端状态、Session 页面渲染、Task detail 渲染和定位 helper。
- 需要补充/调整前端静态回归测试和 DOM 行为测试，覆盖 Turn 标签、Turn detail、Task 起止 Turn 展示和定位联动。
- 不新增外部 JS 依赖，不修改 Python 后端 API，不改变 task segmentation 数据结构。
