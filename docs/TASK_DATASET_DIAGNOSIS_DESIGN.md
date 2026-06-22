# Task Dataset Diagnosis Design

## 背景

当前 CCWhat 的 Dataset v1 已经可以从 Agent 本地日志中抽取 Task Trace，并保存 `manifest.json`、`dataset.jsonl`、`traces/*.json`、`scores.jsonl` 等基础文件。

这套结构适合回答：

```text
用户让 Agent 做了什么？
Agent 实际执行了哪些步骤？
读了哪些文件？
改了哪些文件？
跑了哪些命令？
有没有报错？
最后声称完成了什么？
```

但如果后续目标是做 **问题诊断、失败归因、离线评测、训练数据沉淀**，仅有 Trace 还不够。

诊断真正需要的是：

```text
这个 Task 开始前代码是什么样？
Agent 修改后代码变成什么样？
真实 diff 是什么？
命令和测试输出是什么？
Agent 的操作路径和代码变化之间如何对应？
当前证据是运行时记录的，还是事后从日志/Git 中推断的？
```

因此，未来 Dataset 不应该只是“清洗后的日志”，而应该是：

```text
源码现场 + Agent Trace + 原始日志 + 轻量索引 + 证据完整度说明
```

一句话定义：

> Dataset 是一个可复盘、可诊断、可评测、可二次加工的 Task 现场包。

---

## 最终推荐结构

未来 Dataset 建议采用如下结构：

```text
ccwhat-dataset/
  manifest.json

  raw/
    claude_session.jsonl
    codex_session.jsonl
    opencode_session.jsonl
    raw_req_resp/

  session/
    session_trace.json
    task_segments.json

  tasks/
    task-001/
      task.json
      task_trace.json
      repo_before.tar.gz
      repo_after.tar.gz
      diff.patch
      commands.jsonl
      test_outputs/
      diagnosis.json

    task-002/
      task.json
      task_trace.json
      repo_before.tar.gz
      repo_after.tar.gz
      diff.patch
      commands.jsonl
      test_outputs/
      diagnosis.json

  scores.jsonl
```

其中：

| 路径 | 作用 |
| --- | --- |
| `manifest.json` | Dataset 自身说明：版本、创建时间、Agent、项目、session id、证据来源等 |
| `raw/` | 原始日志和原始请求/响应，用于保底和重新解析 |
| `session/session_trace.json` | 从原始日志清洗出来的完整 Session Trace |
| `session/task_segments.json` | Session 被切分成哪些 Task，以及每个 Task 的边界 |
| `tasks/<task-id>/task.json` | 单个 Task 的定义、索引、证据可用性说明 |
| `tasks/<task-id>/task_trace.json` | 单个 Task 内 Agent 的具体执行步骤 |
| `tasks/<task-id>/repo_before.tar.gz` | Task 开始前源码快照 |
| `tasks/<task-id>/repo_after.tar.gz` | Task 结束后源码快照 |
| `tasks/<task-id>/diff.patch` | `repo_before` 到 `repo_after` 的真实 diff |
| `tasks/<task-id>/commands.jsonl` | Agent 执行过的命令及输出 |
| `tasks/<task-id>/test_outputs/` | 测试输出、报错输出、日志文件 |
| `tasks/<task-id>/diagnosis.json` | 后续诊断结果，初始可以为空 |
| `scores.jsonl` | 后续 evaluator 追加的评分结果 |

---

## Session Trace 和 Task Trace 的关系

两个 Trace 都需要保留，但诊断核心是 **Task Trace**。

```text
原始 Agent 日志
  -> 清洗成 session_trace.json
  -> 根据 task segmentation 切成多个 task_trace.json
```

含义：

```text
session_trace.json = 整个会话发生了什么

task_trace.json = 某个具体任务里 Agent 怎么做的
```

后续诊断主要消费：

```text
task_trace.json + repo_before + repo_after + diff.patch + commands/test outputs
```

Session Trace 主要用于：

```text
回溯全局上下文
检查 Task 边界是否合理
理解多个 Task 之间是否存在上下文依赖
重新切分 Task
```

---

## task.json 推荐字段

