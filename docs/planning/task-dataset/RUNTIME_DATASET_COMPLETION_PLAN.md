# Runtime Dataset Completion Plan

## 目标

CCWhat 的最终目标是支持自动归因诊断。为此，Task Dataset 必须从"事后日志导出"升级为"运行时 Task 现场包"。

最终链路：

```text
ccwhat -- <agent>
  -> 启动 Coding Agent
  -> 原生 slash 菜单出现 CCWhat 命令
  -> 用户用 /ccwhat:start 和 /ccwhat:finish 手动切 Task
  -> CCWhat 后台记录 repo_before、repo_after、diff、trace、commands、test outputs
  -> Dataset 落盘为可复盘、可诊断、可评测的 Task 现场包
  -> 自动归因诊断消费 Dataset 并生成 diagnosis.json
```

本文档只定义后续 OpenSpec change 的总体切分。原则是：

- 子计划尽量少。
- 每个子计划里的 change 尽量少。
- 每个 change 都必须能独立验收。
- 不做 A/B 场景的事后推断主线，优先 C 场景运行时强证据。

## 总体切分（当前状态）

```text
Plan 1: Runtime Recording MVP
  Change 1: add-runtime-task-recording-mvp          ✅ 已完成并归档

Plan 2: Multi-Agent Slash Integration
  Change 2: add-codex-runtime-slash-integration     ⚠️  部分完成，暂停
  Change 3: add-opencode-runtime-command-integration ⚠️  部分完成，暂停
  Change 4: investigate-opencode-local-intercept     🚫 取消，不再推进

Plan 2.5: Dataset V2 Enrichment（新增）
  Change 5: enrich-runtime-task-trace               ✅ 已完成

Plan 3: Auto Attribution Diagnosis（下一阶段）
  Change 6: add-auto-attribution-diagnosis          🔲 待开始
```

---

## Plan 1: Runtime Recording MVP ✅

### Change 1: `add-runtime-task-recording-mvp` [已完成并归档]

**结果**：Claude Code 完全跑通。

打通的完整链路：

```text
ccwhat -- claude
  -> 创建 runtime run，自动分配端口
  -> 安装 Claude Code slash command integration
  -> /ccwhat:start 从原生菜单触发，本地 controller 拦截，不发给模型
  -> 保存 repo_before.tar.gz
  -> /ccwhat:finish 从原生菜单触发
  -> 保存 repo_after.tar.gz + diff.patch
  -> 写 task.json / control_events.jsonl
```

落盘结构：

```text
~/.ccwhat/runtime-runs/claude/<run-id>/
  run.json
  tasks/task-001/
    task.json                 (task_id, status, git before/after, paths, evidence_availability)
    control_events.jsonl      (model_visible=false, confidence=high)
    repo_before.tar.gz
    repo_after.tar.gz
    diff.patch
```

---

## Plan 2: Multi-Agent Slash Integration ⚠️

### 现状与决策

Plan 2 已部分实现，但主动选择暂停，优先推进归因诊断主线。

| Agent | 实现状态 | 已知问题 | 决策 |
|-------|---------|---------|------|
| Claude Code | ✅ 完全跑通 | 无 | 主线继续 |
| Codex | ⚠️ 部分完成 | slash command 不出现在菜单 | 暂停，不再投入 |
| OpenCode | ⚠️ 部分完成 | slash 可见但 model_visible=true；对话框有红色 UI 问题 | 暂停，不再投入 |

**判断依据**：Codex 和 OpenCode 的 slash 适配是"更多 agent 可以产数据"，而归因诊断是"数据转化为洞察"。Claude Code 已经能稳定产出完整 Dataset，足以支撑 Plan 3 的诊断引擎建设。等诊断引擎成熟后再回头补 agent 适配，届时有更强的动力和验收标准。

### Change 2: `add-codex-runtime-slash-integration` [暂停]

已完成的部分：
- `.codex/hooks.json` 已写入，hook 注册成功
- `ccwhat/runtime/codex_integration.py` + `codex_hook.py` 实现完整

未解决的问题：
- Codex slash command 不出现在菜单（命名格式或目录结构与 Codex 预期不符，原因未查明）

### Change 3: `add-opencode-runtime-command-integration` [暂停]

已完成的部分：
- `.opencode/command/ccwhat:start.md` + `ccwhat:finish.md` 写入
- `.opencode/plugin/ccwhat-runtime.js` 写入
- slash command 在 OpenCode 菜单中可见

未解决的问题：
- 命令触发后 model_visible=true（OpenCode 架构限制，command prompt 会发给模型）
- 对话框中显示红色渲染问题（原因未查明）

### Change 4: `investigate-opencode-local-intercept` [取消]

结论：当前阶段不具备技术条件做到 OpenCode 的真正本地拦截，且收益不足以覆盖调研成本。取消。

---

## Plan 2.5: Dataset V2 Enrichment ✅

本 plan 不在原始计划中，是在推进过程中发现的关键缺口后补充的。

### 背景：V1 vs V2 数据集对比

Runtime Staging（V2，新版）相比 Dataset v1（旧版）的本质区别：

