# Runtime Dataset Completion Plan

## 目标

CCWhat 的最终目标是支持自动归因诊断。为此，Task Dataset 必须从“事后日志导出”升级为“运行时 Task 现场包”。

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

## 总体切分

建议拆成 3 个子计划、6 个 OpenSpec change。

```text
Plan 1: Runtime Recording MVP
  Change 1: add-runtime-task-recording-mvp [已完成并归档]

Plan 2: Multi-Agent Slash Integration
  Change 2: add-codex-runtime-slash-integration
  Change 3: add-opencode-runtime-command-integration
  Change 4: verify-opencode-model-visibility-and-promote-confidence

Plan 3: Diagnosis-Ready Dataset and Attribution
  Change 5: promote-runtime-dataset-v2
  Change 6: add-auto-attribution-diagnosis
```

这样切的原因：

- Plan 1 先跑通一条完整竖切链路。
- Plan 2 把竖切链路推广到 Codex/OpenCode，并处理安装、升级、冲突和降级证据。
- Codex 已具备与 Claude 相近的 `UserPromptSubmit` block 能力，适合先做正式竖切。
- OpenCode 已确认支持项目级 command 和 `command.execute.before` plugin hook；是否完全不触发模型请求仍需抓包确认。
- Plan 3 在稳定采集能力上完成最终 Dataset 契约和自动归因诊断。

不建议拆成更多小 plan，因为过细会导致很多中间态只是在搭架子，不能直接证明最终目标。

---

## Plan 1: Runtime Recording MVP

### Change 1: `add-runtime-task-recording-mvp` [已完成并归档]

目标：先用一个 Agent 跑通完整 runtime recording 闭环。

推荐首个 Agent：

```text
Claude Code
```

原因：

- Claude Code 官方 hook 里有 `UserPromptSubmit`，可在 prompt 发送给模型前拦截并 block。
- 更容易验证“原生菜单可见 + 本地执行 + 不发送模型”的强证据路径。

### 范围

这个 change 一次性打通：

```text
ccwhat -- claude
  -> 创建 runtime run
  -> 自动分配 proxy/viewer/control 端口
  -> 安装或检查 Claude Code slash command integration
  -> /ccwhat:start 从原生菜单触发
  -> 本地 controller 收到 start
  -> 保存 repo_before.tar.gz
  -> /ccwhat:finish 从原生菜单触发
  -> 保存 repo_after.tar.gz
  -> 生成 diff.patch
  -> 写 task.json / control_events.jsonl
```

### 主要任务

1. Runtime run registry
   - 新增 `~/.ccwhat/runtime-runs/<agent>/<run-id>/run.json`
   - 记录 agent、workspace、pid、ports、active_task_id、status
   - 支持多个 run 并发

2. Auto port allocation
   - `ccwhat -- <agent>` 未显式指定端口时自动选择可用端口
   - 显式 `--port` / `--web-port` 继续保留
   - 最终端口写入 `run.json`

3. Runtime controller
   - 支持 `start`、`finish`、`status`、`abort`
   - 第一版可以使用 localhost HTTP control port，降低 hook/plugin 跨进程调用复杂度
   - control port 不暴露给普通用户，只写入 `run.json`

4. Task staging writer
   - `/ccwhat:start` 创建 `tasks/task-001/`
   - start 保存 `repo_before.tar.gz`
   - finish 保存 `repo_after.tar.gz`
   - finish 生成 `diff.patch`
   - 写 `task.json`
   - 写 `control_events.jsonl`

5. Claude Code native menu integration
   - 写入 CCWhat 管理的 Claude command/skill 文件
   - 写入或更新 Claude hook 配置
   - 使用 `UserPromptSubmit` 捕获 CCWhat command
   - block 原 prompt 并调用 CCWhat controller

6. `ccwhat -- claude` wiring
   - 启动前 ensure integration
   - 创建 run
   - 启动 controller/proxy/viewer
   - 注入 run env
   - Agent 退出时处理未完成 task

### 验收标准

- 用户通过 `ccwhat -- claude` 启动 Claude Code。
- Claude 原生 slash 菜单中能看到 CCWhat 命令。
- 选择 `/ccwhat:start` 后，本地生成 active task。
- 选择 `/ccwhat:finish` 后，task finalized。
- Dataset staging 中存在：

```text
~/.ccwhat/runtime-runs/claude/<run-id>/
  run.json
  tasks/task-001/
    task.json
    control_events.jsonl
    repo_before.tar.gz
    repo_after.tar.gz
    diff.patch
```

- `control_events.jsonl` 标记：

```json
{
  "model_visible": false,
  "confidence": "high"
}
```

