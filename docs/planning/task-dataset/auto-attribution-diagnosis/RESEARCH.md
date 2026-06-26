# 自动归因诊断调研报告

> 调研目标：为 Plan 3（Auto Attribution Diagnosis）提供业界和学术界的参考依据
>
> 调研日期：2026-06-25

---

## 4. 两层诊断架构的业界验证

### 4.1 架构模式共识

调研发现，业界普遍采用**规则+LLM 混合**的评估/诊断架构：

```
Input: Trace + Artifacts
    │
    ▼
┌─────────────┐     ┌─────────────┐
│   规则层     │────▶│   LLM 层    │
│ Rule-based  │     │ LLM-based   │
│ 快速、确定   │     │ 深度、语义   │
└─────────────┘     └─────────────┘
    │                       │
    ▼                       ▼
┌─────────────┐     ┌─────────────┐
│ High Conf   │     │ Medium Conf │
│ 确定性问题   │     │ 语义类问题   │
└─────────────┘     └─────────────┘
```

### 4.2 各层能力边界

| 层级 | 响应速度 | 成本 | 适用场景 | 典型输出 |
|------|----------|------|----------|----------|
| **规则层** | < 100ms | 低 | 命令未运行、测试失败、diff 为空、文件未修改 | high confidence |
| **LLM 层** | 1-5s | 高 | 语义矛盾、意图理解偏差、多因素交织 | medium confidence |

### 4.3 Evidence Linking 模式

**Phoenix Span Replay**：
- 每个 span 有唯一 ID
- 诊断结果引用 span ID
- 支持从诊断结果跳转到具体执行节点

**Langfuse Trace Annotation**：
- 在 trace 节点上附加评估结果
- 支持多级评估（evaluation of evaluation）

**Plan 3 建议格式**：
```json
{
  "evidence": [
    {
      "source": "task_trace",
      "path": "commands[2]",
      "data": {"command": "pytest", "exit_code": 1}
    },
    {
      "source": "diff.patch",
      "path": "files",
      "data": {"added": 0, "removed": 0}
    }
  ]
}
```

---

## 5. 关键设计决策建议

### 5.1 规则层设计

**应该覆盖的确定性问题**：

| 检查项 | 判断逻辑 | Confidence |
|--------|----------|------------|
| 无代码改动 | `diff.patch` 为空 | high |
| 声称完成但无改动 | `diff.patch` 为空 && `final_claim` 非空 | high |
| 测试未运行 | `test_commands` 为空 | high |
| 测试失败 | `errors[]` 包含 test failure | high |
| 命令错误退出 | `commands[].exit_code != 0` | high |
| 只读未改 | `files.read` 非空 && `files.changed` 为空 | high |

**实现建议**：
- 使用纯代码逻辑，无 LLM 调用
- 返回结构化结果，包含明确的问题类型和证据引用

### 5.2 LLM 层设计

**应该覆盖的语义问题**：

| 检查项 | 判断逻辑 | Confidence |
|--------|----------|------------|
| 改动与任务不相关 | `instruction` vs `files.changed` 语义匹配度 | medium |
| final_claim 与 diff 矛盾 | 声称修复的问题 vs 实际改动 | medium |
| 过早放弃 | 任务难度 vs 尝试次数 vs 最终状态 | medium |
| 方向性错误 | 修改的文件与问题定位不匹配 | medium |

**Prompt 设计建议**：
```
你是一个 Coding Agent 任务诊断专家。

请基于以下证据分析任务失败的原因：

[证据]
- 任务指令: {instruction}
- 预期测试: {expected_tests}
- Agent 行为轨迹: {task_trace.events}
- 执行命令: {task_trace.commands}
- 错误信息: {task_trace.errors}
- 代码改动: {diff.patch}
- 最终声明: {task_trace.final_claim}

[输出格式]
{
  "cause": "失败原因简述",
  "detailed_analysis": "详细分析",
  "evidence_links": ["证据引用"],
  "confidence": "medium"
}

注意：不要编造证据中没有的信息。
```

### 5.3 Confidence Calibration

**High Confidence（规则层输出）**：
- 基于确定性检查
- 有明确的反事实验证
- 误诊率 < 1%

**Medium Confidence（LLM 层输出）**：
- 基于语义分析
- 存在合理的替代解释
- 建议人工复核

**Low Confidence（证据不足）**：
- `evidence_availability` 有缺失项
- 明确说明"无法判断"

---

## 6. 与 V2 Dataset 的契合点

V2 Dataset 已具备业界 observability 平台的核心数据要素：

| V2 Dataset | 业界对应 | 归因用途 |
|------------|----------|----------|
| `task_trace.json` | Langfuse Traces | 完整行为轨迹，归因证据来源 |
| `diff.patch` | Code changes | 实际改动证据 |
| `control_events.jsonl` | Session tracking | 任务边界标定，时间窗口 |
| `repo_before/after.tar.gz` | Snapshots | 支持重放调试 |
| `task.json` | Metadata | 任务语义（instruction, expected_tests） |

**结论**：Plan 3 的数据基础已经完备，可以立即开始实现。

---

## 7. 推荐实现路径

### 7.1 Phase 1：规则层 MVP（1-2 天）

1. 实现基础检查器框架
2. 覆盖 5-6 个高确定性问题类型
3. 输出结构化 `diagnosis.json`

### 7.2 Phase 2：LLM 层集成（2-3 天）

1. 设计诊断专用 prompt
2. 实现证据筛选逻辑（不读全量文件）
3. 集成规则层结果作为 LLM 上下文

### 7.3 Phase 3：置信度校准（1-2 天）

1. 收集测试数据，验证误诊率
2. 调整 confidence threshold
3. 完善 evidence linking 格式

---

## 8. 参考资源

### 8.1 工具与平台

- Langfuse：https://langfuse.com/docs
- Arize Phoenix：https://arize.com/docs/phoenix
- OpenHands：https://github.com/All-Hands-AI/OpenHands
- SWE-bench：https://www.swebench.com/

### 8.2 论文

- Multi-Agent Scaffolding：https://arxiv.org/abs/2606.25514
- Agent Instructions Evolution：https://arxiv.org/abs/2606.25257
- Detecting AI Coding Agents：https://arxiv.org/abs/2606.24429

### 8.3 相关文档

- OpenHands Verification Stack Blog：https://www.openhands.dev/blog

---

## 9. 待进一步调研的问题

1. **归因的可解释性**：如何让诊断结果更易被人理解和验证？
2. **多因素归因**：当多个原因交织时，如何分配权重？
3. **归因的修复建议**：诊断结果如何转化为可执行的修复动作？
4. **大规模验证**：如何批量验证归因准确性？

---

*文档版本：v1.0*

*下一步行动：基于本调研结果，起草 `add-auto-attribution-diagnosis` OpenSpec change 文档*
