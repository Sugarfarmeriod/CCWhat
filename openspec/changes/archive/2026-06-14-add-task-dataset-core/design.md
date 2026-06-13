## Context

当前 CCWhat 已有三类关键输入：

- agent adapter 能把 Claude Code / Codex / OpenCode session 转成 normalized events。
- `ccwhat/task_segments/` 能生成 `TaskSegmentationResult`，其中每个 `TaskSegment` 有 `task_id`、标题、类型、边界、evidence、final claim 等信息。
- 前端 Task Trace Overlay 已经能表达人工校正后的 task 边界，但本 change 不接 viewer 保存入口。

Dataset v1 的核心目标是把“已切分 Task + 对应执行过程”转换为稳定文件集合。这个核心层应独立于 viewer、HTTP API、本地 registry 和 tar.gz 下载，这样后续 `save-and-export-task-dataset-from-viewer` 只需要调用 builder / validator，而不是重新定义数据格式。

## Goals / Non-Goals

**Goals:**

- 定义 Dataset v1 文件契约：`manifest.json`、`dataset.jsonl`、`traces/*.json`、`scores.jsonl`。
- 提供 builder，把 normalized session 与 task segments / overlay-like task 边界转换成内存态 Dataset 文件集合。
- 提供 validator，校验目录或 tar 包中的 Dataset 结构、JSON / JSONL 格式、必填字段、计数和引用一致性。
- 提供最小 fixture，覆盖 Claude Code / Codex / OpenCode 三类 agent session 都可生成 Dataset。
- 提供核心测试，覆盖成功构建、边界裁剪、空 score 文件、缺失文件、坏 JSONL、trace 引用错误等行为。

**Non-Goals:**

- 不新增 viewer 入口、modal、HTTP API 或下载流程。
- 不写入 `~/.ccwhat/datasets/`，不生成 registry 记录。
- 不生成 `.tar.gz`；validator 只需要能读取已存在的目录或 tar 包以便后续复用。
- 不做 evaluator，不自动写入 score。
- 不做 agent-specific `changes` / `patches` evidence 抽取；本 change 中 trace 的 `changes` 和 `patches` 可以为空数组。
- 不要求 Dataset 能完整复现 repo 环境或包含 raw session / raw req-resp。

## Decisions

### Decision 1: 新增独立 `ccwhat/task_dataset/` 核心包

实现应新增独立核心包，例如：

```text
ccwhat/task_dataset/
  __init__.py
  models.py
  builder.py
  validator.py
```

原因：

- Dataset 是后续 evaluator、viewer 保存、离线分析共同依赖的边界对象，不应塞进 `viewer/server.py`。
- `task_segments` 负责识别边界，`task_dataset` 负责把边界固化为可交换数据资产，职责更清楚。

替代方案：直接在 viewer API 中拼 JSON 文件。放弃原因是会让数据契约依赖 UI 流程，后续 CLI / evaluator 复用成本高。

### Decision 2: builder 先输出内存态文件集合

builder 应返回可写入文件系统的内存态结构，例如 `DatasetBundle`：

```text
manifest: dict
dataset_rows: list[dict]
traces: dict[str, dict]
scores_rows: list[dict]  # v1 为空
```

同时提供序列化辅助，把 bundle 写成：

```text
manifest.json
dataset.jsonl
traces/<trace-id>.json
scores.jsonl
```

原因：

- 本 change 不负责 registry 写入或 viewer 下载，但后续 API 需要可直接复用序列化逻辑。
- 测试可以直接断言内存结构，也可以落临时目录后用 validator 验证。

替代方案：builder 直接写目录。放弃原因是会把生成逻辑和存储位置耦合起来，不利于后续 tar.gz 与测试复用。

### Decision 3: v1 trace 保留基础 evidence，延迟 agent-specific patch/diff

trace v1 必须包含：

- `events`
- `commands`
- `test_commands`
- `files.read`
- `files.changed`
- `changes`
- `patches`
- `errors`
- `final_claim`
- `repo_state`