| 维度 | V1（旧版，viewer 导出） | V2（新版，Runtime Staging） |
|------|----------------------|--------------------------|
| 任务边界 | 算法推断，不可靠 | 用户显式标定，可靠 |
| 真实改动证据 | ❌ 只有 Agent 自报 old/new_string | ✅ git diff + before/after 快照 |
| Agent 行为轨迹 | ✅ 完整 events、commands、errors | ❌ 完全没有 |
| 文件内容快照 | ❌ 只有路径 | ✅ 完整 tar.gz |

**关键缺口**：V2 知道代码改了什么，但不知道 Agent 是怎么改的。做归因诊断两类证据缺一不可。

### Change 5: `enrich-runtime-task-trace` [已完成]

**目标**：在 `/ccwhat:finish` 时，从 proxy session 日志按任务时间边界提取 Agent 行为轨迹，写成 `task_trace.json`，放入 task 目录，补齐 V2 缺口。

**新增文件**：

- `ccwhat/runtime/trace_extractor.py`：按时间窗口从 Claude 原生 session JSONL 提取事件，复用 `extract_evidence` + `extract_change_evidence`

**task 目录变化**：

```text
tasks/task-001/
  task.json                 新增: instruction, success_criteria, expected_tests
                            新增: paths.task_trace, evidence_availability.task_trace
  task_trace.json           ← 新文件
    {
      task_id, run_id, agent,
      time_window: {started_at, finished_at},
      events[],
      commands[], test_commands[],
      files: {read[], changed[]},
      changes[], patches[],
      errors[],
      final_claim,
      first_user_message,
      repo_state: {cwd, base_commit, head_commit}
    }
  control_events.jsonl
  repo_before.tar.gz
  repo_after.tar.gz
  diff.patch
```

**降级策略**：session 日志不存在时 `evidence_availability.task_trace=false`，不中断 finish 流程。

**完成后 V2 Dataset 具备的能力**：

```text
✅ 真实 git diff（代码改了什么）
✅ 完整 repo 快照（before/after）
✅ 可靠任务边界（用户标定）
✅ Agent 行为轨迹（events、commands、errors、final_claim）
✅ 任务语义（instruction、expected_tests）
```

---

## Plan 3: Auto Attribution Diagnosis 🔲

V2 Dataset 现在已具备归因诊断所需的全部数据。Plan 3 是最终目标层。

### 现有诊断能力评估

当前 V2 Dataset 已经可以支撑的判断：

```text
✅ Agent 有没有真的改文件（diff.patch 为空？）
✅ 改动是否与任务描述相关（instruction vs files.changed）
✅ 有没有跑测试（test_commands 是否存在）
✅ 测试有没有报错（errors[] 是否有测试失败信息）
✅ final_claim 与实际 diff 是否矛盾
✅ Agent 只读没改（files.read 有，files.changed 为空）
```

### Change 6: `add-auto-attribution-diagnosis`

**目标**：消费 V2 Dataset，生成初版归因诊断结果 `diagnosis.json`。

**两层诊断架构**：

```text
task_trace.json + diff.patch + repo_before/after
  -> 规则层（快，确定性强）
       命令未运行 / 测试失败 / diff 为空但声称完成 / final_claim 矛盾
  -> LLM 层（深，覆盖规则层遗漏的语义问题）
       只消费 Dataset evidence，不全量读文件
       输出结构化 diagnosis，标注 confidence 和 evidence links
  -> diagnosis.json
```

**diagnosis.json 结构**：

```json
{
  "task_id": "task-001",
  "summary": "...",
  "likely_root_causes": [
    {
      "cause": "测试未通过",
      "evidence": ["errors[0]: AssertionError ..."],
      "confidence": "high",
      "source": "rule"
    }
  ],
  "missing_evidence": ["success_criteria 未填写"],
  "confidence": "high",
  "recommended_next_steps": ["..."]
}
```

**验收标准**：

- 对一个 finalized task 能生成 `diagnosis.json`
- 测试失败时，诊断能引用具体 command/error 证据
- diff 为空但 final_claim 非空时，诊断能指出矛盾
- evidence_availability 有缺失项时，诊断明确说明不能判断
- medium-confidence boundary 不被当作 high-confidence 证据引用

**不在本 change 中做**：

- 训练数据转换（SFT/DPO/RL）
- 批量 benchmark
- 完整 evaluator 平台
- 诊断 UI（只做 JSON 输出，viewer 展示可后续补）

---

## 推荐执行顺序（更新后）

```text
✅ 1. add-runtime-task-recording-mvp      Claude Code 完整竖切
⚠️  2. add-codex-runtime-slash-integration  Codex 适配（暂停）
⚠️  3. add-opencode-runtime-command-integration  OpenCode 适配（暂停）
✅ 4. enrich-runtime-task-trace           V2 Dataset 补齐行为轨迹
🔲 5. add-auto-attribution-diagnosis      归因诊断引擎（下一步）
```

当前聚焦：**Change 6（归因诊断）**。Codex/OpenCode 适配等诊断引擎验证后再回头补。
