## 现状背景

当前项目已经能读取 Claude session main 日志和 subagent 日志，并通过 `/api/analyze` 临时调用分析命令生成整段 session 的 Markdown 分析报告。这个报告适合人工阅读，但不能稳定支撑任务级 Eval，因为一个长 session 往往包含多个用户目标、多个交付物、重试、反馈、subagent 调度和 final summary。

第一版 Task 切分需要先建立一条可解释、可测试、可调参的规则 pipeline。边界判断不依赖 LLM，不引入 Elasticsearch 或外部服务。LLM 后续可以用于标题润色、需求点抽取或诊断总结，但不能作为第一版 Task 边界来源。

## 目标与非目标

**目标：**

- 将 session 日志归一化为统一事件流，覆盖用户消息、assistant 文本、tool call、tool result、文件证据、命令、错误、Todo、skill、subagent 和 final claim。
- 使用配置化关键词/短语规则识别用户消息的新任务倾向、延续反馈、模糊消息和任务类型。
- 使用本地轻量 BM25 将用户 Todo / 用户目标与后续证据关联。
- 使用 file-level 和 module-level 加权 Jaccard overlap 判断文件主题是否明显变化。
- 使用边界评分和原因列表决定是否开新 Task，并输出可调试的切分依据。
- 第一版采用保守策略：precision > recall；宁可少切或标记 ambiguous，也不要把一个连续任务切碎。
- 提供 `/api/task-segments` 返回结构化 task segments，供后续 UI 和评测能力使用。

**非目标：**

- 不使用 LLM 判断 Task 边界。
- 不做任务成功率、需求覆盖率或失败归因评测；第一版统一输出 `status: "unevaluated"`。
- 不引入 Elasticsearch、数据库索引或持久化 task segment 存储。
- 不要求第一版完美处理复杂交错任务；对于频繁跨主题跳转的 session 可以标记 `ambiguous`。
- 不改变现有 `/api/analyze` Markdown 报告能力。

## 设计决策

### 决策 1：新增独立 `ccwhat/task_segments/` 模块

模块结构：

```text
ccwhat/task_segments/
  __init__.py
  models.py
  events.py
  rules.py
  evidence.py
  bm25.py
  overlap.py
  segmenter.py
```

`segmenter.segment_session(session: dict) -> TaskSegmentationResult` 作为唯一入口。这样可以在 API、测试和后续 CLI 中复用同一套逻辑，并避免把规则堆进 `viewer/server.py`。

### 决策 2：事件归一化先于切分

原始 Claude 日志结构复杂，main/subagent、tool use/tool result、assistant text、user feedback、skill 回调混在一起。第一步将其归一化为 `NormalizedEvent`：

```json
{
  "eventId": "main:42",
  "source": "main",
  "turnIndex": 8,
  "eventType": "user_message|assistant_text|tool_call|tool_result|file_read|file_edit|command|error|todo|final_claim",
  "text": "...",
  "toolName": "Bash",
  "files": ["viewer/server.py"],
  "command": "python -m unittest",
  "timestamp": "...",
  "rawRef": {"fileLine": 42}
}
```

切分算法只消费归一化事件，便于未来适配 Codex/OpenCode 的日志 adapter。

### 决策 3：用户意图用规则词典打分，不用语义模型

规则词典放在包内资源，例如 `ccwhat/assets/task_segment_rules.json`。第一版支持：

- `new_task_markers`
- `boundary_markers`
- `continuation_markers`
- `task_types`
- `weak_question_markers`

中文使用 phrase contains / regex，英文使用 lowercase + word boundary。代码块和长 JSON 片段默认降权，路径信息保留给证据匹配。

否决规则优先：

```text
如果命中 continuation marker（继续/刚才/还是报错/没通过/根据 review）
并且没有强边界 marker（另外/还有/新任务）
=> 不开新 Task
```

### 决策 4：BM25 只用于证据关联，不用于新任务判断

新任务判断由规则词典完成。BM25 用于：

- 用户消息中多个目标型 Todo 与后续证据的匹配
- 用户目标文本与文件/命令/错误证据的相关性辅助

第一版实现本地内存 BM25，不引入 ES。Tokenizer 规则：

- 英文/路径：按 `[A-Za-z0-9_]+` 切分，并对 `/ . _ -` 拆词。
- 文件路径：保留完整文件名、stem、目录片段。
- 中文：保留连续中文片段，并生成 2-gram。

