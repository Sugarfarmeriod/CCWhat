# CCWhat Version Roadmap

这份文档记录 CCWhat 从日志查看器到数据闭环平台的版本规划。

## 当前结论

如果 Dataset 保存和导出能力已经完整可用，并且能生成：

```text
manifest.json
dataset.jsonl
traces/*.json
scores.jsonl
```

那么当前阶段可以发布为 **v2.0.0**。

原因很简单：

```text
V1 = Task Trace
V2 = Task Dataset
V3 = Evaluator / 自动诊断归因
```

Dataset 能力已经从“看任务”进入“沉淀任务数据”，这是主线能力升级，不只是 v1.x 的页面改进。

---

## 版本大纲

### v0.x — Session Observability

目标：看清 Agent 的原始执行过程。

核心能力：

- 读取 Claude Code 本地 JSONL session。
- 记录 req/resp 抓包数据。
- Web Viewer 展示 session、工具调用、原始请求响应。
- 初步支持导出和导入 session 数据。

一句话：

```text
把 Agent 做了什么先看清楚。
```

---

### v1.0 — Task Trace Viewer

目标：从长 session 中识别 task，并在 Viewer 中展示。

核心能力：

- 支持自动 Task 切分。
- Session Trace 双视图：默认视图 / 调试视图。
- 支持 `Task -> 会话 -> Step/Turn` 树形浏览。
- 支持 Task 起止事件定位、证据展示、原始 JSON 查看。

一句话：

```text
把长 session 拆成多个真实 coding task。
```

---

### v1.1 — Manual Task Overlay

目标：让用户可以人工修正 Task 切分结果。

核心能力：

- 手动框选创建 Task。
- 自动切分结果支持人工微调。
- 支持调整边界、拆分、合并、删除、修改标题和类型。
- 支持保存、撤销、导出 Overlay JSON。

一句话：

```text
自动切分不准时，允许人来校正。
```

---

### v2.0 — Task Dataset Builder

目标：把切出来的 Task 固化成标准数据资产。

核心能力：

- 支持保存 Dataset 到本地 Registry。
- 支持导出 Dataset 压缩包。
- Dataset 采用三层结构：

```text
Dataset = 要做什么
Trace   = 实际怎么做
Score   = 做得好不好
```

标准目录：

```text
ccwhat-dataset/
  manifest.json
  dataset.jsonl
  traces/
    trace-task-001.json
    trace-task-002.json
  scores.jsonl
```

字段原则：

- `dataset.jsonl` 只存任务定义和索引。
- `traces/*.json` 存执行过程、工具调用、命令、文件读写、changes、patches、errors、final claim。
- `scores.jsonl` 第一版可以为空，留给后续 evaluator 追加。

一句话：

```text
把不可复用的 session，变成可保存、可评测、可诊断的数据集。
```

---

### v2.1 — Change Evidence Extractor

目标：统一 Claude Code / Codex / OpenCode 的文件改动证据。

核心能力：

- Claude Code：提取 `Edit.old_string/new_string`、`Write.content`、`Bash.command`。
- OpenCode：提取 `oldString/newString`、`metadata.diff/filediff`、`apply_patch.patchText`。
- Codex：提取 `patch_apply_end`、`unified_diff`、新增文件 content。
- 统一输出 `changes` 和 `patches`。
- 不靠 LLM 猜 patch。

一句话：

```text
patch 不是必填字段，change evidence 才是统一抽象。
```

---

### v3.0 — Offline Evaluator / Score Layer

目标：基于 Dataset 和 Trace 判断任务是否成功。

核心能力：

- 读取 `dataset.jsonl` 和 `traces/*.json`。
- 执行或复用测试命令。
- 支持人工评分、规则评分、LLM judge、测试结果评分。
- 结果写入 `scores.jsonl`。

Score 示例：

```json
{
  "id": "score-001",
  "dataset_item_id": "task-001",
  "trace_id": "trace-task-001",
  "name": "task_success",
  "value": 1,
  "data_type": "BOOLEAN",
  "source": "test",
  "comment": "pytest passed"
}
```

一句话：

```text
Dataset 定义任务，Trace 记录过程，Score 判断结果。
```

---

### v4.0 — Failure Diagnosis

目标：对失败任务做自动归因。

输入：

```text
dataset item
+ trace events
+ changes / patches
+ commands / test output
+ score
```

输出：

- 失败类型。
- 根因解释。
- 关键证据。
- 建议修复方向。

一句话：

```text
先有标准数据和评分，再做可靠归因。
```

---

### v5.0 — Offline Eval Runner

目标：用 Dataset 重新跑 Agent，做离线评测。

核心能力：

- 从 Dataset 读取任务。
- 准备 repo 状态。
- 调用 Claude Code / Codex / OpenCode 执行。
- 采集新 trace。
- 跑 evaluator。
- 对比不同 Agent / Prompt / Workflow 的成功率、耗时、成本。

一句话：

```text
用真实任务数据反复测试 Agent。
```

---

### v6.0 — Prompt / Workflow / Skill Optimizer

目标：基于失败样本优化 Agent 工作流。

核心能力：

- 聚合失败原因。
- 生成 Prompt / Workflow / Skill 修改建议。
- 用 Offline Eval Runner 验证优化是否有效。
- 保留优化前后对比。

一句话：

```text
不是凭感觉调 Prompt，而是用数据验证优化。
```

---

### v7.0 — RL / Post-training Data Export

目标：把真实任务数据转成训练数据。

可能导出格式：

- SFT：成功轨迹。
- DPO：成功 / 失败对比。
- Reward Model：任务结果评分。
- RL Trajectory：完整 task execution trajectory。

一句话：

```text
CCWhat 最终沉淀真实 Coding Agent 训练数据。
```

---

## 当前发布建议

如果当前代码已经完成：

- Dataset Builder。
- Dataset 保存。
- Dataset 导出。
- Dataset validator。
- Trace 中包含 task-scoped events。
- Change evidence 能写入 trace `changes` / `patches`。

那么建议发布：

```text
v2.0.0 — Task Dataset Builder
```

如果只是 core builder 完成，但 Viewer 保存入口还没完全打通，则建议发布：

```text
v1.2.0 — Task Dataset Core Preview
```

版本判断标准：

```text
能从 Viewer 一键保存 / 下载 Dataset = v2.0.0
只能代码层 build_dataset_bundle = v1.2.0
```