`task.json` 是单个 Task 的索引和证据说明，不需要放完整执行过程。

示例：

```json
{
  "task_id": "task-001",
  "instruction": "修复 dataset 导出问题",
  "session_id": "...",
  "agent": "claude",
  "boundary": {
    "start_event_id": "main:42",
    "end_event_id": "main:88",
    "start_turn": 3,
    "end_turn": 7
  },
  "paths": {
    "task_trace": "task_trace.json",
    "repo_before": "repo_before.tar.gz",
    "repo_after": "repo_after.tar.gz",
    "diff": "diff.patch",
    "commands": "commands.jsonl",
    "test_outputs": "test_outputs/",
    "diagnosis": "diagnosis.json"
  },
  "evidence_availability": {
    "raw_log": true,
    "session_trace": true,
    "task_trace": true,
    "repo_before": true,
    "repo_after": true,
    "git_diff": true,
    "command_outputs": true,
    "test_outputs": true
  },
  "evidence_source": {
    "trace": "claude_log",
    "repo_before": "ccwhat_runtime_snapshot",
    "repo_after": "ccwhat_runtime_snapshot",
    "diff": "git_diff",
    "command_outputs": "agent_log"
  },
  "confidence": "high"
}
```

核心原则：

```text
Dataset 格式统一，但不同来源的数据完整度不同。
```

因此，`repo_before`、`repo_after`、`diff.patch` 不应该被假设一定存在，而应该通过 `evidence_availability` 和 `evidence_source` 明确说明。

---

## task_trace.json 推荐字段

`task_trace.json` 保存 Agent 在该 Task 内的具体执行步骤。

示例：

```json
{
  "task_id": "task-001",
  "instruction": "修复 dataset 导出问题",
  "events": [
    {
      "step": 1,
      "event_id": "main:42",
      "type": "user_message",
      "content": "用户让 Agent 做什么"
    },
    {
      "step": 2,
      "event_id": "main:43",
      "type": "tool_call",
      "tool": "Read",
      "file": "ccwhat/task_dataset/builder.py"
    },
    {
      "step": 3,
      "event_id": "main:44",
      "type": "tool_call",
      "tool": "Edit",
      "file": "ccwhat/task_dataset/builder.py",
      "old_string": "...",
      "new_string": "..."
    },
    {
      "step": 4,
      "event_id": "main:45",
      "type": "command",
      "command": "pytest tests/test_task_dataset.py",
      "output_path": "test_outputs/pytest.txt"
    }
  ],
  "files_read": [],
  "files_changed": [],
  "commands": [],
  "test_commands": [],
  "changes": [],
  "patches": [],
  "errors": [],
  "final_claim": "Agent 最后声称完成了什么"
}
```

注意：

```text
task_trace.json 记录 Agent 行为过程。
repo_before/repo_after/diff.patch 记录代码事实现场。
两者都需要，不能互相替代。
```

---

# 三种数据来源场景

未来 Dataset 需要兼容三种主要情况。

---

## 情况 A：只有 Agent 落盘日志 + 最终代码

### 输入

```text
.claude / Codex / OpenCode 本地日志
已经改完后的代码仓库
```

### 能稳定获得

```text
raw Agent log
session_trace.json
task_segments.json
task_trace.json
repo_after.tar.gz
files_read / files_changed
commands / test_commands
errors / final_claim
部分 old_string / new_string / patch 证据
```

### 很难可靠获得

```text
每个 Task 的 repo_before.tar.gz
每个 Task 的 repo_after.tar.gz
每个 Task 的真实 diff.patch
每一步修改前后的完整文件内容
完整依赖上下文
```

### 原因

用户把数据交给 CCWhat 时，代码已经是最终状态。

Agent 日志可以说明 Agent 做过什么，但不能保证保存了每个 Task 开始前和结束后的完整源码现场。

### 推荐处理方式

生成 best-effort Dataset：

```text
tasks/task-001/
  task.json
  task_trace.json
  repo_after.tar.gz
  inferred_changes.json
```

`task.json` 中必须标记：

