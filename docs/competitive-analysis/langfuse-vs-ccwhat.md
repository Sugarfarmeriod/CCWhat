# Langfuse vs CCWhat：数据模型与诊断能力对比

> 本文档用于对外讲述 CCWhat 与 Langfuse 的核心差异，包含字段级别的精确对比，可直接用于面试、投资人沟通或技术交流。

---

## 一、Langfuse 是什么

Langfuse 是目前 GitHub star 最高的开源 LLM Observability 工具，核心定位是**通用 LLM 应用的可观测性平台**。它的能力围绕"LLM API 调用的追踪与评估"展开：追踪每次调用的 prompt/completion、统计 token 消耗和成本、通过 LLM-as-judge 或人工对 trace 打分。

Langfuse 支持自托管，基于 OpenTelemetry 标准构建，适合需要监控 chatbot、RAG、通用 AI 应用的团队。

---

## 二、Langfuse 数据模型（从源码提取）

以下字段来自 Langfuse `packages/shared/src/server/ingestion/types.ts` 的 Zod schema 定义。

### Trace（顶层容器）

```
id, timestamp, name, externalId
input: any          ← 非结构化 JSON blob
output: any         ← 非结构化 JSON blob
sessionId, userId, environment
metadata, release, version, public, tags
```

### Span（时间段观测）

```
id, traceId, name, environment
startTime, endTime
input: any, output: any
level: DEBUG | DEFAULT | WARNING | ERROR
statusMessage, metadata, version
parentObservationId    ← 唯一的嵌套关系字段
```

### Generation（LLM 调用，Span 的子类）

```
# Span 所有字段 +
model: string
modelParameters: {key: value}     ← temperature 等超参
completionStartTime               ← 首 token 时间（TTFT）
usage: {
  input, output, total: int       ← token 计数
  unit: TOKENS | CHARACTERS | ...
  inputCost, outputCost, totalCost: float
}
usageDetails, costDetails
promptName, promptVersion
```

### Score（评估结果）

```
id, name, traceId, observationId
dataType: NUMERIC | CATEGORICAL | BOOLEAN | TEXT
value: number | string
comment, metadata
source: API | EVAL | ANNOTATION
```

**Langfuse 模型本质**：时间段 + 输入输出文本 + token 计数 + 一个标量分数。

---

## 三、CCWhat 数据模型（V2 Runtime Dataset）

### task.json（任务层）

```
schema: "ccwhat-runtime-task-v1"
task_id, run_id, title
status: recording → finalized | aborted
started_at, finished_at, workspace

instruction          ← 用户实际说了什么（从 session 日志提取）
success_criteria     ← 成功标准
expected_tests[]     ← 预期测试命令

git: {
  before_commit, before_status   ← /ccwhat:start 时的 git 状态
  after_commit,  after_status    ← /ccwhat:finish 时的 git 状态
}

evidence_availability: {         ← 每类证据是否成功采集
  repo_before: bool
  repo_after:  bool
  diff:        bool
  control_events: bool
  task_trace:  bool
}
```

### task_trace.json（行为层）

```
events[]: NormalizedEvent {
  event_type: user_message | assistant_text | tool_call | tool_result
            | file_read | file_edit | command | error | final_claim
  tool_name, files[], command
  timestamp, turn_index, source
}

commands[]           ← Agent 实际执行的每一条命令
test_commands[]      ← 其中被识别为测试命令的子集

files: {
  read[]             ← 读过的文件
  changed[]          ← 改过的文件（Agent 自报）
}

changes[]: {
  change_id, event_id            ← 可追溯到具体 tool_call
  file, kind: edit | write | create
  old_string, new_string         ← 改动内容
  confidence: high | medium
}

patches[]: {patch_id, file, format, patch}

errors[]             ← 具体错误信息（含 stack trace）
final_claim          ← Agent 最后声称完成了什么
first_user_message
repo_state: {cwd, base_commit, head_commit}
```

### 其他证据文件

