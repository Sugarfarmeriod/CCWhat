# Plan 3: Auto Attribution Diagnosis 实施计划

> 基于调研结果，将归因诊断引擎拆分为 3 个可独立交付的 Change。
> 每个 Change 完成后都有独立可运行的验收结果，不依赖后续 Change。

---

## 总体架构

```
V2 Dataset (task_trace.json + diff.patch + task.json)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  规则层 (Rule-based)                                         │
│  ├── diff 为空检查（Agent 根本没改代码）                      │
│  ├── 测试失败检查（test_commands 存在但 errors 有失败信息）    │
│  ├── 命令错误退出检查（exit_code != 0）                       │
│  └── 只读未改检查（files.read 有，files.changed 为空）        │
│  → 输出: confidence=high, source=rule                        │
└─────────────────────────────────────────────────────────────┘
    │
    ▼ 规则层无法覆盖的语义问题
┌─────────────────────────────────────────────────────────────┐
│  LLM 层 (LLM-based)                                          │
│  ├── instruction vs diff 语义匹配（改动是否与任务相关）        │
│  ├── final_claim vs diff 矛盾检测（声称做了 vs 实际改了）      │
│  └── 规则层结果作为上下文，避免重复分析                       │
│  → 输出: confidence=medium, source=llm                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
diagnosis.json（写入 task 目录）
```

---

## Change 1: `add-diagnosis-rule-engine`

**目标**：实现规则层 MVP，覆盖高确定性归因场景，零 LLM 成本，毫秒级响应。

**范围**：

- 新建 `ccwhat/diagnosis/` 模块
- 定义 `DiagnosisResult` 数据模型（对齐 diagnosis.json 结构）
- 实现四个确定性检查器：
  - `DiffEmptyChecker`：diff.patch 为空，且 final_claim 非空 → "声称完成但无改动"
  - `TestFailureChecker`：errors[] 包含测试失败信息 → "测试未通过"
  - `CommandErrorChecker`：commands[] 中有 exit_code != 0 → "命令执行失败"
  - `FileReadOnlyChecker`：files.read 非空且 files.changed 为空 → "只读未改"
- 实现 `RuleEngine`，组合四个检查器，输出合并后的 diagnosis.json
- CLI 入口：`ccwhat diagnose --task-dir <path>`

**diagnosis.json 输出格式**：

```json
{
  "task_id": "task-001",
  "summary": "Agent 声称完成但测试未通过",
  "likely_root_causes": [
    {
      "cause": "测试未通过",
      "evidence": [
        "test_commands[0]: pytest tests/unit/",
        "errors[0]: AssertionError: expected True, got False"
      ],
      "confidence": "high",
      "source": "rule"
    }
  ],
  "missing_evidence": [],
  "confidence": "high"
}
```

**验收标准**：

- 给定一个 V2 task 目录，能输出完整 diagnosis.json
- diff 为空且 final_claim 非空时，正确识别"声称完成但无改动"
- 测试失败时，诊断引用具体命令和错误信息
- 无问题时输出 likely_root_causes 为空，不制造假阳性
- evidence_availability 有缺失项时，diagnosis 明确说明无法判断

---

## Change 2: `add-diagnosis-llm-layer`

**目标**：覆盖规则层无法处理的语义级问题，confidence=medium。

**前置**：Change 1 完成。

**范围**：

- 实现 `LLMDiagnosisEngine`，接收规则层结果 + V2 Dataset 证据作为输入
- 设计诊断专用 Prompt，覆盖两类语义问题：
  - **instruction vs diff 语义匹配**：改动是否与任务描述相关（改了 README 但任务是修复登录 bug）
  - **final_claim vs diff 矛盾**：Agent 声称修复了什么，与实际 diff 是否一致（需要语义理解，不适合关键词匹配）
- 规则层已发现的问题作为 LLM 上下文，避免重复分析
- Token 预算控制：只传入相关证据片段，不读全量文件
- 输出合并进 diagnosis.json，source=llm

**Prompt 结构**：

```
你是 Coding Agent 任务诊断专家。

规则层已发现：{rule_findings}

请基于以下证据，分析规则层未覆盖的语义问题：

- 任务指令: {instruction}
- 代码改动文件: {diff_files_summary}
- Agent 最终声明: {final_claim}
- 执行命令（摘要）: {commands_summary}
- 错误信息: {errors_summary}

只输出规则层未发现的问题。不要编造证据中没有的信息。
```

**验收标准**：

- instruction 与 diff 明显不匹配时，LLM 层能给出语义解释
- final_claim 与 diff 存在语义矛盾时，能正确识别
- 规则层已发现的问题不重复出现在 LLM 层输出中
- source=llm, confidence=medium

---

## Change 3: `add-diagnosis-persistence-and-viewer`

**目标**：打通端到端流程，让诊断结果可落盘、可查看。

**前置**：Change 1 完成（Change 2 可选）。

**范围**：

- diagnosis.json 写入 task 目录
- task.json 新增字段：`paths.diagnosis`、`evidence_availability.diagnosis=true`
- CLI 查看命令：`ccwhat diagnose --task-dir <path> --show`，输出人类可读的诊断摘要
- `ccwhat diagnose --task-dir <path> --json`，输出原始 diagnosis.json

**验收标准**：

- 诊断结果正确写入 task 目录，task.json 同步更新
- CLI `--show` 输出可读摘要，包含 summary 和每条 root_cause 的 cause + evidence
- 端到端：给定一个真实 task 目录，一条命令跑完规则层 + LLM 层 + 落盘

---

## 实施顺序

```
Change 1（规则层引擎）
    │
    ├──→ Change 3（落盘与查看）   ← Change 1 完成即可开始
    │
    └──→ Change 2（LLM 层）       ← Change 1 完成即可开始，与 Change 3 并行
```

Change 2 和 Change 3 没有互相依赖，可以并行推进。

---

## 关键设计决策

**为什么 final_claim vs diff 矛盾检查放在 LLM 层，而不是规则层？**

判断"声称改了 auth 逻辑"对应哪些文件，需要语义理解。用关键词匹配做这件事，假阴性率高（Agent 说"修复了验证问题"，关键词匹配不到"auth"就漏掉）。规则层只做有客观物证支持的确定性判断，语义判断交给 LLM 层。

**为什么不做 Phase 2（结构化数据推理）？**

文件读写比例、命令重复次数等启发式规则，confidence 标注为 high 但依据是经验阈值，实际上是中等置信度的猜测。这类模式 LLM 层处理更准确，且不需要单独一个 Phase。等诊断引擎跑起来后根据真实数据再决定是否补充。

**为什么不做 Phase 4（验证框架）？**

准确率/召回率验证框架在 MVP 阶段是过度设计。先把诊断跑起来，用真实 task 手动验证，再决定是否需要系统化验证工具。
