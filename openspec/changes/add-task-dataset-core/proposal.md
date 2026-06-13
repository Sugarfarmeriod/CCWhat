## Why

CCWhat 已经能够从 Claude Code / Codex / OpenCode session 中切分 Task，并通过 Task Trace Overlay 做人工校正；下一步需要把这些 Task 固化为稳定、可校验、可被后续 evaluator 和离线分析消费的数据资产。

本 change 先建立 Dataset v1 的核心契约、builder、validator、fixtures 和核心测试，为后续 viewer 保存/下载与 agent-specific change evidence 抽取提供可靠底座。

## What Changes

- 新增 Task Dataset v1 数据契约，固定 `manifest.json`、`dataset.jsonl`、`traces/*.json`、`scores.jsonl` 四类输出。
- 新增 Dataset builder，从 normalized session 与 task segments / active overlay 构建内存态 Dataset 文件集合。
- 新增 Dataset validator，校验目录或 tar 包内的必需文件、JSON / JSONL 格式、基础 schema、计数一致性和 task-to-trace 引用。
- 新增覆盖 Claude Code / Codex / OpenCode 的最小 fixture，用于确认三类 agent session 都能生成 Dataset。
- 新增核心测试，覆盖 schema、builder、validator、边界裁剪和错误提示。
- 第一版 trace 只要求基础执行证据：`events`、`commands`、`test_commands`、`files`、`errors`、`final_claim`、`repo_state`，并保留空的 `changes` / `patches` 数组。

## Capabilities

### New Capabilities

- `task-dataset-core`: 定义 Task Dataset v1 核心数据契约，并要求系统能从已切分 Task 构建和校验 Dataset 文件集合。

### Modified Capabilities

- 无。

## Impact

- 预计新增后端核心模块，例如 `ccwhat/task_dataset/` 或现有包内同等职责目录。
- 预计新增 Dataset fixture 与单元测试。
- 预计新增 validator 入口，供测试、后续 API 和后续 tar.gz 导出复用。
- 不新增 viewer 入口、不新增 HTTP API、不写入 `~/.ccwhat/datasets/`、不生成 `.tar.gz`、不做 evaluator。
- 不解析 agent-specific `changes` / `patches` evidence；该能力留给后续 `extract-dataset-change-evidence` change。
