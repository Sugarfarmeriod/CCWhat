## Context

当前仓库状态是本地 `main` 与 `origin/main` 分叉。本地前端更接近产品期望的 App Shell 观感：左侧一级导航、顶部上下文栏、功能入口齐全；云端版本则包含更多稳定性修复和测试，例如 threaded viewer server、OpenCode adapter 跨线程访问修复、viewer agent status probe、canonical navigation 和 session load 诊断。

用户当前目标不是保留本地 Task-first 默认入口，而是保留本地前端外壳观感，同时采用云端稳定逻辑。默认首屏必须保持 `Session`，`Tasks` 作为用户手动进入的功能页。

## Goals / Non-Goals

**Goals:**

- 以 `origin/main` 为稳定合并底座，保留云端已有 bug fix 和新增测试。
- 修复云端 viewer 的 `init()` 自递归问题，确保页面打开后自动初始化且不会栈溢出。
- 将本地 App Shell 的视觉和导航结构迁移到云端 viewer：左侧导航、顶部上下文、按钮排布、开发者工具风格。
- 保持默认进入 `Session` 页面，用户手动点击 `Tasks` 后再运行或查看任务切分。
- 未完成的功能页保留导航入口，但显示清晰的“开发中/占位”状态。
- 使用测试固定合并后的关键行为，避免后续再次把默认入口、初始化、agent badge 或导航结构改坏。

**Non-Goals:**

- 不修改 `ccwhat.task_segments` 的规则切分算法。
- 不实现 Dataset Builder、Offline Eval Runner 或未来路线中的完整能力。
- 不引入 React/Vue/Svelte 等前端框架。
- 不直接复制 `/Users/elon-ge/Downloads/index.html` 或本地 `viewer/claude-log.html` 整文件。
- 不把默认首屏改回 `Tasks`。

## Decisions

### 1. 云端为逻辑底座，本地为视觉参考

合并时 SHALL 以 `origin/main` 的功能逻辑和稳定性修复为基准，然后把本地 App Shell 视觉结构按模块迁移。原因是云端已包含更多 bug fix 和回归测试；本地 HTML 作为整文件覆盖会重新引入已修复问题。

备选方案是以本地 `viewer/claude-log.html` 为基准再 cherry-pick 云端修复。该方案风险更高，因为云端对 viewer/server/adapter/test 的修复散布在多个提交里，容易遗漏。

### 2. `init()` 只保留一个真实入口

合并后的 `viewer/claude-log.html` SHALL 只有一个页面初始化入口。禁止使用会被函数声明提升影响的写法，例如：

```js
const _origInit = init;
async function init() {
  await _origInit.call(this);
}
```

如果需要扩展初始化流程，应将基础逻辑提取为不同命名的 helper，例如 `loadProjects()`、`initializeWorkbench()`，再由唯一的 `init()` 顺序调用。

### 3. 默认页固定为 Session

合并后的 workbench state SHALL 默认 `activeView` / `activePage` 为 `sessions`。`loadSession()` 完成后 SHALL 刷新当前页面内容，但不得自动跳转到 `tasks`。用户点击左侧 `Tasks` 或任务切分按钮时，才进入任务切分工作流。

### 4. 左侧导航是一级功能入口，不再承载 turn tree

左侧导航 SHALL 展示产品级功能入口：`Session`、`Tasks`、`Overview`、`Timeline`、`Req / Resp`、`Diff`、`Diagnostics`、`Export`、`Settings`。原始 turn/event 树 SHALL 留在 `Session` 页面内部，而不是作为全局左栏。

未完成页面 SHALL 显示占位状态，说明该功能正在开发或需要先选择 session；不能出现空白页面。

### 5. 导航定位继续使用 canonical target

任务起止事件、错误、命令、文件证据等跳转 SHALL 使用云端已有的 canonical navigation 思路。即使页面视觉迁移，`startEventId` / `endEventId` 仍必须能定位回 `Session` 页面内部的事件列表。

### 6. Agent badge 必须来自真实数据

Agent badge SHALL 使用 `/api/projects` 或 `/api/viewer/status` 返回的真实 agent 名称；初始 DOM 可以是中性占位，但加载后不得硬编码为 `claude`。viewer 端口复用时 SHALL 保持云端的 agent mismatch fail-fast 行为。

## Risks / Trade-offs

- [Risk] `viewer/claude-log.html` 是大体量单文件，视觉迁移容易误删现有逻辑。  
  Mitigation: 按 CSS/HTML shell/导航状态/页面渲染函数分块迁移，每块后跑测试。

- [Risk] 左侧入口齐全但部分页面未完成，用户可能误以为功能已实现。  
  Mitigation: 未完成页面显示明确占位，不使用假数据冒充真实功能。

- [Risk] 修复 `init()` 后可能影响自动加载项目列表。  
  Mitigation: DOM 测试覆盖页面打开后调用初始化、项目列表加载、session 页面不空白。

- [Risk] 本地视觉和云端 canonical navigation 结构不完全一致。  
  Mitigation: 迁移视觉时保留云端 `rebuildCanonicalNavIndex()`、`navigateToEventId()`、`focusEntryInNav()` 的行为合同，并补充事件定位测试。

- [Risk] OpenSpec 中旧 change 仍存在，执行 agent 可能混用旧目标。  
  Mitigation: 本 change 的 tasks 明确不要实施 `Task-first 默认入口`，并标注旧 change 已被当前合并策略取代。

## Migration Plan

1. 创建临时合并分支或工作树，以 `origin/main` 为基线。
2. 修复 `viewer/claude-log.html` 的 `init()` 自递归问题，并先跑前端 DOM 测试。
3. 保留云端后端和 adapter 稳定性修复。
4. 分块迁移本地 App Shell 视觉：左侧导航、顶部上下文栏、按钮排布、占位页面样式。
5. 确认默认页为 `Session`，`Tasks` 为手动入口。
6. 更新静态测试、DOM 测试和 Python 测试。
7. 若合并后前端出现空白页或初始化失败，回退到云端稳定 HTML，再逐块重放视觉迁移。

## Open Questions

- 本次是否需要把 `Overview`、`Timeline` 等页面做成真实数据页面，还是只保留占位？当前决策：只要求入口和占位，真实数据可后续 change 完成。
- 是否要把 `Session` 文案改为 `Raw Events`？当前决策：左侧主入口使用 `Session`，页面内部可以标注 Raw Events / Turns。
