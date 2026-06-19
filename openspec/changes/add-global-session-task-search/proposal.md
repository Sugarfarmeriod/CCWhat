## Why

当前 Viewer 只支持在已加载的单个 session 内搜索 turns/events/tasks。用户想找“当前 session 里某个细节”“当前 project 下之前哪个 session 做过某个功能”“其他 project 里是否有相关 task”时，需要逐个 session 打开和切换，效率低，也容易漏掉已切分或已保存的 task。

## What Changes

- 新增带范围选择的 Session/Task 搜索能力，范围包括当前 session、当前 project 内跨 session、跨 project 搜索。
- 搜索范围默认是当前 session，用户显式选择后才扩大到跨 session 或跨 project。
- 新增后端搜索 API，基于现有 adapter/session 读取能力按选定范围扫描本地 session，不引入外部索引服务。
- 前端新增搜索入口和结果视图，结果可定位回对应 session、task 或 turn。
- 搜索结果包含清晰来源、匹配类型和简短摘要，避免用户必须打开完整 raw log 才能判断是否相关。

## Capabilities

### New Capabilities

- `session-viewer`: 提供可选范围的 Session/Task 搜索入口、后端 API 和结果导航。

### Modified Capabilities

- `session-viewer`: 保留当前 session 内搜索行为，将当前 session 作为新搜索入口的默认范围，并允许用户显式扩大搜索范围。

## Impact

- `viewer/server.py`: 增加全局搜索 API，复用 session discovery 和 adapter 加载逻辑。
- `viewer/claude-log.html`: 增加全局搜索入口、结果页面或 modal、结果点击后的 session/task/turn 定位。
- `tests/`: 增加后端 API、前端 DOM 或最小 JS 测试，覆盖 session/task 搜索关键路径。