```json
{
  "evidence_availability": {
    "raw_log": true,
    "task_trace": true,
    "repo_before": false,
    "repo_after": true,
    "git_diff": false
  },
  "evidence_source": {
    "trace": "agent_log",
    "repo_after": "user_uploaded_final_repo",
    "diff": "inferred_from_agent_log"
  },
  "confidence": "low"
}
```

### 适合做的诊断

```text
Agent 行为诊断
是否读了相关文件
是否执行了命令/测试
是否有明显报错
final claim 和行为证据是否矛盾
基于 old_string/new_string 的局部改动分析
```

### 不适合做的诊断

```text
完整代码现场复盘
每个 Task 的真实 before/after 对比
可靠复现
跨文件依赖链路诊断
精确失败归因
```

---

## 情况 B：Agent 落盘日志 + 仓库 + Git 历史

### 输入

```text
Agent 本地日志
代码仓库
Git commit 历史
```

### 能获得什么，取决于 Git 历史粒度

#### B1：每个 Task 或关键步骤都有 commit

这是比较理想的情况。

可以通过 Git 还原：

```text
task-001/
  repo_before.tar.gz   # checkout task 开始前 commit
  repo_after.tar.gz    # checkout task 结束后 commit
  diff.patch           # git diff before..after
  task_trace.json      # 从 Agent 日志切出来
```

这种 Dataset 质量较高。

#### B2：整个 Session 结束后只有一个 commit

只能获得 Session 级别的代码现场：

```text
session_repo_before.tar.gz
session_repo_after.tar.gz
session.diff.patch
```

可以切分出多个 Task Trace，但每个 Task 的 before/after 不能可靠还原。

这时每个 Task 的 `diff.patch` 只能来自 Agent 日志中的 patch、old_string/new_string，或者从全局 session diff 中 best-effort 分配。

#### B3：没有 commit，但有 dirty working tree

通常只能获得：

```text
当前 repo_after
当前 dirty diff
```

很难还原 Task 级别 before。

### 推荐处理方式

先做 Git-aware Dataset Builder：

```text
1. 解析 Agent 日志，生成 Session Trace 和 Task Trace
2. 读取 Git commit 历史
3. 尝试把 Task 时间/事件边界和 commit 对齐
4. 如果可以对齐，就生成 Task 级 repo_before/repo_after/diff.patch
5. 如果不能对齐，就退化为 Session 级快照和低置信度 Task diff
```

`task.json` 示例：

```json
{
  "evidence_availability": {
    "raw_log": true,
    "task_trace": true,
    "repo_before": true,
    "repo_after": true,
    "git_diff": true
  },
  "evidence_source": {
    "trace": "agent_log",
    "repo_before": "git_commit",
    "repo_after": "git_commit",
    "diff": "git_diff"
  },
  "confidence": "medium"
}
```

如果只能拿到 Session 级快照：

```json
{
  "evidence_availability": {
    "raw_log": true,
    "task_trace": true,
    "repo_before": false,
    "repo_after": false,
    "session_repo_before": true,
    "session_repo_after": true,
    "git_diff": "session_level_only"
  },
  "confidence": "medium_low"
}
```

### 适合做的诊断

Git 粒度足够细时：

```text
Task 级代码复盘
真实 diff 分析
测试失败归因
部分跨文件诊断
```

Git 粒度较粗时：

```text
Session 级复盘
行为诊断
粗粒度失败归因
```

---

## 情况 C：用户边用 CCWhat 边开发

### 输入

```text
用户通过 CCWhat 包装/接入 Claude Code、Codex、OpenCode 等 Agent
CCWhat 在后台实时采集日志、命令、文件变化、Git 状态和源码快照
```

### 这是最理想、最应该优先支持的情况

因为 CCWhat 可以在运行时主动记录，而不是事后推断。

### 推荐采集流程

```text
Task 开始时：
  记录 task_id
  记录 start_event_id
  记录当前 git commit
  记录 git status
  打 repo_before.tar.gz
  开始收集 task_trace

Task 过程中：
  收集 Agent 工具调用
  收集文件读写
  收集命令输出
  收集测试输出
  收集错误信息

Task 结束时：
  记录 end_event_id
  记录 git status
  打 repo_after.tar.gz
  生成 diff.patch
  保存 task_trace.json
  保存 task.json
```

### 能稳定获得

