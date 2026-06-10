## Context

CCWhat 的 viewer 原本是 Claude Log 样式的本地日志查看器。多 Agent adapter 和 task segmentation 加入后，界面需要升级，但第一阶段不能丢掉旧版最核心的能力：选择一个 session 后立即查看本地日志。

上一版改造把导航扩展成完整 workbench，但 Session 展示没有成为第一等页面，导致用户点击 `Sessions` 后看不到当前 session 的具体内容。这个设计方向需要收敛。

## Goals / Non-Goals

**Goals:**

- 默认进入 `Session` 页面。
- 用户选择 session 后，`Session` 页面必须展示旧版日志树和详情区域。
- `Session` 页面必须支持现有本地日志查看能力：
  - turn 分组
  - entry 列表
  - entry detail
  - 类型筛选
  - 搜索过滤
  - canonical event 定位
- `Tasks` 页面必须支持任务切分入口和已有 Task List + Task Detail。
- Task 的 start/end/evidence 跳转必须跳回 `Session` 页面并定位原始 entry。
- 左侧导航第一阶段只把 `Session` 和 `Tasks` 作为核心模块。

**Non-Goals:**

- 不要求实现完整 Overview。
- 不要求实现 Timeline。
- 不要求迁移 Raw Req/Resp。
- 不要求实现 Diff。
- 不要求实现 Diagnostics。
- 不要求实现 Export 重构。
- 不要求实现 Dataset Builder。

## Decisions

### 1. `Session` 是默认页面

默认页面应是 `Session`，不是 `Tasks`。

理由：

- CCWhat 当前最稳定、最重要的能力是本地日志查看。
- Task segmentation 是增强能力，但它依赖已经加载的 session。
- 用户选择 session 后，第一预期是看到这个 session 的具体日志内容。

### 2. `Session` 承接旧版 Raw Events 能力

原 `Raw Events` 页面中的日志树和 detail panel 应成为 `Session` 页面主体。

页面结构：

```text
Session
  ├─ toolbar: count + type filters
  ├─ left pane: turn tree / entry list
  └─ right pane: entry detail
```

这不是新的 session 列表页，也不是占位页。

### 3. `Tasks` 承接任务切分

`Tasks` 页面只负责任务切分和 task 详情。

页面结构：

```text
Tasks
  ├─ empty state + run segmentation CTA
  └─ when ready:
       ├─ Task List
       └─ Task Detail tabs
```

Task Detail 可以继续保留 Overview / Evidence / Turns / Files & Diff / Commands / Raw tabs，但这些 tabs 都是 task 内部内容，不代表左侧需要完整 Diff 页面。

已加载 session 后，用户点击左侧 `Tasks` 的行为应是“查看/生成当前 session 的任务切分”，而不是只显示一个空 CTA。

规则：

```text
进入 Tasks
  ├─ 当前 session 未加载：显示禁用提示
  ├─ 当前 session 已有切分缓存：直接显示 Task List + Task Detail
  ├─ 当前 session 无切分缓存且未在切分：自动调用 /api/task-segments
  └─ 切分中：显示 loading 状态
```

这个自动切分只使用当前已选定 session，不再让用户在 Tasks 页面二次选择 session。

### 3.1 报告与任务切分不能互相阻塞

报告生成可能调用外部 analyzer，耗时远大于本地 task segmentation。viewer server 必须允许 `/api/analyze` 和 `/api/task-segments` 并行处理。

实现决策：

- viewer server 使用 threaded HTTP server。
- `/api/task-segments` 仍保持无持久化、按当前 session 即算即返。
- 不通过前端端口拆分解决，因为阻塞根因不是端口冲突，而是单线程 HTTP request handler 串行处理。

### 3.2 Task 卡片标题稳定

Task 卡片上的主标题表示“第几个任务”，不是 raw 用户消息摘要。

规则：

```text
task-001 -> 任务 1
task-002 -> 任务 2
task-003 -> 任务 3
```

原因：

- 不同 Agent 的本地日志字段差异较大，raw user text 可能包含结构化 payload、路径、编码片段或 adapter 内部字符串。
- 当前阶段用户最需要稳定识别任务边界，详细上下文可以在 Task Detail / Evidence 中查看。

### 4. Session 恢复报告分析入口

`Session` 页面应恢复旧版“分析当前 Session / 报告分析”能力。

设计约束：

- 报告分析按钮放在 `Session` 工具栏中。
- 按钮只在当前 session 加载成功后可用。
- 点击后复用已有分析模式弹窗和 `/api/analyze` 请求。
- 报告结果显示在 `Session` 详情区域中。
- 旧的 `evidence` page id 不再作为独立页面依赖；如果旧代码尝试跳转到 `evidence`，应归一到 `Session`，避免出现无 active page 的空白状态。

### 5. 其他页面降级

Overview、Timeline、Req / Resp、Diff、Diagnostics、Export、Settings 可以暂时保留占位入口，或从左侧导航隐藏。它们不得阻塞本阶段验收。

如果保留入口，必须显示明确占位文案，不能让用户误以为主功能已经完成。

### 6. 导航别名兼容

历史代码和 tests 中可能仍使用 `raw-events` 作为页面 id。第一阶段可以保留 alias：

```text
raw-events -> session
sessions -> session
evidence -> session
```

但用户可见文案应统一为 `Session`。

### 7. Session 加载后的刷新规则

`loadSession()` 成功后必须：

- 更新 `workbenchState.sessionId`
- 更新 `workbenchState.sessionData`
- rebuild canonical nav index
- render session list/detail
- render current active page
- 不得因为没有 task segmentation 结果而自动跳离当前页面

如果当前 active page 是 `Tasks`，则 `render current active page` 应触发当前 session 的任务切分展示/生成，而不是把任务页留空。

## Risks / Trade-offs

- [Risk] 收敛范围会让之前设计出来的多页面 workbench 看起来退回去了。  
  Mitigation: 这是阶段性收敛，先保证核心主流程可用，后续再逐个恢复其他页面。

- [Risk] 旧测试仍按多页面导航断言。  
  Mitigation: 更新测试，让它们围绕 `Session + Tasks` 两个核心模块。

- [Risk] 内部函数仍叫 `raw-events`。  
  Mitigation: 使用 alias 兼容，不要求一次性重命名所有内部变量。
