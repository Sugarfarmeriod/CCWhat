## Why

`add-task-dataset-core` 已经建立 Dataset v1 的基础文件契约和 builder，但 trace 中的 `changes` / `patches` 仍为空数组。为了让 Dataset 成为后续 evaluator、失败归因和离线分析的有效输入，需要把 Claude Code / OpenCode / Codex session 中已经存在的文件改动证据统一抽取进 Dataset trace。

本 change 只补齐“可证明的改动证据”，不通过 LLM 猜测 patch，也不读取当前 repo 现场生成 diff。

## What Changes

- 为 Dataset trace 定义统一的 `changes` evidence 结构，用来记录 edit、write、patch、command、git_diff 等改动证据。
- 为 Dataset trace 定义统一的 `patches` evidence 结构，只保存原生日志中存在或可确定性派生的 diff / patch。
- 扩展 Dataset builder，在每个 task 的 event 边界内抽取 `changes` 和 `patches`。
- 支持 Claude Code：
  - 抽取 `Edit.old_string/new_string`、`MultiEdit` 等可证明 edit evidence。
  - 抽取 `Write.content` 作为 write evidence。
  - 抽取 `Bash.command` 作为 command evidence；没有 diff 时不生成 patch。
- 支持 OpenCode：
  - 抽取 `edit.oldString/newString`。
  - 抽取 `metadata.diff` / `metadata.filediff`。
  - 抽取 `apply_patch.patchText` 或等价 patch part。
- 支持 Codex：
  - 抽取 `patch_apply_end` 事件中的 `changes[path].unified_diff`。
  - 对新增文件 `content` 记录 change evidence，并在确有 diff 字段时记录 patch evidence。
- 新增 fixtures 和测试，覆盖三类 agent 的核心 evidence 字段、confidence、format、task 边界过滤和禁止猜测 patch 的行为。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `task-dataset-core`: 扩展 Dataset trace 的 `changes` / `patches` 语义，要求 builder 从 Claude Code / OpenCode / Codex session events 中抽取可证明的改动证据。

## Impact

- 预计修改 `ccwhat/task_dataset/` builder / models，新增或扩展 evidence extraction helper。
- 可能需要调整 normalized event 的 `raw_ref` / `metadata` 保留策略，确保 builder 能读取原始 tool input 或 adapter event 中的 patch/diff 字段。
- 新增三类 agent 的 change evidence fixture 与单元测试。
- 不新增 viewer 入口、HTTP API、registry、tar.gz 下载入口或 evaluator。
- 不做 repo 现场 `git diff`，不读取工作区当前文件推导 patch，不通过 LLM 猜测缺失 patch。