其中 `changes` 和 `patches` 在本 change 可以为空数组。builder 可从 `TaskSegment.evidence` 和 task 边界内的 normalized events 填充 commands、test commands、files、errors、final claim。

原因：

- 后续 evaluator 需要一个稳定字段位，即使 evidence 抽取还没补齐。
- 三类 agent 的 patch/diff 语义不同，应单独 change 处理，避免 Dataset core 过早绑定具体日志细节。

替代方案：本 change 一并做 patch/diff 抽取。放弃原因是范围会跨 agent adapter 和日志细节，风险与测试矩阵明显扩大。

### Decision 4: validator 聚焦结构和引用，不做语义评分

validator 应检查：

- 必需文件存在：`manifest.json`、`dataset.jsonl`、`scores.jsonl`、`traces/`。
- JSON / JSONL 可解析。
- `manifest.schema_version == "ccwhat-dataset-v1"`。
- `manifest.counts.dataset_items` 与 `dataset.jsonl` 行数一致。
- `manifest.counts.traces` 与实际 trace 数一致。
- 每个 dataset row 的 `metadata.trace_path` 指向存在的 trace。
- trace 的 `task_id` 与 dataset row `id` 一致。
- `scores.jsonl` 第一版可以为空；非空时必须是合法 JSONL。

validator 不判断 task 是否成功、不运行测试、不检查 patch 是否真实可应用。

### Decision 5: 路径与 repo 状态允许缺省，但字段必须稳定

`repo_state.base_commit`、`repo_state.head_commit`、`input.base_commit` 取不到时允许为 `null`；`project_dir` / `cwd` 第一版按现有 session 信息原样保留。后续如果需要脱敏，可另开 change 或在 viewer save/export 层增加选项。

原因：

- 不同 agent session 未必都有 git 信息。
- Dataset v1 的关键价值是稳定引用和 evidence，不应因缺少 git 信息阻止生成。

## Risks / Trade-offs

- [Risk] Dataset v1 暴露本机 `project_dir` / `cwd`。→ Mitigation: 在用户审阅问题中确认是否接受；本 change 先按计划保留，后续可加脱敏策略。
- [Risk] overlay-like task 边界与 `TaskSegment` 字段不完全一致。→ Mitigation: builder 设计输入适配层，优先支持 `TaskSegmentationResult`，并为 overlay payload 预留转换函数，但不接 viewer。
- [Risk] normalized events 的 event id 排序规则跨 agent 不完全一致。→ Mitigation: builder 以输入 events 的顺序为准，按 start/end event id 截取闭区间；找不到边界时 validator 或 builder 返回清晰错误。
- [Risk] 过早细化 JSON schema 可能限制后续 evaluator。→ Mitigation: v1 固定核心字段，允许对象保留 `metadata` 扩展；新增 evaluator 字段放入后续 change。
- [Risk] validator 同时支持目录和 tar 包会增加一点复杂度。→ Mitigation: 读取层统一抽象成 path-to-bytes 映射，schema 校验逻辑共用。

## Migration Plan

这是新增能力，不需要迁移既有数据。

实施完成后，后续 change 可以按以下方式接入：

1. `extract-dataset-change-evidence` 扩展 trace 的 `changes` / `patches` 填充逻辑。
2. `save-and-export-task-dataset-from-viewer` 调用 builder 生成 bundle，写入 `~/.ccwhat/datasets/<dataset-id>/`，再调用 validator 做保存后校验。

## Open Questions

- 是否接受 Dataset v1 默认保留 `project_dir` / `cwd` 本机路径，还是需要在第一个实现 change 中默认脱敏？
- validator 是否需要暴露 CLI 命令，还是第一阶段只作为 Python API 和测试工具存在？
- overlay payload 到 Dataset 的转换是否必须在本 change 完成，还是只要求 `TaskSegmentationResult` 输入，overlay 在 viewer save/export change 中适配？