| 文件 | 内容 |
|------|------|
| `repo_before.tar.gz` | `/ccwhat:start` 时的完整工作区快照 |
| `repo_after.tar.gz` | `/ccwhat:finish` 时的完整工作区快照 |
| `diff.patch` | 真实 `git diff HEAD`（不是 Agent 说的，是 git 量出来的） |
| `control_events.jsonl` | 任务边界事件流，含精确时间戳，confidence=high |

---

## 四、Coding Agent 特有概念：字段级对比

| 概念 | 在 CCWhat 中的体现 | 在 Langfuse 中的对应 | 为什么对 Coding Agent 重要 |
|------|-------------------|---------------------|---------------------------|
| **任务指令** | `instruction` | 无（只有 `input` blob） | Coding 任务需要明确的目标描述，不是闲聊 |
| **成功标准** | `success_criteria` | 无 | 定义"完成"的验收条件，是归因的必要参照 |
| **预期测试** | `expected_tests[]` | 无 | Coding Agent 的核心验证方式 |
| **代码改动** | `diff.patch`（git 真实 diff） | 无（Agent 说的算） | 客观 ground truth，可验证 Agent 声明 |
| **文件快照** | `repo_before/after.tar.gz` | 无 | 可重放、可 diff、可验证 |
| **命令执行** | `commands[]` + exit_code | 无 | Agent 行为的关键证据 |
| **Agent 声明** | `final_claim` | `output` 文本 | 需要与 diff 交叉验证 |
| **证据可用性** | `evidence_availability` | 无 | 明确知道哪些证据缺失，诊断不瞎猜 |
| **测试失败** | `errors[]` 含 stack trace | 无 | 归因需要具体错误信息 |
| **编程动作** | `event_type: file_edit/command/error` | `type: SPAN/GENERATION` | 语义层级不同 |

---

## 五、六个核心差距

### 差距 1：观测单元的语义层级

**Langfuse** 的原子观测单元是 **LLM API 调用**（Generation）。回答的问题：这次调用用了多少 token、花了多少钱、latency 多少。

**CCWhat** 的原子观测单元是 **编程动作**（NormalizedEvent）。`event_type` 是 `file_edit`、`command`、`error`，不是"一次 API 调用"。回答的问题：Agent 读了哪个文件、改了什么内容、跑了什么命令、命令有没有报错。

**Coding Agent 长程任务的特有挑战**：

普通 LLM chat 是"一问一答"，但 Coding Agent 的任务是：
- 跨多轮对话（20-50轮）
- 涉及多文件读写（5-20个文件）
- 执行多条命令（git/test/lint/install）
- 最终产出是代码变更，不是文本回答

Langfuse 的 Generation 模型适合看单次调用，但无法回答：
- "这5次文件修改中，哪一次引入了测试失败？"
- "Agent 读了 utils.py 但改了 helpers.py，这个决策合理吗？"
- "第3轮说'添加测试'，第15轮才实际执行，中间发生了什么？"

CCWhat 的 NormalizedEvent 按**编程语义**（file_read/command/error）而非**API 调用**组织，天然适配长程任务的归因需求。

> **一句话**：Langfuse 的 Generation 告诉你 Agent **说了**什么，CCWhat 的 NormalizedEvent 告诉你 Agent **做了**什么。

---

### 差距 2：有无客观 ground truth

**Langfuse** 没有客观验证层——只有 Agent 的 output 文本。Agent 声称"我修复了 bug"，Langfuse 就记录这段文字，无法验证。

**CCWhat** 在 `/ccwhat:finish` 时执行 `git diff HEAD`，获取真实的 `diff.patch`。把 `diff.patch`（代码实际改了什么）和 `final_claim`（Agent 声称做了什么）放在同一个 task 目录里，归因诊断可以直接做交叉验证：Agent 说改了 auth 逻辑，但 diff 只改了 README？这个矛盾直接可检测。

> **一句话**：Langfuse 只有 Agent 的证词，CCWhat 还有法证级别的 git 物证。

---