### 不在本 change 中做

- Codex/OpenCode 正式适配
- 自动归因诊断
- Dataset v2 最终 schema validator
- Viewer 控制按钮
- Natural language skill 触发
- Task merge/split UI

### 需要提前决策

1. 如果 Claude Code 不支持 `/ccwhat:start` 这种冒号命名，是否接受降级为 `/ccwhat-start`？

推荐：接受。

2. 第一版是否只支持 git repo？

推荐：是。非 git workspace 明确报错，避免伪造 diff。

3. 控制通道是否使用 localhost HTTP？

推荐：是。比 Unix socket 更容易被不同 Agent hook/plugin 调用；端口自动分配且只绑定 `127.0.0.1`。

---

## Plan 2: Multi-Agent Slash Integration

Plan 2 不再把 Codex 和 OpenCode 混进一个大 change。原因是两者确定性不同：

```text
Codex:
  已有官方 UserPromptSubmit hook，可做原生菜单 + 本地 controller + block prompt 的强证据路径。

OpenCode:
  custom command 默认是 prompt-based。
  项目级 plugin 可在 command.execute.before 调用本地 controller，并清空 command parts。
  仍需确认清空 parts 后是否完全不会触发空模型请求。
```

因此 Plan 2 的执行顺序是：

1. 先做 Codex 正式竖切。
2. 再做 OpenCode command/plugin MVP。
3. 抓包确认 OpenCode command 清空 parts 后的模型可见性，并据此提升或保留 confidence。

这样可以尽快把 OpenCode 接入 runtime Dataset，同时把模型可见性作为独立验收项处理。

### Change 2: `add-codex-runtime-slash-integration`

目标：把 Plan 1 的 runtime recording 机制推广到 Codex，达到与 Claude Code 相同的强证据标准。

### 范围

这个 change 不重新设计 runtime recording，而是实现 Codex 的原生菜单注册、提交前 hook block 和 `ccwhat -- codex` runtime wiring。

```text
ccwhat -- codex
  -> 创建 runtime run
  -> 自动分配 proxy/viewer/control 端口
  -> 安装或检查 Codex CCWhat prompt/skill + hook
  -> 原生 slash 菜单出现 CCWhat 命令
  -> /ccwhat:start 触发 marker prompt
  -> Codex UserPromptSubmit hook 捕获 marker
  -> 调用 CCWhat runtime controller
  -> block prompt，不发送模型
  -> 生成 task staging
```

### 主要任务

1. Codex command registration
   - 写入 CCWhat 管理的 Codex prompt/skill 文件
   - 菜单中至少出现 start、finish
   - 优先 `/ccwhat:start`、`/ccwhat:finish`
   - 如 Codex 命名限制不支持冒号，降级为 `/ccwhat-start`、`/ccwhat-finish`

2. Codex hook installation
   - 写入或更新 Codex `UserPromptSubmit` hook
   - hook 检测 CCWhat marker
   - hook 调用 runtime controller
   - hook 返回 block，阻止 marker prompt 发给模型

3. Runtime evidence
   - `integration=codex_user_prompt_submit`
   - `model_visible=false`
   - `agent_log_visible=false` 或实测后的真实值
   - `confidence=high`

4. `ccwhat -- codex` wiring
   - 启动前 ensure Codex integration
   - 创建 run
   - 启动 controller/proxy/viewer
   - 注入 run env
   - Agent 退出时关闭 controller

5. Tests and manual acceptance
   - 文件生成/升级/冲突检测测试
   - hook -> controller -> staging 测试
   - CLI wiring 测试
   - 手工验收说明

### 验收标准

- 用户通过 `ccwhat -- codex` 启动 Codex。
- Codex 原生 slash 菜单中能看到 CCWhat start/finish。
- 选择 start 后，本地生成 active task。
- 选择 finish 后，task finalized。
- 最新 runtime run 下存在：

```text
~/.ccwhat/runtime-runs/codex/<run-id>/
  run.json
  tasks/task-001/
    task.json
    control_events.jsonl
    repo_before.tar.gz
    repo_after.tar.gz
    diff.patch
```

- `control_events.jsonl` 中 Codex 命令证据标记：

```json
{
  "integration": "codex_user_prompt_submit",
  "model_visible": false,
  "confidence": "high"
}
```

### 不在本 change 中做

- OpenCode 正式适配
- integration doctor/uninstall 完整 CLI
- Dataset v2 schema 升级
- 自动归因诊断
- Natural language skill 触发

### Change 3: `add-opencode-runtime-command-integration`

目标：把 OpenCode 接入 runtime recording MVP，先跑通用户手动 start/finish 切 Task 的完整链路。

