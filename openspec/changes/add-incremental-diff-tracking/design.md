## Context

Change 6 已完成清理，移除了 repo_before/after.tar.gz、control_events.jsonl 和 note 命令。当前 task 目录结构：

```
tasks/task-001/
  task.json          # paths.diff = null, evidence_availability.diff = false
  task_trace.json    # 完整保留
```

本 change 引入增量 diff 追踪，解决以下问题：
1. 不污染主 git 工作区
2. 能追踪新增文件（即使未 git add）
3. 能关联每次变更到具体 tool_call

## Goals / Non-Goals

**Goals:**
- 实现 `CCWhatIndex` 类封装 GIT_INDEX_FILE
- 每次文件修改后生成 diff 片段
- diff.patch 格式带 step 注释头，可追溯 tool_call
- Task 完成时 `paths.diff` 指向 diff.patch
- 主 git 工作区完全不受影响

**Non-Goals:**
- 不实现 Hook 集成（阶段三）
- 不实现 ccwhat 脚手架脚本（阶段三）
- 不修改 task_trace.json 生成逻辑

## Decisions

### Decision 1: GIT_INDEX_FILE 方案

**选择**: 使用 `GIT_INDEX_FILE=.git/index.ccwhat` 创建隔离的 staging area。

**理由**:
- 不污染主 `.git/index`
- 能追踪未 git add 的新增文件（通过显式 `git add` 到备用 index）
- 原生 git diff 格式，可验证、可应用

**替代方案**: Python difflib 自实现（拒绝，需自己管理文件生命周期，复杂度高）

### Decision 2: 单文件 diff.patch vs 多文件

**选择**: 单文件 `diff.patch`，按 step 追加。

**理由**:
- 简单，与原有设计一致
- 易于查看完整变更历史
- 文件数少，目录清晰

**格式**:
```diff
# Step 1: Write src/app.py
# Timestamp: 2024-01-15T10:30:00Z
# Tool: Write
diff --git a/src/app.py b/src/app.py
new file mode 100644
...

# Step 2: Edit src/app.py
# Timestamp: 2024-01-15T10:31:00Z
# Tool: Edit
diff --git a/src/app.py b/src/app.py
...
```

### Decision 3: StepDiff 数据结构

```python
@dataclass
class StepDiff:
    step_index: int
    timestamp: str
    tool_name: str
    file_path: str
    diff: str
```

**理由**:
- 简单，足够描述一次文件修改
- 不存储 old_string/new_string（与 task_trace.json 重复）
- 存储在 diff.patch 注释中，不额外存 JSON

### Decision 4: 何时生成 diff

**选择**: 每次 `record_step()` 调用时生成该步骤的 diff。

**理由**:
- 及时，不依赖 finish 时一次性计算
- 失败时可追溯哪步出错

**流程**:
```
record_step(tool_name, file_path)
  -> CCWhatIndex.add(file_path)
  -> git diff HEAD > step_diff
  -> 追加到 diff.patch（带注释头）
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| `.git/index.ccwhat` 残留 | finish 时清理，或作为证据保留 |
| 并发修改同一文件 | 顺序处理，每次 add 后立刻 diff |
| diff 文件过大 | 当前不处理，后续可加压缩或分片 |

## Migration Plan

- 无破坏性变更，新增功能
- 现有 task（无 diff.patch）保持现状
- 新 task 自动生成 diff.patch

## Open Questions

1. **Q**: 是否需要存储每步的完整文件内容？
   **A**: 不需要，diff 足够重建变更。

2. **Q**: 删除文件如何处理？
   **A**: `CCWhatIndex.remove()` + diff 会显示删除。