```text
raw Agent log
session_trace.json
task_segments.json
task_trace.json
repo_before.tar.gz
repo_after.tar.gz
diff.patch
commands.jsonl
test_outputs/
files_read / files_changed
errors / final_claim
```

### `task.json` 示例

```json
{
  "evidence_availability": {
    "raw_log": true,
    "session_trace": true,
    "task_trace": true,
    "repo_before": true,
    "repo_after": true,
    "git_diff": true,
    "command_outputs": true,
    "test_outputs": true
  },
  "evidence_source": {
    "trace": "ccwhat_runtime_trace",
    "repo_before": "ccwhat_runtime_snapshot",
    "repo_after": "ccwhat_runtime_snapshot",
    "diff": "git_diff",
    "command_outputs": "ccwhat_runtime_capture"
  },
  "confidence": "high"
}
```

### 适合做的诊断

```text
Task 级完整复盘
真实 before/after 对比
真实 diff 诊断
测试失败归因
跨文件依赖诊断
后续 evaluator
训练数据转换
SFT / DPO / RL 数据沉淀
```

---

## 三种情况对比

| 场景 | Task Trace | repo_before | repo_after | diff.patch | 证据质量 | 适合用途 |
| --- | --- | --- | --- | --- | --- | --- |
| A：只有日志 + 最终代码 | 有 | 基本没有 | 有最终状态 | 部分推断 | 低到中 | 事后行为分析 |
| B：日志 + Git 历史 | 有 | 看 Git 粒度 | 看 Git 粒度 | 看 Git 粒度 | 中到高 | Git-aware 复盘 |
| C：CCWhat 实时记录 | 有 | 稳定有 | 稳定有 | 稳定有 | 最高 | 核心诊断数据 |

---

## 产品优先级建议

推荐优先级：

```text
第一优先级：C，CCWhat 实时采集高质量 Dataset
第二优先级：B，利用 Git 历史做事后还原
第三优先级：A，只做 best-effort 导入和低置信度分析
```

原因：

```text
A 是历史数据导入能力，不是核心壁垒。
B 有价值，但质量依赖用户 Git 习惯。
C 是 CCWhat 能主动创造高质量数据的地方，也是未来可观测、诊断、评测、训练数据闭环的核心。
```

因此，CCWhat 的主线应该是：

```text
用户边用 Agent 开发，CCWhat 边记录 Task 现场。
```

而不是：

```text
事后从不完整日志里硬还原完整诊断现场。
```

---

## 关键设计原则

### 1. 先保现场，再做清洗

不要一开始就追求完美标准化 Dataset。

优先保证：

```text
这个 Task 以后一定能复盘。
```

### 2. Dataset 字段统一，但证据可缺失

不同来源下，数据完整度不同。

所以必须显式记录：

```text
evidence_availability
evidence_source
confidence
```

### 3. Trace 和源码快照都必须保留

```text
Trace 说明 Agent 怎么做。
源码快照说明代码真实变成了什么样。
```

只有 Trace，没有源码现场，难以做代码诊断。

只有源码现场，没有 Trace，难以定位 Agent 从哪一步走偏。

### 4. Task Trace 是核心消费对象

Session Trace 用于全局回溯。

真正诊断时，主要分析：

```text
task_trace.json
repo_before.tar.gz
repo_after.tar.gz
diff.patch
commands.jsonl
test_outputs/
```

### 5. A/B/C 都支持，但不要混淆质量

不能把 A 场景下推断出来的数据伪装成 C 场景下运行时采集的数据。

所有 Dataset 都应该明确标记证据来源和置信度。

---

## 一句话总结

未来 CCWhat Dataset 应该长这样：

```text
每个 Task = 任务说明 + Agent 执行 Trace + 修改前源码快照 + 修改后源码快照 + 真实 diff + 命令/测试输出 + 证据来源说明
```

三种来源的定位是：

```text
A：事后弱证据，能做行为诊断。
B：Git 还原证据，能做中等质量复盘。
C：运行时强证据，是 CCWhat 的核心主线。
```

最终目标：

```text
把 Agent 开发过程沉淀成可复盘、可诊断、可评测、可训练的数据资产。
```
