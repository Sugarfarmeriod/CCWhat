# 可复用 Agent Loop 工作流模板

这份文档用于把“主控 Agent + 多角色子 Agent + heartbeat 轮询”的开发流程迁移到其他 Codex 或 Coding Agent 项目。

## 目标

用户只和一个主控 Agent 对话。主控 Agent 负责调度 Planner、Executor、Reviewer 等子 Agent，并在需要用户审阅或手测时通知用户。

核心目标：

- 用户不再手动切换多个线程当“胶水”。
- 子 Agent 工作期间，主控 Agent 通过 heartbeat 自动轮询进度。
- 需要用户决策时暂停 heartbeat，节省 token。
- 所有流程状态写入项目文件，避免依赖对话记忆。

## 需要创建的东西

### 1. 主控线程

创建一个主线程，命名建议：

```text
Orchestrator - <Project Name> Agent Loop
```

用户只和这个线程交互。

主控职责：

- 读取 `.agent-loop/ORCHESTRATOR.md`
- 读取 `.agent-loop/state.md`
- 创建或调度子 Agent
- 根据阶段更新 heartbeat 间隔
- 汇总子 Agent 结果给用户
- 在人工关卡暂停 heartbeat

### 2. 三个角色线程

建议创建三个真实线程：

```text
Planner - <Project Name> Agent Loop
Executor - <Project Name> Agent Loop
Reviewer - <Project Name> Agent Loop
```

如果项目是严格顺序执行，可以让三者都操作当前文件夹。

如果希望隔离实现风险，可以让 Executor 使用独立 git worktree。

### 3. `.agent-loop/` 目录

在项目根目录创建：

```text
.agent-loop/
  ORCHESTRATOR.md
  state.md
```

`.agent-loop` 不是 Codex 自动生成目录，也不是系统配置。它是项目自定义的 Agent Loop 协议目录。

## 角色定义

### Orchestrator

主控 Agent。只和用户直接沟通。

职责：

- 派 Planner 写计划或 Spec。
- 派 Executor 实现。
- 派 Reviewer review。
- 汇总结果给用户。
- 管理 heartbeat。
- 更新 `.agent-loop/state.md`。
- 在用户审阅、手测、确认时暂停 heartbeat。
- 手测通过后派 Executor 做归档、归档 commit 和 push。

### Planner

规划和 Spec Agent。

职责：

- 写总体计划。
- 写 OpenSpec change。
- 写 proposal/design/tasks/spec delta。
- 不实现业务代码。
- 不 commit。
- 写完后停下，等待 Orchestrator 汇总给用户审阅。

### Executor

实现 Agent。

职责：

- 只根据已通过的 Spec/tasks 实现。
- 不重新规划。
- 不主动改 Spec。
- 每次实现后运行测试。
- 每次实现后立即 commit。
- 手测通过后，负责归档 OpenSpec change。
- 归档后负责再次 commit。
- 归档 commit 后负责 push。

### Reviewer

审查和反馈沉淀 Agent。

职责：

- Review Executor 的实现 commit 是否符合 Spec。
- 找阻塞问题、行为偏差、测试缺口、回归风险。
- Review 不通过时，把问题沉淀回 Spec/tasks。
- 用户手测失败时，根据反馈更新 Spec/tasks。
- 不直接实现业务代码，除非 Orchestrator 明确授权。

## 标准流程

```text
Planner 写 Spec
  ↓
用户审阅 Spec
  ↓
Executor 实现并 commit
  ↓
Reviewer review
  ↓
如果 review 不通过：
    Reviewer 更新 Spec/tasks
    Executor 修复并 commit
    Reviewer 再 review
  ↓
如果 review 通过：
    用户手测
  ↓
如果手测不通过：
    Reviewer 根据反馈更新 Spec/tasks
    Executor 修复并 commit
    Reviewer 再 review
    用户再手测
  ↓
如果手测通过：
    Orchestrator 派 Executor 归档 change
    Executor commit
    Executor push
    Orchestrator 汇总结果
    进入下一个 change
```

## Heartbeat 设置

Heartbeat 只用于“AI 等 AI”的阶段，不用于“AI 等人”的阶段。

Codex heartbeat 不支持一个 automation 内部原生按条件动态调度。动态效果由 Orchestrator 在阶段切换时主动更新同一个 heartbeat 的真实配置实现。

建议只创建一个 heartbeat：

```text
<Project Name> Agent Loop heartbeat
```

heartbeat prompt 应要求：

```text
每次执行前先读取：
1. <project>/.agent-loop/ORCHESTRATOR.md
2. <project>/.agent-loop/state.md

不要依赖对话记忆。
只检查 state 中的 active_agent。
如果 active_agent 未完成，简短静默状态。
如果 active_agent 完成，汇总结果、更新 state，并推进下一阶段。
如果进入 waiting_human_*，暂停 heartbeat。
```

