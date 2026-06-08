## MODIFIED Requirements

### Requirement: 非 Claude Agent Log 展示
系统 MUST 支持基于 normalized events/turns 展示 Codex 和 OpenCode session，并在 LangSmith 风格 Viewer 中保持可诊断的信息层级。

#### Scenario: Session API 返回非 Claude 兼容壳
- **WHEN** 前端请求 Codex 或 OpenCode session
- **THEN** API 必须返回 `main: []`、`subagents: []`、`events` 和 `turns`，不得伪装 Claude 原始结构

#### Scenario: 前端展示 turns
- **WHEN** session 数据没有 Claude `main/subagents` 但包含 `turns`
- **THEN** 前端必须展示 normalized turns 的基础内容、工具调用、reasoning 和 usage

#### Scenario: 前端展示 events
- **WHEN** session 数据没有可用 `turns` 但包含 `events`
- **THEN** 前端必须展示 normalized events 的基础列表

#### Scenario: LangSmith 风格展示 normalized 数据
- **WHEN** 前端展示 Codex 或 OpenCode 的 `events` 或 `turns`
- **THEN** 页面必须用与 Claude Code 一致的工作台布局展示 role、kind、summary、tool call、usage 和 raw JSON，不得退回到只显示原始 JSON

#### Scenario: Req/Resp 页面保持独立
- **WHEN** 展示 Codex 或 OpenCode 本地日志
- **THEN** 系统必须保持 Req/Resp 页面独立，只允许作为跳转或补充来源