### 差距 3：任务边界的可靠性

**Langfuse** 的 Span 边界由开发者在代码里手动传 `traceId` 来设定，是软件工程层面的观测点，不是用户意图层面的任务边界。多轮对话里"这一步属于哪个任务"本质上是模糊的。

**CCWhat** 用用户主动触发的 `/ccwhat:start` 和 `/ccwhat:finish` 作为边界，记录在 `control_events.jsonl` 里，`confidence: "high"`，时间戳精确到毫秒。所有证据文件都严格归属于这个边界，`evidence_availability` 显式标记每类证据是否成功采集。

> **一句话**：Langfuse 的任务边界是代码打的标记，CCWhat 的任务边界是用户的意图声明。

---

### 差距 4：诊断输出结构

**Langfuse 的 Score**（LLM-as-a-judge 或人工标注）：
```json
{
  "name": "quality",
  "value": 0.7,
  "dataType": "NUMERIC",
  "comment": "response was mostly relevant"
}
```
一个标量。告诉你"这次交互质量 0.7 分"，但：
- 为什么是 0.7 不是 0.6？无法验证
- "mostly relevant" 指什么？无法追溯到具体证据
- 怎么改才能到 0.9？不知道

**CCWhat 的 diagnosis.json**（Plan 3 目标）：
```json
{
  "task_id": "task-001",
  "summary": "Agent 声称完成但测试未通过，diff 与描述不符",
  "likely_root_causes": [
    {
      "cause": "测试未通过",
      "evidence": [
        "test_commands[0]: pytest tests/unit/",
        "errors[0]: AssertionError: expected True, got False"
      ],
      "confidence": "high",
      "source": "rule"
    },
    {
      "cause": "final_claim 与 diff 矛盾：声称修改了 auth 逻辑，实际只改了 README",
      "evidence": [
        "final_claim: '已修复登录验证逻辑'",
        "diff.patch: 仅含 README.md 的变更"
      ],
      "confidence": "high",
      "source": "rule"
    }
  ],
  "missing_evidence": ["success_criteria 未填写，无法判断验收标准"],
  "confidence": "high",
  "recommended_next_steps": ["查看 errors[0] 的完整 stack trace", "重新运行 pytest tests/unit/"]
}
```

告诉你**为什么失败、具体哪条命令、具体什么错误、证据链是什么、confidence 来自规则层还是 LLM 层**。

> **一句话**：Langfuse 的 Score 是考卷分数，CCWhat 的 diagnosis 是老师批注——告诉你错在哪道题、错误原因是什么、下次怎么避免。

---

### 差距 5：展示视图的根本差异

**Langfuse 的视图：Trace Timeline**
- 横向时间轴展示 LLM 调用序列
- 每个节点显示：input/output、token数、latency、一个 score 数值
- 适合看"Agent 和模型交互了几次"
- 看不到：文件改了什么、命令执行结果、测试是否通过

**CCWhat 的视图：Task Evidence Board**
- 任务为中心的因果图谱
- 展示：`instruction` → `commands[]` → `diff.patch` → `test output` 的因果链
- 诊断结果直接标注在证据上："测试失败 ← 命令[2] ← 错误[0]"

> **一句话**：Langfuse 展示的是"Agent 怎么聊天的"，CCWhat 展示的是"Agent 怎么干活的"以及"干成了没有"。

---

### 差距 6：诊断结果的可验证性

**Langfuse Score 的问题**：
```json
"quality": 0.7, "comment": "mostly relevant"
```
- 为什么是 0.7 不是 0.6？无法验证
- "mostly relevant" 指什么？无法追溯到具体证据
- 这是 LLM 的主观判断还是客观事实？分不清楚

**CCWhat diagnosis 的可验证性**：
```json
{
  "cause": "测试未通过",
  "evidence": ["test_commands[0]: pytest", "errors[0]: AssertionError"],
  "confidence": "high",
  "source": "rule"
}
```
- 每条证据都有确切路径 `test_commands[0]`
- 用户可以手动打开 `task_trace.json` 验证
- `confidence: "high"` 因为是规则层检测（exit_code != 0），非主观判断
- `source: "rule"` vs `source: "llm"` 明确区分确定性

