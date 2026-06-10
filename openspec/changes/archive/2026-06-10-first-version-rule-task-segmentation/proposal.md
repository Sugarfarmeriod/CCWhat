## 背景与动机

当前分析入口只能对整个 session 生成一段 Markdown 报告，无法把长对话拆成可复盘、可测试、可调参的任务单元。为了支撑后续 Agent Eval、任务级证据链和失败诊断，第一版需要先建立一个纯规则的 Task Segment 切分能力。

## 变更内容

- 新增纯规则 Task Segment 切分能力，将 Claude/Codex 风格长 session 归一化为事件流，并按用户目标、Todo 候选、文件主题变化和 final summary 生成任务片段。
- 新增规则化意图分类器，用配置化关键词/短语识别新任务倾向、延续反馈、模糊消息和任务类型，不使用 LLM 判断边界。
- 新增证据抽取，抽取文件读取/修改、命令、测试、错误、Todo、skill、subagent、final claim 等证据。
- 新增加权文件 overlap 计算，使用 file-level 和 module-level 加权 Jaccard 判断主题是否发生明显变化。
- 新增本地轻量 BM25，用于将用户 Todo / 用户目标与后续证据关联，不引入 Elasticsearch 等外部依赖。
- 新增 `/api/task-segments` 接口，接收当前 session ID，返回结构化任务片段、边界原因和调试分数。
- 第一版只做保守切分，默认 `status: unevaluated`，不做成功率评测或 LLM Judge。

## 能力变更

### 新增能力

- `task-segmentation`：定义 session 到 Task Segment 的纯规则切分、证据抽取、边界评分、调试输出和 API 行为。

### 修改能力

无。

## 影响范围

- 影响代码：新增 `ccwhat/task_segments/` 模块；扩展 `viewer/server.py` 增加 `/api/task-segments`；后续可在 viewer 页面接入任务视图。
- 影响测试：新增规则分类、BM25、加权 overlap、segment build、API 行为的单元测试。
- 依赖影响：不新增外部服务或搜索引擎依赖；BM25 和规则匹配在 Python 内存中完成。
- 行为边界：第一版偏保守，目标是 precision > recall；宁可少切或标记 ambiguous，也不要把一个连续任务切碎。
