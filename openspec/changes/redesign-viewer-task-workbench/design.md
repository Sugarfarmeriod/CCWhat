## Context

CCWhat / Agent Session Workbench 面向开发者，用于观察和诊断 Claude Code、Codex、OpenCode 等 AI Coding Agent 的真实执行过程。当前 V0 已能查看 session 日志、工具调用、Subagent 日志、原始请求响应和导出数据，但界面仍以 Raw Events 日志树为中心。

V1 的核心是 Task Trace：一个长 session 需要拆成多个真实 coding task，并围绕每个 task 展示用户意图、执行过程、文件改动、命令、测试、错误、边界原因和任务状态。旧布局继续修补会让 task 视图和 raw event 视图互相挤压，因此需要升级为 Task-first 的桌面端工作台。

设计参考为 `/Users/elon-ge/Downloads/index.html` 的 OpenDesign 原型。该原型提供 App Shell、左侧一级导航、顶部上下文栏、Tasks 双栏工作区、Overview 指标、Diff、Diagnostics、Export 等结构。本 change 采用其信息架构与视觉方向，但实现时应复用当前 viewer 的数据源、接口和页面能力。

## Goals / Non-Goals

**Goals:**

- 默认进入当前 session 的 `Tasks` 页面，把 Task Trace 作为主工作流。
- 建立稳定的 App Shell：左侧一级导航、顶部 context bar、主工作区页面。
- 将 Raw Events 从全局左侧树降级为一个证据页面，保留按 turn 展示和原始日志查看能力。
- 定义 canonical navigation target，使 task、turn、event、file、command、req/resp、diff 之间可以稳定跳转。
- 为 V0→V1 提供清晰页面分工：Overview、Tasks、Timeline、Sessions、Raw Events、Req / Resp、Diff、Diagnostics、Export、Settings。
- 保持开发者工具风格：高信息密度、克制配色、清晰边界、可扫描。

**Non-Goals:**

- 不实现完整 Dataset Builder、Offline Eval Runner、Prompt Optimizer 或 RL 数据导出。
- 不改变 task segmentation 核心算法。
- 不把 OpenDesign HTML 作为独立静态页直接塞入项目。
- 不做营销官网、大屏展示或聊天软件式布局。
- 不一次性重写所有后端 API。

## Decisions

### 1. App Shell 取代 Raw Events 全局树

页面 SHALL 使用固定左侧一级导航、顶部 context bar 和主工作区。左侧不再展示当前 session 的 user turn 树；Raw Events 树只在 `Raw Events` 页面内部出现。

理由：

- V1 的默认对象是 Task，不是日志 entry。
- 左侧需要承载跨页面功能导航，而不是被单个 session 的原始事件占用。
- Raw Events 仍重要，但它是证据视图，不是全局导航。

### 2. 左侧导航按工作流分组

建议导航结构：

- 工作台：`Tasks`、`Overview`、`Timeline`、`Sessions`
- 证据：`Raw Events`、`Req / Resp`、`Diff`
- 诊断：`Diagnostics`
- 数据：`Export`
- 底部：`Settings`

`Tasks` SHALL 默认 active。`Overview` 不作为默认页，因为 V1 用户最需要先看到任务拆分是否合理。

### 3. 顶部 context bar 只放全局上下文

顶部只保留 Agent、Project、Session、Search、Refresh。分析、导出、重新切分、Diff 筛选、诊断筛选等动作 SHALL 放在对应页面内部。

Agent、Project、Session 应是可切换的 selector 或 selector-like 控件；Search 是全局搜索入口，应覆盖 tasks、turns、events、files、commands。

### 4. Tasks 页面是主工作台

Tasks 页面采用 Task List + Task Detail 双栏布局：

- Task List 展示任务卡片和关键状态，支持选择、筛选、搜索和排序。
- Task Detail 展示所选 task 的 Overview、Evidence、Turns、Files & Diff、Commands、Raw。

Task Detail 不应把所有信息挤在一个长面板里。命令、测试、错误必须有独立区域，避免 Evidence 区变成无法扫描的混合日志。

### 5. Canonical Navigation Target 是第一阶段基础能力

所有跨页面定位都应基于统一导航目标，而不是临时解析字符串。建议前端内部建立以下结构：

```ts
type NavTarget = {
  kind: 'task' | 'turn' | 'event' | 'file' | 'command' | 'reqresp' | 'diff';
  sessionId: string;
  taskId?: string;
  turnKey?: string;
  eventId?: string;
  entryIdx?: number;
  filePath?: string;
  commandId?: string;
  requestId?: string;
};
```

实现上可以先在前端构建 alias index：

- `eventId -> entryIdx`
- `main:<line> -> entryIdx`
- `agent-<id>:<line> -> entryIdx`
- normalized event `id/eventId -> entryIdx`
- `message.id/uuid/tool_use_id -> entryIdx`
- `entryIdx -> turnKey`
- `taskId -> task`

这能解决旧 change 暴露的问题：task 的 `startEventId/endEventId` 在 Claude 行号型事件和 Codex/OpenCode normalized events 中都必须可定位。

### 6. 证据页面支持 Task Scope 和 Session Scope

`Raw Events`、`Diff`、`Req / Resp`、`Diagnostics`、`Export` 都应支持至少两种上下文：

- Session scope：从左侧导航直接进入时展示整个 session。
- Task scope：从 Tasks 页面跳转时聚焦当前 task 相关证据。

第一版可以用前端状态保存 `activeTaskId` 和 `activeNavTarget`，不需要后端持久化。

### 7. 迁移策略

不要一次删除旧功能。实现应先引入 App Shell，并把现有能力迁移到新页面：

1. 保留现有 API 和数据加载。
2. 新增工作台级状态：active view、active task、active nav target。
3. 将旧原始事件列表移动到 `Raw Events` 页面。
4. 将 task segmentation panel 重构为 `Tasks` 页面。
5. 将 analyze/export/req-resp/diff 入口迁移到对应页面。

## Risks / Trade-offs

- [Risk] 大改版范围过大，容易把 UI 重构和数据模型修复混在一起。  
  Mitigation: tasks 中先实现 canonical navigation target，再实现页面迁移。

- [Risk] 旧 viewer 的 Raw Events 能力在迁移中丢失。  
  Mitigation: Raw Events 页面必须先复用旧列表能力，再逐步优化样式。

- [Risk] 新导航项过多导致 V1 显得不聚焦。  
  Mitigation: 左侧只放 V0→V1 必需页面；Dataset/Eval 只在 Export 中弱提示，不进主导航。

- [Risk] OpenDesign 原型与真实数据结构不完全一致。  
  Mitigation: 原型只作为视觉和信息架构参考，真实实现以 `/api/session`、`/api/task-segments`、req/resp、diff 数据为准。

- [Risk] canonical navigation target 初版无法覆盖所有 adapter。  
  Mitigation: 显示不可定位状态和 debug alias 信息；测试覆盖 Claude line-based 与 normalized event id 两类路径。
