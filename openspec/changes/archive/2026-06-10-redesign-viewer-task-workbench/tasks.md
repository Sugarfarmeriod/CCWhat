## 1. OpenSpec 范围收敛

- [x] 1.1 将 proposal 从“多页面 Task-first Workbench”收敛为“Session + Tasks 双模块工作台”
- [x] 1.2 重写 design，明确 `Session` 是默认页面并承接旧版日志展示
- [x] 1.3 重写 spec，只保留 Session 展示、Tasks 切分、非核心页面降级和回归测试要求
- [x] 1.4 运行 `openspec validate redesign-viewer-task-workbench --strict`

## 2. Session 展示迁移

- [x] 2.1 左侧核心导航改为 `Session` 和 `Tasks`，`Session` 默认 active
- [x] 2.2 将旧版日志树、类型筛选、entry detail 主体迁移到 `Session` 页面
- [x] 2.3 `sessions` / `raw-events` 内部 page id 兼容路由到 `Session`
- [x] 2.4 `loadSession()` 成功后不得因为缺少 task segmentation 结果自动跳转到 Raw Events
- [x] 2.5 `loadSession()` 成功后必须刷新当前 active page，保证主工作区不空白
- [x] 2.6 Session 页面在无 entry 或未加载时显示明确空状态

## 3. Tasks 切分保留

- [x] 3.1 `Tasks` 页面保留任务切分 CTA，未加载 session 时显示明确禁用/提示状态
- [x] 3.2 `Tasks` 页面保留 Task List + Task Detail 双栏布局
- [x] 3.3 Task Detail 保留 Overview / Evidence / Turns / Files & Diff / Commands / Raw tabs
- [x] 3.4 Task start/end/evidence 跳转回 `Session` 页面并定位 entry
- [x] 3.5 非核心页面入口降级为占位或隐藏，不影响 Session / Tasks 主流程

## 4. 测试与验收

- [x] 4.1 更新前端静态测试，覆盖默认 `Session` 页面、`Tasks` 页面和 Session 容器存在
- [x] 4.2 更新测试，覆盖 `loadSession()` 不再自动跳离当前页面
- [x] 4.3 更新测试，覆盖 `raw-events` alias 跳转到 `Session`
- [x] 4.4 运行 `uv run python -m unittest`
- [x] 4.5 抽取 `viewer/claude-log.html` 内联脚本并执行 `node --check`
- [x] 4.6 运行 `node tests/test_task_segmentation_dom.js`

## 5. 手动验收

- [x] 5.1 启动 viewer，选择一个 Claude / Codex / OpenCode session，默认看到 `Session` 页面日志内容
- [x] 5.2 点击左侧 `Session`，主页面仍显示当前 session 的日志树和详情区
- [x] 5.3 点击左侧 `Tasks`，可运行任务切分并看到 Task List + Task Detail
- [x] 5.4 从 task start/end/evidence 点击定位，能回到 `Session` 并聚焦对应 entry
- [x] 5.5 在 Session 和 Tasks 之间切换，不丢失当前 session

## 6. 空白页与报告入口回归修复

- [x] 6.1 `Tasks` 页面在当前 session 已加载且无缓存时自动调用任务切分，不停留在空白或静态 CTA
- [x] 6.2 `Tasks` 页面切分中、成功、失败三种状态都有可见内容
- [x] 6.3 `Session -> Tasks -> Session` 往返切换后仍显示当前 session 日志列表和详情区
- [x] 6.4 导航到未知/旧 page id 时不得清空所有 active page；`raw-events` / `evidence` alias 归一到 `Session`
- [x] 6.5 `Session` 工具栏恢复“报告分析”按钮，并在 session 加载成功后启用
- [x] 6.6 报告分析结果复用已有 `/api/analyze` 链路并显示在 `Session` detail 区域
- [x] 6.7 补充静态与 DOM 回归测试覆盖 Tasks 自动切分、往返切换、报告按钮和 missing page 防空白
- [x] 6.8 运行 `openspec validate redesign-viewer-task-workbench --strict`
- [x] 6.9 运行 `uv run python -m unittest`
- [x] 6.10 抽取 `viewer/claude-log.html` 内联脚本并执行 `node --check`
- [x] 6.11 运行 `node tests/test_task_segmentation_dom.js`

## 7. 报告并发与任务卡片标题修复

- [x] 7.1 将 viewer server 从单线程 `HTTPServer` 切换为 threaded HTTP server，避免 `/api/analyze` 阻塞 `/api/task-segments`
- [x] 7.2 补充 server 构造测试，确认 `create_server()` 返回 threaded server
- [x] 7.3 将 task segmentation 输出标题统一为稳定序号 `任务 1`、`任务 2`
- [x] 7.4 补充 segmenter 测试，确认多任务标题不会使用 raw 噪声文本
- [x] 7.5 运行 `openspec validate redesign-viewer-task-workbench --strict`
- [x] 7.6 运行 `uv run python -m unittest`
- [x] 7.7 运行 `node tests/test_task_segmentation_dom.js`
- [x] 7.8 抽取 `viewer/claude-log.html` 内联脚本并执行 `node --check`
- [x] 7.9 commit 并 push 到远端 GitHub 仓库