最终相关性分数为 `bm25_score * evidence_weight`。

### 决策 5：文件主题变化用加权 overlap，并要求附近边界

每个 Task 和候选窗口维护 `dict[path, weight]`。事件贡献：

```text
Edit / Write / Patch / MultiEdit     +3
测试/构建命令相关文件                  +2
Read / Grep / Open                   +1
README/docs/lockfile                 *0.3
pyproject/package/config             *0.5
test files                           *0.8，除非 task_type 是 test
```

加权 Jaccard：

```python
intersection = sum(min(a[k], b[k]) for k in keys)
union = sum(max(a[k], b[k]) for k in keys)
overlap = intersection / union if union else 0
```

同时计算：

- `file_overlap`：完整相对路径级别
- `module_overlap`：目录前 1-2 层级别

文件主题变化只能作为切分支持信号，不能单独切分。建议初始条件：

```text
file_overlap < 0.25
AND module_overlap < 0.5
AND next_window_edit_or_test_weight >= 3
AND 附近存在 user/todo/final summary 边界
```

### 决策 6：边界评分输出原因列表

每个候选边界生成分数和原因：

```json
{
  "eventId": "main:32",
  "score": 4.5,
  "reasons": [
    "user_new_task:修复:+2",
    "boundary_marker:另外:+2",
    "file_overlap_low:0.12:+2",
    "continuation_absent:+0.5"
  ]
}
```

初始阈值：

```text
score >= 3 => split
score < 3  => attach_to_current
```

正向信号包括用户新需求、强边界词、目标型 Todo 有后续证据、低 overlap、有 edit/test 证据、前一任务已有 final claim。抑制信号包括延续反馈、高 overlap、只有 Read/Grep、只有 Skill 变化、同一错误继续出现。

### 决策 7：Final summary 关闭 Task，反馈消息可重开 Task

Final summary 不创建新 Task，只记录：

```text
finalClaim = Agent 声称完成的内容
```

如果后续用户消息命中"还是报错/没通过/不对/继续改"等反馈，并且与最近关闭 Task 的文件、错误或 final claim 有重叠，则 reopen 最近 Task，而不是开新 Task。

### 决策 8：Todo 分层处理

Todo 分为：

- `user_todo`：用户消息里的目标列表，可以生成 CandidateTask。
- `assistant_plan_todo`：assistant 自己的计划，默认作为当前 Task steps。
- `tool_todo`：TodoWrite / task manager 工具里的执行计划，默认作为当前 Task steps。

只有 `user_todo` 可以直接产生 CandidateTask。assistant/tool todo 只有在后续证据与某条 Todo 强匹配、且文件主题也发生明显变化时，才支持拆分。

### 决策 9：Subagent 和 Skill 是辅助信号

Subagent 归属于派发它的 main task，不单独开 Task。Skill 调用表示工作模式变化，最多提供弱分，不允许单独触发切分。

### 决策 10：API 返回结构化结果，不持久化

新增：

```http
POST /api/task-segments
{"sessionId": "<uuid>"}
```

返回 `ok: true`、`sessionId`、`tasks`、`summary`。第一版不落盘、不写入 session、不改变导出包。

## 风险与权衡

- 关键词规则漏掉隐含新需求 → 第一版采用保守切分，并通过 boundary reasons 方便补规则。
- 文件 overlap 误判跨前后端同一任务 → 同时计算 module overlap，并要求 user/todo/final summary 附近边界。
- Todo 被过度拆分 → 只有用户目标型 Todo 生成 CandidateTask，执行步骤 Todo 留在当前 Task。
- 复杂交错任务难以准确切分 → 标记 `ambiguous`，不强行细切。
- 规则参数需要迭代 → 所有边界输出 score/reasons，测试 fixture 覆盖典型误切/漏切场景。

## 实施路径

1. 新增 task segmentation 内部模块和包内规则配置。
2. 为现有 Claude session 数据实现事件归一化和证据抽取。
3. 实现规则词典、BM25、加权 overlap 和 segmenter。
4. 新增 `/api/task-segments`，只读取当前 session，不持久化。
5. 增加单元测试和 API 测试。
6. 后续另起 change 将结构化任务结果接入 viewer 任务视图。

## 待讨论问题

- 第一版是否需要将 `task-segments` API 暴露到 CLI，还是只服务 viewer。
- 前端 debug 模式是否默认展示 boundary reasons，还是先仅在 JSON/API 中保留。
