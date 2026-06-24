## Context

`ccwhat -- claude` 运行时，proxy（mitmproxy）持续在磁盘上追加 session JSONL 日志，记录 Agent 的全部 API 交互。同时，`RuntimeController` 以 `/ccwhat:start` / `/ccwhat:finish` 作为任务边界的锚点，写入带时间戳的 `control_events.jsonl`。

两份数据同时存在，但彼此没有连接：
- `control_events.jsonl`：知道边界时间戳，不知道 Agent 行为
- session JSONL：知道 Agent 行为，不知道哪段属于哪个 task

`task_trace.json` 的目标就是把这两份数据合并，在 `finish` 时按时间窗口切出属于本次 task 的那段 session 日志，提取结构化字段，写进 task 目录。

## Goals / Non-Goals

**Goals:**
- `finish_task()` 结束时，从 session JSONL 按 `started_at`/`finished_at` 时间窗口切出任务片段
- 复用 `extract_evidence` 和 `extract_change_evidence` 提取 commands、files、changes、errors、final_claim 等字段
- 将提取结果写成 `task_trace.json`，结构与 Dataset v1 的 trace 对齐
- `task.json` 补充 `instruction`、`success_criteria`、`expected_tests`
- `evidence_availability` 新增 `task_trace` 标志位

**Non-Goals:**
- 不修改 Dataset v1 导出路径和格式
- 不做实时流式写入（只在 finish 时一次性提取）
- 不处理 session JSONL 不存在的情况（降级为 `task_trace: false`，不报错）
- 不跨 run 聚合多个 session

## Decisions

### 决策 1：提取时机选在 `finish` 而非实时

**选择**：`finish_task()` 时一次性提取，不在 start/运行期间做流式切割。

**原因**：session JSONL 是追加写入的，只有 finish 时才知道任务边界的结束时间。实时切割需要 inotify 或轮询，复杂度高且收益低。

### 决策 2：复用已有的 extract_evidence / extract_change_evidence

**选择**：从 `ccwhat.task_segments.evidence` 和 `ccwhat.task_dataset.change_evidence` 直接复用。

**原因**：这两个函数已经在 Dataset v1 路径上被充分测试，支持 Claude/OpenCode/Codex 三种 agent 的事件格式。重新实现会引入重复逻辑和新的 bug 风险。

**替代方案**：新写一个专用提取器 → 否决，代码重复，维护成本高。

### 决策 3：session 日志路径从 run.json 推导

**选择**：从 `run.proxy` 端口推导 session log 目录（`~/.ccwhat/logs/<session_id>.jsonl` 或 proxy output 目录），而不是在 run.json 里新增字段。

**原因**：proxy output 目录已经由 `--output` 参数控制，run.json 里有足够信息（workspace、proxy port）定位到对应 session 文件。

### 决策 4：时间窗口匹配策略

**选择**：以 `control_events.jsonl` 中 start event 的 `timestamp` 为下界，finish event 的 `timestamp` 为上界，过滤 session JSONL 中每条事件的 `timestamp`。

**原因**：session JSONL 的每条 NormalizedEvent 都有 `timestamp`。时间窗口是目前最简单可靠的匹配方式，不需要在 session 日志里注入 run_id。

**风险**：时钟偏差（edge case）→ 上下界各留 1 秒 buffer。

## Risks / Trade-offs

**[Risk] session 日志文件找不到**
→ 降级处理：`evidence_availability.task_trace = false`，不报错，不中断 finish 流程。

**[Risk] 时间窗口内有其他 session 的事件混入**
→ 当前阶段接受。`ccwhat -- claude` 是单 agent 单 session，多 session 并发是极端场景，后续再加 session_id 过滤。

**[Risk] extract_evidence 依赖 NormalizedEvent 格式，日志格式变化会静默失败**
→ 缓解：task_trace.json 写入后校验核心字段是否为空，如果全空记录 warning。

**[Risk] finish 时提取耗时过长（大 repo + 大 session 日志）**
→ 缓解：提取在 finish 的同步路径上，目前接受。后续可异步化，但第一版不做。

## Open Questions

1. session JSONL 的具体路径约定是否已固定？需确认 `--output` 目录下的文件命名规则。
2. `instruction` 字段的提取优先级：control event 的 `raw_args` → session 首条 user_message → task title，顺序是否合理？
