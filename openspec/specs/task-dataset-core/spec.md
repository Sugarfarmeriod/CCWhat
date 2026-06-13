## Purpose

定义 Task Dataset v1 的后端核心数据契约、构建器和校验器，使 CCWhat 可以从已切分的 coding task 生成稳定、可保存、可导出、可复用的数据资产。

## Requirements

### Requirement: Dataset v1 文件契约
Task Dataset Core SHALL 定义 `ccwhat-dataset-v1` 文件集合，包含 `manifest.json`、`dataset.jsonl`、`traces/*.json` 和 `scores.jsonl`。

#### Scenario: 生成必需文件集合
- **WHEN** 系统从已切分 Task 构建 Dataset
- **THEN** 输出 SHALL 包含 `manifest.json`
- **AND** 输出 SHALL 包含 `dataset.jsonl`
- **AND** 输出 SHALL 包含 `scores.jsonl`
- **AND** 输出 SHALL 包含 `traces/` 目录下每个 task 对应的 trace JSON

#### Scenario: manifest 描述数据包
- **WHEN** Dataset 包含 N 个 task
- **THEN** `manifest.json` SHALL 包含 `schema_version` 且值为 `ccwhat-dataset-v1`
- **AND** `manifest.json` SHALL 包含 `created_at`
- **AND** `manifest.json` SHALL 包含 `tool` 且值为 `ccwhat`
- **AND** `manifest.json` SHALL 包含 session 信息
- **AND** `manifest.json` SHALL 记录 `counts.dataset_items`
- **AND** `manifest.json` SHALL 记录 `counts.traces`
- **AND** `manifest.json` SHALL 记录 `counts.scores`

#### Scenario: dataset.jsonl 一行对应一个 task
- **WHEN** Dataset 包含一个 task
- **THEN** `dataset.jsonl` SHALL 为该 task 写入一行 JSON
- **AND** 该 JSON SHALL 包含 `id`
- **AND** 该 JSON SHALL 包含 `input.instruction`
- **AND** 该 JSON SHALL 包含 `input.repo`
- **AND** 该 JSON SHALL 包含 `input.base_commit`
- **AND** 该 JSON SHALL 包含 `expected.success_criteria`
- **AND** 该 JSON SHALL 包含 `expected.tests`
- **AND** 该 JSON SHALL 包含 `metadata.agent`
- **AND** 该 JSON SHALL 包含 `metadata.session_id`
- **AND** 该 JSON SHALL 包含 `metadata.task_source`
- **AND** 该 JSON SHALL 包含 `metadata.trace_id`
- **AND** 该 JSON SHALL 包含 `metadata.trace_path`
- **AND** 该 JSON SHALL 包含 task 边界 event id

#### Scenario: scores.jsonl 第一版为空
- **WHEN** Dataset v1 初次生成
- **THEN** `scores.jsonl` SHALL 存在
- **AND** `scores.jsonl` SHALL 允许为空文件
- **AND** 系统 SHALL NOT 自动写入 evaluator score

### Requirement: Dataset builder 构建核心内容
Task Dataset Core SHALL 提供 builder，从 normalized session events 与已切分 task 边界构建 Dataset v1 内容。

#### Scenario: 从 TaskSegmentationResult 构建 Dataset
- **WHEN** builder 接收 session metadata、normalized events 和 `TaskSegmentationResult`
- **THEN** builder SHALL 为每个 `TaskSegment` 生成一个 dataset item
- **AND** builder SHALL 为每个 `TaskSegment` 生成一个 trace JSON
- **AND** 每个 dataset item SHALL 通过 `metadata.trace_id` 和 `metadata.trace_path` 引用对应 trace
- **AND** 每个 trace SHALL 通过 `task_id` 引用对应 dataset item

#### Scenario: 按 task 边界裁剪 events
- **WHEN** task 指定 `start_event_id` 和 `end_event_id`
- **THEN** builder SHALL 将 trace `events` 限制在该闭区间内
- **AND** builder SHALL 保持 events 的原始输入顺序
- **AND** builder SHALL NOT 将其他 task 范围内的 events 写入该 trace

#### Scenario: task 没有 end_event_id
- **WHEN** task 的 `end_event_id` 为空
- **THEN** builder SHALL 将 trace `events` 从 `start_event_id` 开始延伸到 session events 末尾
- **AND** dataset item SHALL 保留 `metadata.end_event_id` 为 `null`

#### Scenario: 提取基础执行 evidence
- **WHEN** builder 生成 trace JSON
- **THEN** trace SHALL 包含 `events`
- **AND** trace SHALL 包含 `commands`
- **AND** trace SHALL 包含 `test_commands`
- **AND** trace SHALL 包含 `files.read`
- **AND** trace SHALL 包含 `files.changed`
- **AND** trace SHALL 包含 `errors`
- **AND** trace SHALL 包含 `final_claim`
- **AND** trace SHALL 包含 `repo_state`

