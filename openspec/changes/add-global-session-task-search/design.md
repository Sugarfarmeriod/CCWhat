## Context

现有 Viewer 已经具备项目/session 列表、单 session 加载、当前 session 内搜索、任务切分、Task Trace Overlay 和 Dataset 保存能力。但这些能力大多围绕当前已加载 session 工作。新的搜索应先服务当前 session 的高频查找，并允许用户在需要时显式扩大到当前 project 的多个 sessions 或所有 projects，再跳转到已有 session/task 视图继续分析。

## Goals / Non-Goals

**Goals:**

- 支持按关键词搜索当前 session、当前 project 内多个 sessions、所有 projects 的基础信息和 session 内容摘要。
- 搜索范围默认是当前 session，避免无意触发大范围扫描。
- 支持搜索已有 task 信息，包括当前可由 task segmentation 结果或保存的 Task Trace Overlay 表达的 task 标题、ID、类型和 evidence。
- 搜索结果能跳转回对应 session，并在可行时定位到 task 或 turn。
- 第一版保持实现简单，适合本地小规模 session 集合。

**Non-Goals:**

- 不引入外部索引服务、数据库、后台常驻索引进程或向量搜索。
- 不改变录制、代理、req/resp 捕获链路。
- 不改变 `POST /api/task-segments` 的单 session 契约，不让任务切分 API 接收跨 session 参数。
- 不在第一版自动评估 task 成功率或生成新的 Dataset。

## Decisions

### Decision 1: 新增独立的 scoped search API

新增独立 API，例如 `GET /api/search?q=<query>&scope=<scope>&project=<projectDir>&session=<sessionId>&limit=<n>`。`scope` 支持：

- `current_session`：仅搜索当前已选 session，也是默认值。
- `current_project`：搜索当前 project 下的全部 sessions。
- `all_projects`：搜索所有本地可发现 projects 下的 sessions。

API 应复用现有 project/session discovery 与 adapter 加载逻辑，返回结构化结果，而不是让前端一次性加载所有 sessions 后本地搜索。

这样可以把文件扫描、session 加载、结果裁剪和错误处理留在后端，前端只负责展示和导航。

### Decision 2: 第一版使用按需扫描，不做持久索引

第一版按请求和选定 scope 扫描本地 session metadata 和必要的 session 内容，并用 limit 控制结果数量。默认 `current_session` 不会扫描其他 sessions；只有用户选择 `current_project` 或 `all_projects` 时才扩大扫描范围。对本地开发者的常见 session 数量，这比维护索引更简单，也更符合当前项目“不做推测性复杂实现”的原则。

如果后续 session 数量变大，可以在单独 change 中增加缓存或索引。

### Decision 3: Task 搜索以已有 task source 为准

Task 搜索不应静默为所有 sessions 执行昂贵的自动切分。第一版优先搜索：

- 当前页面内存中已有的 task segmentation result 或 active/saved overlay；
- 后端可发现的已保存 Dataset/registry task metadata；
- 已加载 session 中可直接派生的 task source。

若某个 session 尚未产生 task source，搜索结果可以仍返回 session/turn 命中，但不伪造 task。

### Decision 4: 结果导航复用现有 Session/Tasks 页面

结果点击后应加载对应 session。若结果包含 `taskId`，前端应进入 Tasks 页面并选中该 task；若结果包含 `eventId` 或 turn 定位信息，前端应进入 Session 页面并定位对应 turn/event。若目标 task source 不在当前页面内存中，前端应显示可读提示并允许用户先执行任务切分或加载已保存 overlay。

## Risks

- **性能风险**：大量 session 全文扫描可能变慢。缓解方式是默认只搜当前 session，跨 session/project 需要用户显式选择，并设置 limit、最小 query 长度、按最近 session 优先，在响应中返回是否截断。
- **task source 不完整**：未切分 session 没有 task 结果。缓解方式是明确区分 session/turn 命中和 task 命中，不自动伪造 task。
- **导航状态复杂**：搜索结果跨 session 跳转可能与未保存 overlay 冲突。缓解方式是复用现有 dirty overlay 切换保护逻辑。
