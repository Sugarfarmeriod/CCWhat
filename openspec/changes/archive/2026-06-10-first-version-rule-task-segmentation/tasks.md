## 1. 模块初始化与数据模型

- [x] 1.1 创建 `ccwhat/task_segments/` 包，暴露唯一公开入口 `segment_session(session)`
- [x] 1.2 定义 `NormalizedEvent`、`EvidenceBundle`、`BoundaryDecision`、`TaskSegment`、`TaskSegmentationResult` 的 dataclass 或类型字典
- [x] 1.3 新增包内资源 `ccwhat/assets/task_segment_rules.json`，包含初始的新任务、边界、延续、模糊问句和任务类型 marker
- [x] 1.4 在 `pyproject.toml` 的 package-data 中添加新规则 JSON 资源的配置

## 2. 事件归一化

- [x] 2.1 实现 main session 事件归一化，生成稳定 event id、turn index、source、timestamp、原始行号引用和文本提取
- [x] 2.2 实现 assistant tool call 与 user tool result 的抽取，尽力通过 tool use id 关联
- [x] 2.3 实现 subagent 事件归一化，保留 agent id 和 metadata 摘要
- [x] 2.4 为 main 事件、tool call/result 关联、subagent 事件归一化新增测试

## 3. 意图规则与 Todo 检测

- [x] 3.1 实现规则加载器和词法匹配器，支持中文短语 marker、英文词边界 marker 和正则 marker
- [x] 3.2 实现用户消息意图分类，输出新任务分数、延续分数、任务类型和原因列表
- [x] 3.3 实现延续否决逻辑，确保反馈消息不开新 Task（除非同时命中强边界 marker）
- [x] 3.4 实现 Todo 抽取与分类，区分用户目标 Todo、assistant 计划 Todo 和执行步骤 Todo
- [x] 3.5 为新任务消息、延续反馈、模糊问句、任务类型识别、Todo 分类新增测试

## 4. 证据抽取

- [x] 4.1 从归一化事件中抽取 `filesRead`、`filesChanged`、命令、测试/构建命令、错误、skill、subagent 和 final claim
- [x] 4.2 将文件路径归一化为仓库相对路径，无法相对化时保留原路径
- [x] 4.3 实现 final claim 检测，关闭当前 Task 但不开新 Task
- [x] 4.4 为文件证据、命令/测试证据、错误证据、skill/subagent 证据、final claim 抽取新增测试

## 5. 本地 BM25 与加权 Overlap

- [x] 5.1 实现本地 BM25 tokenizer，支持英文、路径、标识符和中文 2-gram
- [x] 5.2 实现内存 BM25 评分，用于 Todo/证据和意图/证据的关联计算
- [x] 5.3 实现文件证据权重，对 docs、README、lockfile、package config、通用配置文件降权
- [x] 5.4 实现 file-level 和 module-level 加权 Jaccard overlap
- [x] 5.5 为 tokenization、BM25 排序、文件权重、overlap 阈值新增测试

## 6. Segment 构建器

- [x] 6.1 实现边界候选检测，来源包括用户消息、用户 Todo、文件主题窗口和 final summary 关闭点
- [x] 6.2 实现候选边界的前瞻窗口，按事件数和 turn 数限制
- [x] 6.3 实现边界评分，包含正向信号、抑制信号、阈值检查和原因输出
- [x] 6.4 实现 Task Segment 状态机，涵盖开启、关闭、失败反馈后重开、高重叠相邻 segment 合并和模糊标记
- [x] 6.5 确保第一版 segment 默认 `status: "unevaluated"`，不输出成功或失败判断
- [x] 6.6 新增基于 fixture 的测试，覆盖：保守单任务 session、多用户任务、用户 Todo 拆分、文件主题变化、final claim 关闭、反馈重开和模糊交错场景

## 7. API 集成

- [x] 7.1 在 `viewer/server.py` 新增 `POST /api/task-segments`，含 session id 校验，仅支持当前 session 范围
- [x] 7.2 返回结构化 JSON，包含 `ok`、`sessionId`、`summary`、`tasks`、证据、文件权重、边界原因和模糊标记
- [x] 7.3 JSON 非法或 session id 无效时返回 400，session 不存在时返回 404
- [x] 7.4 为成功、非法请求、session 不存在和无持久化行为新增 API 测试

## 8. 验证与文档

- [x] 8.1 为第一版规则策略和调参旋钮编写面向开发者的说明文档
- [x] 8.2 运行任务切分单元测试和现有 session 分析测试
- [x] 8.3 对修改的包执行 Python 语法检查
- [x] 8.4 执行 `openspec validate first-version-rule-task-segmentation --strict`
- [x] 8.5 在至少一个真实 session fixture 上审查 API 输出，并记录已知局限性