#### Scenario: 预留 changes 和 patches 字段
- **WHEN** builder 生成 trace JSON
- **THEN** trace SHALL 包含 `changes` 数组
- **AND** trace SHALL 包含 `patches` 数组
- **AND** 本 change 中 builder MAY 将 `changes` 和 `patches` 置为空数组
- **AND** builder SHALL NOT 通过 LLM 猜测 patch 或 diff

### Requirement: Dataset validator 校验结构和引用
Task Dataset Core SHALL 提供 validator，校验 Dataset v1 目录或 tar 包的结构、格式和引用一致性。

#### Scenario: 校验合法目录
- **WHEN** validator 接收一个合法 Dataset v1 目录
- **THEN** validator SHALL 返回通过结果
- **AND** validator SHALL 报告 dataset item 数量、trace 数量和 score 数量

#### Scenario: 校验合法 tar 包
- **WHEN** validator 接收一个包含 Dataset v1 文件集合的 tar 包
- **THEN** validator SHALL 返回通过结果
- **AND** validator SHALL 使用与目录校验相同的结构和 schema 规则

#### Scenario: 缺少必需文件时报错
- **WHEN** Dataset 缺少 `manifest.json`、`dataset.jsonl`、`scores.jsonl` 或 `traces/`
- **THEN** validator SHALL 返回失败结果
- **AND** validator SHALL 报告缺失的路径

#### Scenario: JSON 或 JSONL 格式错误时报错
- **WHEN** Dataset 文件包含非法 JSON 或非法 JSONL 行
- **THEN** validator SHALL 返回失败结果
- **AND** validator SHALL 报告文件路径和行号或字段位置

#### Scenario: trace 引用不存在时报错
- **WHEN** `dataset.jsonl` 中的 `metadata.trace_path` 指向不存在的 trace
- **THEN** validator SHALL 返回失败结果
- **AND** validator SHALL 报告对应 dataset item id 和 trace path

#### Scenario: task 与 trace id 不一致时报错
- **WHEN** dataset item 的 `id` 与对应 trace 的 `task_id` 不一致
- **THEN** validator SHALL 返回失败结果
- **AND** validator SHALL 报告不一致的 dataset item id 和 trace path

#### Scenario: manifest counts 不一致时报错
- **WHEN** `manifest.json` 中的 `counts.dataset_items`、`counts.traces` 或 `counts.scores` 与实际文件内容不一致
- **THEN** validator SHALL 返回失败结果
- **AND** validator SHALL 报告不一致的 count 字段

### Requirement: 三类 agent fixture 覆盖
Task Dataset Core SHALL 提供最小 fixture 和测试，证明 Claude Code、Codex、OpenCode session 都可以生成 Dataset v1。

#### Scenario: Claude Code fixture 可生成 Dataset
- **WHEN** 测试使用 Claude Code fixture 构建 Dataset
- **THEN** builder SHALL 生成合法 Dataset v1
- **AND** validator SHALL 校验通过

#### Scenario: Codex fixture 可生成 Dataset
- **WHEN** 测试使用 Codex fixture 构建 Dataset
- **THEN** builder SHALL 生成合法 Dataset v1
- **AND** validator SHALL 校验通过

#### Scenario: OpenCode fixture 可生成 Dataset
- **WHEN** 测试使用 OpenCode fixture 构建 Dataset
- **THEN** builder SHALL 生成合法 Dataset v1
- **AND** validator SHALL 校验通过

### Requirement: Dataset core 不引入产品流程
Task Dataset Core SHALL 保持为后端核心能力，不直接引入 viewer 保存入口、registry 写入、下载流程或 evaluator。

#### Scenario: 不新增 viewer 保存入口
- **WHEN** 本 change 完成
- **THEN** 系统 SHALL NOT 新增 Tasks 页面“保存为 Dataset”按钮
- **AND** 系统 SHALL NOT 新增保存确认 modal

#### Scenario: 不新增保存和下载 API
- **WHEN** 本 change 完成
- **THEN** 系统 SHALL NOT 新增 `POST /api/save-task-dataset`
- **AND** 系统 SHALL NOT 写入 `~/.ccwhat/datasets/`
- **AND** 系统 SHALL NOT 生成 `dataset-*.tar.gz`

#### Scenario: 不做 evaluator
- **WHEN** Dataset v1 生成
- **THEN** 系统 SHALL NOT 自动评分
- **AND** 系统 SHALL NOT 写入非空 evaluator score
