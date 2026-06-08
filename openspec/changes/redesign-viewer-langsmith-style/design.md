## Context

当前 `viewer/claude-log.html` 是一个单文件 Web Viewer，承载了 Agent Log 的布局、样式、数据加载、列表渲染、详情渲染、导出弹窗和 Raw Req/Resp 跳转。它已经支持 Claude Code 的原始 `main/subagents` 展示，也开始支持 Codex/OpenCode 的 normalized `events/turns/usage` 展示。

用户希望这次全面对标 LangSmith 的观测产品气质：深色、专业、信息密度高、侧边栏明确、trace/table 优先、详情面板清楚。OpenSpec 负责定义这次改造的边界和验收条件。Open Design 第一阶段已经完成，后续执行 Agent 必须读取既有设计稿并落地实现，不需要重新生成设计。

已完成的 Open Design 设计输入：

- Project ID: `71acf6a9-38cc-40b4-bb00-f7200b01cdf4`
- Artifact: `ccwhat-viewer.html`
- Preview URL: `http://127.0.0.1:55306/api/projects/71acf6a9-38cc-40b4-bb00-f7200b01cdf4/raw/ccwhat-viewer.html`
- Run ID: `f07de3ba-f694-4a29-8576-8f3e688df9fb`
- Agent: `opencode`

## Goals / Non-Goals

**Goals:**

- 将 Agent Log 页面改造成 LangSmith 风格的诊断工作台。
- 保留多 Agent 支持：Claude Code、Codex、OpenCode 都必须能进入同一套 UI。
- 强化本地日志页面的信息层级：
  - agent / project / session 上下文
  - session/turn/event 浏览
  - tool call、reasoning、usage、raw JSON 详情
  - Raw Req/Resp 作为独立页面入口
- 使用已完成的 Open Design 设计稿作为视觉和信息架构参考。
- 前端实现尽量保持单文件可维护，不引入大型前端构建链。

**Non-Goals:**

- 不复制 LangSmith 的 Logo、品牌名、商标、专有文案或完整视觉资产。
- 不把 Agent Log 和 Raw Req/Resp 融合成同一个页面。
- 不在这次改造中新增复杂后端 API 或重写 adapter。
- 不把 `viewer/claude-log.html` 改造成 React/Vite 项目，除非后续单独开 change。
- 不在本次设计中默认展示没有公式的 cache hit rate。

## Decisions

### Decision 1: 采用“左侧导航 + 顶部上下文栏 + 主 trace 表格 + 详情面板”的工作台布局

理由：LangSmith 的核心体验是从 workspace/application 导航进入 tracing，再从 run/trace 表格进入详情。CCWhat 对应的核心体验是从 agent/project/session 进入 turn/event，再查看工具调用、内容和 raw JSON。

替代方案：
- 保留现有左右两栏日志列表：实现成本低，但不够产品化。
- 做成聊天时间线：更适合阅读对话，不适合诊断工具调用和 usage。

### Decision 2: 对标 LangSmith 的产品气质，不复制品牌

视觉方向：
- 深色背景，近黑主画布。
- 低饱和蓝色作为主要操作和选中态。
- 细边框、低圆角、高密度表格。
- 使用小字号、mono 数字、状态 badge 和 compact controls。
- 页面看起来像 observability / tracing 工具，而不是营销页或聊天应用。

### Decision 3: 保留 Raw Req/Resp 独立页面

Agent Log 来自本地 agent 会话记录，Raw Req/Resp 来自网络抓包。两者数据来源、字段含义和使用场景不同。UI 可以提供跳转和上下文提示，但不得在本次改造中强行合并。

### Decision 4: Open Design 作为已完成的设计输入，不作为最终代码来源

Open Design 输出的 artifact 用于确定布局、视觉层级、配色和交互结构。最终实现仍落在 `viewer/claude-log.html`，并以现有 API 和功能为准。

执行 Agent 必须：
- 读取 Open Design artifact `ccwhat-viewer.html`。
- 提取布局、配色、密度、控件状态、详情面板和 usage 展示方案。
- 将这些方案映射到现有 `viewer/claude-log.html` 的真实数据加载和渲染逻辑。
- 不再启动新的 Open Design 设计生成，除非用户明确要求重新设计。

### Decision 5: 先改 Viewer 外观和展示结构，不重写数据模型

后端 adapter 已经提供 `main/subagents/events/turns/usage`。这次前端应优先消费已有数据，并在必要时做轻量兼容判断。

## Risks / Trade-offs

- [Risk] 单文件 HTML 继续变大，维护难度增加。  
  Mitigation: 本次先保持单文件，后续如复杂度继续上升，再单独开 change 拆分前端模块。

- [Risk] 过度追求 LangSmith 相似度导致 CCWhat 自己的功能不清楚。  
  Mitigation: 只对标布局、信息密度和诊断工作流，不复制品牌资产。

- [Risk] 设计稿与现有后端数据不完全匹配。  
  Mitigation: OpenSpec 明确要求实现以现有 API 为准，设计稿只是视觉参考。

- [Risk] 移动端空间不足。  
  Mitigation: 以桌面诊断工具为主，移动端要求不重叠、可滚动、可选择 session，但不追求完整多栏体验。

## Migration Plan

1. OpenSpec proposal/design/spec/tasks 已完成。
2. Open Design 设计稿已完成，并保存在 `ccwhat-viewer.html` artifact 中。
3. 执行 Agent 读取该 artifact 和本 change 的 spec/tasks。
4. 实现 `viewer/claude-log.html` 的布局和样式改造。
5. 运行现有测试并手动验证 Claude/Codex/OpenCode。
6. 如出现问题，可回退本次前端文件改动，不影响 adapter 后端架构。

## Open Questions

- 实现时是否需要微调设计稿中的导航命名，以更贴近当前 CCWhat 页面实际功能？
- 是否需要在实现阶段补一张 README 截图，还是等下一版统一补？
