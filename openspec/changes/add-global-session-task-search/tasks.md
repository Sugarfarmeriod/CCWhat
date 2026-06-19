## 1. 后端搜索 API

- [x] 1.1 梳理 `viewer/server.py` 当前 project/session discovery、session load 和 adapter 数据结构，确定搜索复用点。
- [x] 1.2 新增 scoped search handler，校验 query、scope、project、session 和 limit 参数，默认 scope 为当前 session，返回结构化 JSON。
- [x] 1.3 实现当前 session、当前 project 跨 session、跨 project 三种 scope 的 session metadata 与 session content 搜索，结果包含 sessionId、projectDir、matchedFields、snippet 和可选 event/turn 定位。
- [x] 1.4 实现 task 搜索的数据来源选择，优先使用已有 task source，不为所有 sessions 静默执行自动任务切分。
- [x] 1.5 为无 query、无匹配、部分 session 读取失败和结果截断补齐响应语义。

## 2. Viewer 交互

- [x] 2.1 在 `viewer/claude-log.html` 增加搜索入口和 scope 控制，选项包含当前 session、跨 session、跨 project，默认选中当前 session。
- [x] 2.2 增加搜索结果视图，展示当前搜索范围、session/task/turn 类型、匹配摘要、来源 session 和时间信息。
- [x] 2.3 实现结果点击导航：session 结果加载对应 session，task 结果进入 Tasks 页面，turn/event 结果进入 Session 页面定位。
- [x] 2.4 处理跨 session 跳转时的 dirty Task Trace Overlay 保护和失败提示。
- [x] 2.5 保留现有当前 session 内搜索行为，并确保新搜索入口默认当前 session，不让用户无意触发跨 session/project 扫描。

## 3. 测试与验证

- [x] 3.1 增加后端 API 测试，覆盖默认当前 session scope、跨 session scope、跨 project scope、关键词命中、无结果、参数校验、limit 截断和部分 session 读取失败。
- [x] 3.2 增加 task 搜索测试，验证未切分 session 不产生伪 task，已有 task source 能返回 task 命中。
- [x] 3.3 增加前端 DOM/JS 测试，覆盖默认 scope、scope 切换、搜索结果渲染和结果点击导航。
- [x] 3.4 运行与本变更直接相关的测试：`uv run python -m unittest tests.test_task_segmentation_api`、新增后端测试，以及相关 Node DOM 测试。
