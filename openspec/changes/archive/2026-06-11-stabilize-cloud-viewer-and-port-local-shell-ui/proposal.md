## Why

本地 `main` 和 `origin/main` 已经分叉：云端版本包含更多 viewer 稳定性修复和测试，但前端入口存在 `init()` 自递归风险；本地版本的 App Shell 视觉和导航排布更符合产品方向，但不应整文件覆盖云端稳定逻辑。现在需要一个明确的合并 change，把云端作为稳定底座，同时迁移本地前端外壳观感。

## What Changes

- 以 `origin/main` 的 viewer/server/adapter 稳定性修复作为合并底座，保留 threaded server、OpenCode SQLite 跨线程访问修复、viewer agent status probe、任务导航并发修复和现有测试覆盖。
- 修复云端 `viewer/claude-log.html` 中 `init()` 包装导致的自递归问题，确保页面打开后能自动初始化且不会栈溢出。
- 保留云端行为：默认进入 `Session` / 原始事件视图，用户手动进入 `Tasks` 后再触发或查看任务切分。
- 从本地 viewer 迁移 App Shell 视觉结构：左侧一级导航、功能分组、顶部上下文栏、按钮位置、开发者工具风格、未完成页面占位。
- 明确左侧导航入口齐全，但未实现页面 SHALL 显示开发中/占位状态，而不是隐藏入口或挤到顶栏。
- 保持现有 `/api/task-segments`、session load、Req/Resp、Diff、Export 等真实数据逻辑；不直接复制设计版 HTML，也不以本地 `viewer/claude-log.html` 整文件覆盖云端。
- 更新前端静态测试和 DOM 测试，覆盖默认 Session 首屏、手动 Tasks 入口、`init()` 非递归、agent badge、左侧导航结构和稳定定位。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `session-viewer`: 调整 viewer 合并后的前端外壳、默认入口、初始化稳定性、左侧导航和任务切分入口行为。

## Impact

- 影响代码：`viewer/claude-log.html`、`viewer/server.py`、`ccwhat/commands/run.py`、`ccwhat/adapters/opencode.py`，以及相关测试。
- 影响测试：需要保留云端新增的稳定性测试，并补充/调整前端测试，证明 `init()` 不递归、默认页为 Session、Tasks 为手动入口、导航视觉入口齐全。
- 影响 OpenSpec：本 change 收敛当前本地/云端合并策略；不继续沿用“直接 Task-first 默认入口”的旧设计。
- 非目标：不修改 task segmentation 规则算法；不引入 Dataset Builder / Offline Eval Runner；不重写成前端框架；不逐像素复刻 `/Users/elon-ge/Downloads/index.html`。
