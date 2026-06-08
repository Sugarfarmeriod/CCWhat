## Why

CCWhat 已经从 Claude Code 专用日志查看器演进到多 Coding Agent 会话查看器，但当前 Web Viewer 仍然更像早期 JSONL 日志列表，信息层级、导航方式和诊断工作流不够专业。

这次改造希望全面对标 LangSmith 的深色观测工作台体验，让用户在 README、手动演示和实际使用中都能感受到 CCWhat 是一个面向 Tracing / Debugging / Session Diagnosis 的产品，而不是简单日志页。

## What Changes

- 将 Web Viewer 重新设计为 LangSmith 风格的诊断工作台。
- 保留 Agent Log 和 Raw Req/Resp 两个页面的独立性，不把网络抓包页强行融合进本地日志页。
- 在 Agent Log 页面中引入更清晰的布局：
  - 左侧应用导航和 session/project 入口
  - 顶部 agent、project、session、搜索、过滤、导出等操作栏
  - 主区域以 trace/turn/event 表格或列表展示会话行为
  - 详情区域展示选中事件的 content、tool call、usage、raw JSON
- 使用已生成的 Open Design 设计稿作为实现输入，后续执行 Agent 不再重新设计，只负责落地到 `viewer/claude-log.html`。
- 保持现有 Claude Code、Codex、OpenCode 本地日志展示能力不回退。
- 保持搜索、类型过滤、导出、分析当前 Session、Raw Req/Resp 跳转等现有功能可用。
- 不引入 LangSmith 品牌资产，不复制 LangSmith 商标、Logo 或专有文案，只对标信息架构、视觉密度和交互风格。

## Capabilities

### New Capabilities

- `viewer-langsmith-redesign`: 定义 CCWhat Web Viewer 的 LangSmith 风格诊断工作台体验、页面结构、设计约束、功能保留和验收要求。

### Modified Capabilities

- `multi-agent-log-adapters`: Viewer 展示层必须继续支持 Claude Code、Codex 和 OpenCode 的 `main/subagents` 或 `events/turns/usage` 数据，不得因重设计破坏多 Agent 展示契约。

## Impact

- 主要影响：
  - `viewer/claude-log.html`
  - 可能影响 `viewer/server.py` 返回的轻量 metadata 字段，但不应大改 API
  - 可能影响前端 CSS、布局、渲染函数和交互状态管理
- Open Design：
  - 设计稿已生成：Open Design project `71acf6a9-38cc-40b4-bb00-f7200b01cdf4`
  - Artifact 文件：`ccwhat-viewer.html`
  - Preview URL：`http://127.0.0.1:55306/api/projects/71acf6a9-38cc-40b4-bb00-f7200b01cdf4/raw/ccwhat-viewer.html`
  - 设计稿只作为前端实现参考，不直接替代现有后端逻辑
- 测试和验收：
  - 需要手动验证 `ccwhat web --agent claude`
  - 需要手动验证 `ccwhat web --agent codex`
  - 需要手动验证 `ccwhat web --agent opencode`
  - 需要确认 Raw Req/Resp 页面仍可跳转和独立使用
  - 需要确认导出、搜索、过滤、详情查看不坏