## 动态间隔规则

阶段切换时，Orchestrator 必须更新 heartbeat：

```text
Planner 阶段：
  status = ACTIVE
  RRULE = FREQ=MINUTELY;INTERVAL=5

Executor 阶段：
  status = ACTIVE
  RRULE = FREQ=MINUTELY;INTERVAL=20

Reviewer 阶段：
  status = ACTIVE
  RRULE = FREQ=MINUTELY;INTERVAL=10

等待用户阶段：
  status = PAUSED
```

推荐阶段名：

```text
planner_reviewing_plan
planner_writing_spec
waiting_human_plan_review
waiting_human_spec_review
executor_implementing
implementation_committed
reviewer_reviewing
reviewer_updating_spec
waiting_human_manual_test
executor_fixing
executor_archiving
archive_committed
pushing_change
ready_for_next_change
```

## `state.md` 模板

```markdown
# <Project Name> Agent Loop 状态

## 角色线程

- 主控 Orchestrator：当前线程
- Planner：<planner-thread-id>
- Executor：<executor-thread-id>
- Reviewer：<reviewer-thread-id>

## 当前状态

- 阶段：<phase>
- 当前 change：<change-id-or-none>
- 当前活跃角色：<orchestrator|planner|executor|reviewer>
- 是否等待人工：<true|false>
- heartbeat id：<automation-id>
- heartbeat 当前间隔：<paused|5 分钟|10 分钟|20 分钟>

## 当前待办

- <next-action>
```

## `ORCHESTRATOR.md` 必须包含的规则

```text
每次用户消息或 heartbeat 唤醒后，先读 ORCHESTRATOR.md 和 state.md。
不要依赖对话记忆。

派 Planner 时：
  更新 state 为 planner_writing_spec
  active_agent=planner
  awaiting_human=false
  heartbeat=ACTIVE, 5 分钟

派 Executor 时：
  更新 state 为 executor_implementing
  active_agent=executor
  awaiting_human=false
  heartbeat=ACTIVE, 20 分钟

派 Executor 归档时：
  更新 state 为 executor_archiving
  active_agent=executor
  awaiting_human=false
  heartbeat=ACTIVE, 20 分钟
  Executor 负责归档、归档 commit、push

派 Reviewer 时：
  更新 state 为 reviewer_reviewing
  active_agent=reviewer
  awaiting_human=false
  heartbeat=ACTIVE, 10 分钟

等待用户时：
  更新 state 为 waiting_human_*
  active_agent=orchestrator
  awaiting_human=true
  heartbeat=PAUSED
```

## 最小启动步骤

1. 在项目里创建 `.agent-loop/ORCHESTRATOR.md` 和 `.agent-loop/state.md`。
2. 创建或指定 Orchestrator 主线程。
3. 创建 Planner、Executor、Reviewer 三个线程。
4. 把三个线程 ID 写入 `state.md` 和 `ORCHESTRATOR.md`。
5. 创建一个 heartbeat automation，目标指向 Orchestrator。
6. heartbeat 初始状态按当前阶段设置：
   - 如果 Planner 正在工作，设为 5 分钟 ACTIVE。
   - 如果 Executor 正在工作，设为 20 分钟 ACTIVE。
   - 如果 Reviewer 正在工作，设为 10 分钟 ACTIVE。
   - 如果等用户，设为 PAUSED。
7. 以后用户只和 Orchestrator 对话。

## 给新 Agent 的启动提示词

```text
你是这个项目的 Orchestrator。

请先读取：
- .agent-loop/ORCHESTRATOR.md
- .agent-loop/state.md

之后严格按这两个文件推进 Agent Loop。

不要依赖对话记忆。
不要让我手动切换 Planner、Executor、Reviewer。
你负责调度子 Agent、读取结果、更新 heartbeat、暂停人工关卡。

当你派出：
- Planner：heartbeat 改为 5 分钟
- Executor：heartbeat 改为 20 分钟
- Reviewer：heartbeat 改为 10 分钟
- 等我审阅/手测：heartbeat 暂停

所有汇报保持简洁。
```

## 注意事项

- `.agent-loop` 是自定义协议目录，不是 Codex 官方自动生成目录。
- heartbeat 的动态间隔不是原生条件调度，而是 Orchestrator 阶段切换时调用工具更新 automation。
- 如果当前 Agent 平台没有 heartbeat/automation 功能，可以退化为用户手动发“检查进度”。
- 如果当前 Agent 平台不能创建或读写其他线程，就只能半自动，无法真正让 Orchestrator 代替用户当胶水。
- 如果项目会并行修改代码，Executor 应使用独立 worktree 或分支。
- 如果项目严格顺序执行，所有角色使用当前文件夹即可。
