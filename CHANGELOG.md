# 更新日志 / Changelog

这里记录 codelenagent / ccwhat 的重要版本变化。版本号以 `pyproject.toml` 和 `ccwhat.__version__` 为准，发布标签使用 `v<version>`，例如 `v0.1.2`。

## v1.1.0 - 2026-06-13

### 新增手动任务切分 + 自动任务切分，支持人为微调

V1.1.0 新增手动任务切分，并与原有自动切分并列。用户既可以一键自动切分，也可以在 Session 会话树上手动框选范围创建 Task。自动切分的结果还支持人为微调：调整边界、拆分、合并、删除、修改标题和类型。编辑后可保存、撤销或导出 Overlay JSON。

---

## v1.0.0 - 2026-06-12

### 正式发布：Session Trace 双视图 + 自动任务切分闭环

V1.0.0 正式发布。相比 Preview 版，核心补齐了 Session 页面的双视图浏览能力和任务切分闭环。

### 新增

- **Session Trace 双视图切换**：顶部新增 `默认视图` / `调试视图` 切换控件。
- **默认视图**：只展示主执行链路 Step，隐藏普通内部事件。默认视图包含：
  - `Step N` 连续编号
  - 用户请求（user request）、思考过程（thinking）、Agent 文本回复（agent text）、工具调用（tool call）、工具结果（tool result）
  - 包含 error/warning/failed/denied 等异常信号的内部事件也会自动提升为 primary Step
- **调试视图**：展示完整 Turn 时间线，保留原始 `Turn N` 标签和时序，包括默认视图中隐藏的内部事件：
  - `permission-mode`、`last-prompt`、`PostToolUse` hook
  - `file-history-snapshot`、`queue-operation`
  - `system`、`context` 注入、`attachment` 元数据、`unknown` 事件
  - 调试视图下保留底层类型筛选（user/assistant/system/attachment/perm/fhs/queue/other）作为高级筛选
- **自动任务切分闭环**：任务切分完成后，Session Trace 自动切换为 `Task -> 会话 -> Step/Turn` 树形结构，无需额外点击确认。
- **Turn Detail 完整证据**：右侧详情区始终展示当前选中 Turn 的完整证据（不再受左侧筛选影响），包括完整 tool input/output、thinking 全文、internal event 结构化字段、可展开 raw JSON 和 entry/block 定位信息。
- **任务切分定位强化**：Task 起止事件可稳定映射回 Session Trace Turn，支持 OpenCode/Codex adapter 的 normalized event id 稳定性。

### 改进

- 默认进入 Session 页面，默认使用默认视图，减少首屏信息噪声。
- 类型筛选降级为调试视图下的高级筛选，默认视图不显示类型筛选栏。
- 搜索支持两步过滤：默认视图下搜索主执行 Step，调试视图下搜索完整 Turn + 类型筛选。
- 切换视图时，当前选中节点尽量保持选中；internal Turn 切回默认视图时自动回退到父会话并给出切换提示。
- 保留 Tasks 页面的确认状态机制，确认只影响 UI badge，不改变 Tree 结构。

---

## v1.0.0 preview - 2026-06-11

### 新增

- 发布 V1 preview版本：新增 Task Trace Workbench。
- 新增第一版规则任务切分能力，可从长 Session 中识别多个 Coding Task。
- Viewer 新增任务列表、任务详情、边界原因、Evidence、命令/错误、Raw JSON 等任务切分展示。
- 左侧导航升级为 App Shell 工作台，包含 Session、Tasks、Overview、Timeline、Req / Resp、Diff、Diagnostics、Export、Settings。

### 改进

- 默认仍进入 Session 页面，Tasks 由用户手动触发任务切分。
- 修复 Viewer 初始化递归问题，避免页面打开时栈溢出。
- 保留 Claude Code、Codex、OpenCode 三类 Agent 的日志查看、报告、时间线和任务切分入口。
- 改进 task 起止事件到原始日志 turn/event 的定位。

---

## v0.1.3 - 2026-06-09

### 新增

- 完成 Codex 报告生成链路的完整适配，元析报告和通用报告在 Codex 会话上均可正常生成。
- 至此，codelenagent 已全面支持三大主流 AI Coding Agent：**Claude Code（VS Code）**、**Codex** 和 **OpenCode**，日志查看、分析报告、时间轴、工具耗时、Agent 摘要等核心功能对三者均可用。

### 改进

- Codex 报告生成的协议解析和超时问题已修复。
- 三大 Agent 的 Analyzer 适配器统一收归 `ccwhat/analyzers/` 模块，结构更清晰。

---

## v0.1.2 - 2026-06-09

### 新增

- 完成 OpenCode 报告生成链路的第一版适配。
- OpenCode Analyzer 默认使用 `opencode run --format json`，并支持真实 JSONL 输出中的 `part.text`。
- OpenCode 本地 DB 日志接入元析报告和通用报告的数据管线。

### 改进

- 修复 OpenCode 数字时间戳归一化，工具事件可正确进入时间轴、阶段统计、柱状图和饼图。
- 修复通用报告 Mermaid 渲染失败时的 fallback 展示，保留原始 Mermaid 源码并区分语法失败和库未加载。
- 收紧通用报告 prompt 中的 Mermaid 输出约束，降低 OpenCode 生成非法 Mermaid 的概率。
- 增加 OpenCode 报告链路和 Mermaid fallback 的回归测试。

### 已知问题

- Codex 已接入多 Agent 日志/Analyzer 架构，但报告生成仍存在耗时和协议解析问题，下一步会继续适配 Codex。

## v0.1.1 - 2026-06-06

### 新增

- 新增多 Coding Agent 会话查看架构。
- 新增 Claude Code、Codex、OpenCode 本地日志 Adapter。
- 新增 `ccwhat web --agent <agent>`，支持按 agent 选择默认日志来源。
- 新增统一的 normalized events / turns / usage 数据结构，为后续跨 agent 展示做准备。

### 改进

- Web Viewer 保持 Claude Code 原有展示能力，同时可显示当前 agent 类型。
- `ccwhat -- <target>` 会根据启动目标推断 agent 类型，并把类型传给 Viewer。
- Codex 和 OpenCode 先按各自本地日志结构适配，不假设它们和 Claude Code JSONL 相同。

## v0.1.0 - 2026-05-28（初始版本）

### 新增

- Claude Code 本地会话日志查看。
- 请求 / 响应抓包记录。
- Web Viewer、导出、导入和基础诊断流程。