> **一句话**：Langfuse 的诊断是"黑盒评分"，CCWhat 的诊断是"白盒推理"。

---

## 六、Langfuse 的评估能力到底是什么

Langfuse 确实有评估功能，但需要准确理解其边界：

| 评估方式 | Langfuse 的实现 | 局限 |
|---------|----------------|------|
| **LLM-as-a-judge** | 你写 prompt 让 LLM 给 trace 打分 | 评分是标量，无结构化因果解释；依附于 trace 节点，非跨节点归因；需人工预设标准 |
| **人工标注** | 人在 UI 上看 trace 后手动选分数 | 成本高，无法自动化 |
| **程序化评分** | 你自己调用 API 上传一个数值 | 只是存储，不是诊断 |

**与 CCWhat 的根本差异**：

Langfuse 的评估是**事后标签系统**——你需要提前定义"什么叫质量好"，然后让 LLM 或人给每个 trace 贴标签。

CCWhat 的归因诊断是**自动证据推理**——不需要人工预设标准，直接从 `diff.patch`、`errors[]`、`test_commands[]` 等证据推导失败原因。

---

## 七、全维度对比表

| 维度 | Langfuse | CCWhat |
|------|---------|--------|
| 原子观测单元 | LLM API 调用（Generation） | 编程动作（NormalizedEvent） |
| 核心问题 | 这次调用花了多少 token / 钱 / 时间？ | Agent 做了什么？做成了吗？为什么失败？ |
| Ground truth | Agent 的输出文本（无验证） | `diff.patch`（git 物证）+ 完整快照 |
| 测试结果捕获 | ❌ 不捕获 | ✅ `test_commands[]` + `errors[]` |
| 命令执行捕获 | ❌ 不捕获 | ✅ `commands[]` 逐条记录 |
| 文件系统快照 | ❌ | ✅ `repo_before/after.tar.gz` |
| Agent 声明 vs 实际改动 | ❌ 无法验证 | ✅ `final_claim` vs `diff.patch` 交叉验证 |
| 任务边界 | 开发者代码层的 traceId（软标记） | 用户意图层的 start/finish（高置信度） |
| 缺失证据处理 | 显示空白 | `evidence_availability` 显式标记 |
| 评估输出结构 | 标量分数（数值/分类/布尔） | 结构化因果链（原因 + 证据链 + confidence + 来源） |
| 诊断可验证性 | 黑盒评分（无法追溯证据） | 白盒推理（每条结论有证据路径） |
| 展示视图 | Trace Timeline（LLM 调用序列） | Task Evidence Board（因果证据图谱） |
| 长程任务支持 | 弱（适合单次调用分析） | 强（适合 20-50 轮的多文件任务） |
| 核心适用场景 | 通用 LLM API 可观测性 | Coding Agent 任务归因诊断 |

---

## 八、定位关系

Langfuse 和 CCWhat 不是同一层次的竞争：

```
CCWhat
  └── 任务语义层：任务边界 / 归因诊断 / 代码感知
  └── 代码物证层：git diff / 文件快照 / 命令执行
  └── 行为轨迹层：NormalizedEvent / 编程动作分类

Langfuse
  └── LLM 调用可观测性：token 计数 / 延迟 / 成本 / 标量评分
```

Langfuse 解决的是"LLM 调用的可观测性"，CCWhat 解决的是"Coding Agent 任务的归因诊断"。前者是通用 infrastructure，后者是 Coding Agent 专用的诊断引擎——关注代码有没有真正被正确修改，而不是 API 调用是否成功返回。

---

## 九、一句话总结

**Langfuse 回答的问题是**："这次 LLM 调用花了多少钱、质量如何？"  
**CCWhat 回答的问题是**："Agent 说改了登录逻辑，真的改了吗？测试过了吗？为什么还报错？"
