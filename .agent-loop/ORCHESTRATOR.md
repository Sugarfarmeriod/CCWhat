# CCWhat Agent Loop 主控协议

这个文件是 Orchestrator 的持久工作协议。每次用户消息或 heartbeat 唤醒后，主控 Agent 都应先读取：

1. `.agent-loop/ORCHESTRATOR.md`
2. `.agent-loop/state.md`

主控 Agent 不依赖记忆推进流程，而是依赖这两个文件。

## 核心原则

- 用户只和 Orchestrator 对话。
- Planner、Executor、Reviewer 是由 Orchestrator 调度的子线程。
- 所有角色线程当前都操作同一个本地项目目录。
- 同一时间只允许一个角色修改文件。
- 需要用户审阅、手测或确认时，必须暂停 heartbeat。
- heartbeat 只用于“AI 等 AI”的阶段，不用于“AI 等人”的阶段。

## 线程 ID

- Planner：019ec17c-f36b-71c3-912d-2d82e55a610d
- Executor：019ec17d-37cc-7662-84d6-46f31fbe3755
- Reviewer：019ec17d-389f-7043-bf37-720027920f62
- Heartbeat automation：ccwhat-agent-loop-heartbeat

## 标准流程

1. Planner 写 OpenSpec change。
2. 用户审阅 Spec。
3. Executor 按已通过的 Spec 实现。
4. Executor 每次实现完成后立即 commit。
5. Reviewer review Executor 的实现 commit。
6. Review 不通过时，Reviewer 更新 spec/tasks，Executor 继续修复并再次 commit。
7. Review 通过后，用户手动测试。
8. 手测不通过时，Reviewer 根据用户反馈更新 spec/tasks，Executor 修复并再次 commit。
9. 手测通过后，Orchestrator 派 Executor 归档 change。
10. Executor 为归档/收尾再次 commit。
11. Executor push 到远端。
12. Orchestrator 读取 Executor 结果并询问是否进入下一个 change。

## Heartbeat 动态间隔规则

Codex heartbeat 不支持在一个 automation 中原生按条件动态调度。动态效果由 Orchestrator 在阶段切换时调用 `automation_update` 修改同一个 heartbeat 的真实配置来实现。

### 派 Planner 时

- state 阶段设为：`planner_writing_spec` 或 `planner_reviewing_plan`
- 当前活跃角色设为：`planner`
- 是否等待人工设为：`false`
- heartbeat 状态设为：`ACTIVE`
- heartbeat RRULE 设为：`FREQ=MINUTELY;INTERVAL=5`
- state 中 heartbeat 当前间隔写为：`5 分钟`

### 派 Executor 实现或修复时

- state 阶段设为：`executor_implementing` 或 `executor_fixing`
- 当前活跃角色设为：`executor`
- 是否等待人工设为：`false`
- heartbeat 状态设为：`ACTIVE`
- heartbeat RRULE 设为：`FREQ=MINUTELY;INTERVAL=20`
- state 中 heartbeat 当前间隔写为：`20 分钟`

### 派 Executor 归档时

- state 阶段设为：`executor_archiving`
- 当前活跃角色设为：`executor`
- 是否等待人工设为：`false`
- heartbeat 状态设为：`ACTIVE`
- heartbeat RRULE 设为：`FREQ=MINUTELY;INTERVAL=20`
- state 中 heartbeat 当前间隔写为：`20 分钟`
- Executor 负责归档 OpenSpec change、执行归档 commit、push 到远端，并向 Orchestrator 汇报 commit hash、push 结果和遗留问题。

### 派 Reviewer 时

- state 阶段设为：`reviewer_reviewing` 或 `reviewer_updating_spec`
- 当前活跃角色设为：`reviewer`
- 是否等待人工设为：`false`
- heartbeat 状态设为：`ACTIVE`
- heartbeat RRULE 设为：`FREQ=MINUTELY;INTERVAL=10`
- state 中 heartbeat 当前间隔写为：`10 分钟`

### 等待用户时

- state 阶段设为对应的 `waiting_human_*`
- 当前活跃角色设为：`orchestrator`
- 是否等待人工设为：`true`
- heartbeat 状态设为：`PAUSED`
- state 中 heartbeat 当前间隔写为：`paused`

## Heartbeat 唤醒时的行为

1. 读取本文件和 `.agent-loop/state.md`。
2. 如果当前阶段是 `waiting_human_*`，或“是否等待人工”为 `true`，立即确认 heartbeat 已暂停，然后不做推进。
3. 否则只读取当前活跃角色线程，不读取所有线程。
4. 如果活跃角色还在运行，只输出简短静默状态。
5. 如果活跃角色完成：
   - 汇总结果。
   - 更新 `.agent-loop/state.md`。
   - 如果下一步仍是子 Agent 工作，派发下一角色并更新 heartbeat 间隔。
   - 如果下一步需要用户审阅或手测，暂停 heartbeat 并通知用户。

## 当前人工关卡

- 计划审阅：用户通过后，派 Planner 写第一个 change spec。
- Spec 审阅：用户通过后，派 Executor 实现。
- 手动测试：用户通过后，派 Executor 归档 change、commit、push；用户不通过时，派 Reviewer 更新 spec/tasks。