### 范围

```text
ccwhat -- opencode
  -> 创建 runtime run
  -> 自动分配 proxy/viewer/control 端口
  -> 安装或检查项目级 OpenCode command + plugin
  -> /ccwhat:start 触发 OpenCode command
  -> command.execute.before plugin 调用 CCWhat runtime controller
  -> command prompt 进入模型，但只要求回复“收到”
  -> 生成 task staging
```

### 主要任务

1. OpenCode command registration
   - 写入 `.opencode/command/ccwhat:start.md`
   - 写入 `.opencode/command/ccwhat:finish.md`
   - 清理 CCWhat 早期生成的 `.opencode/command/ccwhat-start.md` 和 `.opencode/command/ccwhat-finish.md`
   - 命令不带参数，后端自动生成 `Task1`、`Task2`
   - 命令 prompt 明确说明这是 CCWhat 本地 task-boundary marker，模型只回复“收到”

2. OpenCode plugin installation
   - 写入 `.opencode/plugin/ccwhat-runtime.js`
   - plugin 使用 `command.execute.before`
   - plugin 调用 runtime controller
   - plugin 不再声明可以阻止模型请求

3. Runtime evidence
   - `integration=opencode_command_execute_before`
   - `model_visible=true`
   - `agent_log_visible=true`
   - `confidence=medium`

4. `ccwhat -- opencode` wiring
   - 启动前 ensure OpenCode integration
   - 创建 run
   - 启动 controller/proxy/viewer
   - 注入 run env

### 验收标准

- 用户通过 `ccwhat -- opencode` 启动 OpenCode。
- OpenCode 原生 slash 菜单中能看到 `/ccwhat:start` 和 `/ccwhat:finish`。
- 选择 start 后，本地生成 active task。
- 选择 finish 后，task finalized。
- 最新 runtime run 下存在 `task.json`、`control_events.jsonl`、repo before/after snapshot 和 `diff.patch`。

### Change 4: `investigate-opencode-local-intercept`

目标：继续调研 OpenCode 是否存在真正的本地拦截能力，让 `/ccwhat:start`、`/ccwhat:finish` 完全不进入模型请求。

需要确认：

1. OpenCode 是否提供 cancel/prevent command prompt 的官方 API。
2. plugin 是否能替换 command prompt 为本地响应，且不触发模型请求。
3. 是否需要改用 PTY wrapper 或 OpenCode 数据库轮询兜底。
4. 如果找到真拦截路径，再把 `control_events.jsonl` 的 `model_visible`、`agent_log_visible`、`confidence` 调整为更强证据。

结论：

- 当前已知 OpenCode command prompt 会进入模型请求，本阶段接受 `model_visible=true` 的降级路径。
- 真拦截能力作为后续增强，不阻塞 OpenCode runtime MVP 跑通。

### 需要提前决策

1. Codex 如果自定义 prompt 被 block 后仍进入本地 transcript，是否接受？

推荐：接受，但 `agent_log_visible` 必须按实测结果标记。

2. OpenCode 如果无法 cancel prompt，是否允许第一版以 medium-confidence 降级上线？

推荐：允许，但必须在 `doctor` 和 Dataset evidence 中清楚标记。

3. Agent integration 默认写全局用户配置还是项目配置？

推荐：本阶段默认项目配置，减少修改用户全局 Agent 配置的风险；后续 doctor/install CLI 再支持全局安装。

4. integration 冲突时是否自动覆盖非 CCWhat 文件？

推荐：不覆盖。提示用户处理。

---

## Plan 3: Diagnosis-Ready Dataset and Attribution

Plan 3 是最终目标层。它分成两个 change：先稳定 Dataset 契约，再做自动归因诊断。

### Change 3: `promote-runtime-dataset-v2`

目标：把 runtime staging 升级为正式 diagnosis-ready Dataset 结构。

### 范围

将 Plan 1/2 的 staging 产物固化为稳定 Dataset：

```text
ccwhat-dataset/
  manifest.json
  raw/
  session/
  tasks/
    task-001/
      task.json
      task_trace.json
      repo_before.tar.gz
      repo_after.tar.gz
      diff.patch
      commands.jsonl
      test_outputs/
      control_events.jsonl
      diagnosis.json
  scores.jsonl
```

### 主要任务

1. Dataset v2 schema
   - manifest 记录 run、agent、workspace、evidence summary
   - task.json 记录 evidence_availability、evidence_source、confidence
   - task_trace.json 聚合 runtime events

2. Runtime staging finalizer
   - Agent 退出或用户手动 finalize 时生成正式 Dataset
   - partial task 可保留为 incomplete

