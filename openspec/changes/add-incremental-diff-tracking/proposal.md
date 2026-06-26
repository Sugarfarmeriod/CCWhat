## Why

Change 6 移除了 repo_before/after.tar.gz 和 diff.patch，解决了大型仓库无法打包的问题，但也丢失了代码变更的客观证据。我们需要一种不污染主 git 工作区、能追踪每次文件修改、且可关联到具体 tool_call 的增量 diff 方案。

## What Changes

- **新增 `CCWhatIndex` 类**: 封装 GIT_INDEX_FILE 操作，提供隔离的 git staging area
- **新增增量 diff 追踪**: 每次文件修改后生成 diff 片段，带 step 元数据
- **新增 diff.patch 格式**: 带注释头的分步 diff，可追溯每个 tool_call
- **新增 StepDiff 数据结构**: 记录 step_index、timestamp、diff、files_changed
- **更新 `TaskStaging`**: 集成 `CCWhatIndex`，支持 `record_step()` 方法
- **更新 task.json**: 恢复 `paths.diff` 和 `evidence_availability.diff`，指向增量 diff.patch

## Capabilities

### New Capabilities
- `incremental-diff-index`: GIT_INDEX_FILE 封装，提供隔离的 git staging area
- `incremental-diff-tracking`: 增量 diff 生成和存储，关联 tool_call

### Modified Capabilities
- `runtime-task-staging`: 新增 `CCWhatIndex` 集成和 `record_step()` 方法，恢复 diff 相关字段

## Impact

- **ccwhat/runtime/index.py**: 新增 `CCWhatIndex` 类（初始化、add、remove、diff、diff_step）
- **ccwhat/runtime/staging.py**: 集成 `CCWhatIndex`，新增 `record_step()`，恢复 diff 字段
- **ccwhat/runtime/models.py**: 新增 `StepDiff` dataclass
- **Task 目录结构**: 新增 `diff.patch`，格式为带 step 注释头的统一 diff