3. Validator
   - 校验 v2 结构
   - 校验 task paths
   - 校验证据字段
   - 校验 diff/snapshot 存在性

4. Registry and export
   - 保存到 `~/.ccwhat/datasets/<dataset-id>/`
   - 支持下载 tar.gz
   - 保留 v1 validator 兼容

### 验收标准

- 从一个 runtime run 能 finalize 出 v2 Dataset。
- validator 能通过完整 Dataset。
- 缺失 snapshot、diff 或 evidence 字段时 validator 能报错或 warning。
- v1 Dataset 保存导出不被破坏。

### 不在本 change 中做

- 自动诊断模型或规则
- 诊断 UI
- 训练数据转换

### 需要提前决策

1. v2 schema 是否与 v1 并存？

推荐：并存。v1 保持当前任务导出能力，v2 专用于 runtime diagnosis。

2. partial task 是否进入正式 Dataset？

推荐：进入，但标记 `status=incomplete`，默认诊断可以跳过。

### Change 4: `add-auto-attribution-diagnosis`

目标：让 CCWhat 自动消费 diagnosis-ready Dataset，生成初版归因诊断结果。

### 范围

第一版自动归因不追求最终智能程度，先形成可迭代闭环：

```text
task_trace.json
repo_before/repo_after
diff.patch
commands/test outputs
errors/final claim
  -> diagnosis engine
  -> diagnosis.json
```

### 主要任务

1. Diagnosis input builder
   - 从 task 现场包构建诊断上下文
   - 控制上下文大小
   - 明确证据来源和缺失项

2. Rule-based first pass
   - 命令未运行
   - 测试失败
   - final claim 与证据矛盾
   - diff 为空但声称完成
   - 修改文件和读取文件不匹配

3. LLM-assisted attribution pass
   - 只消费 Dataset evidence
   - 输出结构化 diagnosis
   - 标注 confidence 和 evidence links

4. diagnosis.json schema
   - summary
   - likely_root_causes
   - evidence
   - missing_evidence
   - confidence
   - recommended_next_steps

5. Basic viewer/report surface
   - 在 Dataset 或 Task 页面展示 diagnosis summary
   - 不做复杂 UI

### 验收标准

- 对一个 finalized task 能生成 `diagnosis.json`。
- 如果测试失败，诊断能引用 command/test output。
- 如果 evidence 缺失，诊断明确说明不能判断。
- 诊断结果不把 medium-confidence 或 model-visible boundary 当作 high-confidence 证据。

### 不在本 change 中做

- 训练数据转换
- SFT/DPO/RL 数据流水线
- 批量 benchmark
- 完整 evaluator 平台

### 需要提前决策

1. 自动归因是否可以调用模型？

推荐：可以，但必须保留 rule-based baseline，并在 diagnosis 中标记 `source=llm`。

2. LLM 诊断是否允许读取 repo snapshot 全量文件？

推荐：第一版不全量读取。只读取 diff、trace、命令输出和必要文件片段。

---

## 推荐执行顺序

```text
1. add-runtime-task-recording-mvp
2. productionize-agent-slash-integrations
3. promote-runtime-dataset-v2
4. add-auto-attribution-diagnosis
```

只有第一个 change 是立即要开始的。

如果第一个 change 发现 Claude Code 的原生菜单拦截不可行，应先回到 `TASK_AGENT_SLASH_COMMAND_INTEGRATION.md` 更新兼容性矩阵，再决定是否改用 Codex 作为 MVP agent。

## 当前需要用户拍板的决策

在创建第一个 OpenSpec change 前，需要确认：

1. MVP 首个 Agent 是否选择 Claude Code。
2. 如果冒号命名不被支持，是否接受 `/ccwhat-start` 降级。
3. 第一版是否只支持 git repo workspace。
4. 控制通道是否采用 localhost HTTP control port。
5. OpenCode 后续如果无法做到不发模型，是否接受 medium-confidence 降级。

推荐答案：

```text
1. 是，先选 Claude Code。
2. 是，接受命名降级。
3. 是，第一版只支持 git repo。
4. 是，第一版用 localhost HTTP control port。
5. 是，短期接受 OpenCode 降级，但必须显式标记。
```

## 与现有文档关系

本计划依赖以下设计文档：

- `docs/planning/task-dataset/integration/TASK_RUNTIME_RECORDING_INTERACTION.md`
- `docs/planning/task-dataset/integration/TASK_AGENT_SLASH_COMMAND_INTEGRATION.md`

本计划不是 OpenSpec change，不直接定义 SHALL 级需求。审阅通过后，再按 Plan 1 创建第一个 change：

```bash
openspec change add-runtime-task-recording-mvp
```
