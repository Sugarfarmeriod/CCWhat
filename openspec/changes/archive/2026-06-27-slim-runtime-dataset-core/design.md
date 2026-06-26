## Context

当前 Runtime Dataset V2 在 `runtime-task-recording-mvp` 基础上完成了基本功能，但存在以下技术债务：

1. **control_events.jsonl**: 记录 task 边界事件（start/finish/abort），但诊断引擎实际从 `task.json` 和 `task_trace.json` 获取信息，该文件对用户透明
2. **repo_before/after.tar.gz**: 完整仓库快照，对大型仓库（如 100MB+）不可行，且与增量 diff 策略冲突
3. **ControlEvidence**: 过度设计的证据抽象，实际只用于 control_events.jsonl
4. **note 命令**: 未实际使用，增加维护负担

本 change 清理这些废弃结构，为后续 `add-incremental-diff-tracking` 奠定精简基础。

## Goals / Non-Goals

**Goals:**
- 删除 `control_events.jsonl` 及其生成逻辑
- 删除 `repo_before.tar.gz` 和 `repo_after.tar.gz` 及其打包逻辑
- 简化 `TaskStaging` 类，移除 `ControlEvidence` 和 `note` 方法
- 简化 controller 和 hook，移除废弃参数
- 更新测试，确保无回归

**Non-Goals:**
- 不修改 `task.json` 核心结构（保留 `paths` 和 `evidence_availability` 框架）
- 不修改 `task_trace.json` 生成逻辑
- 不新增功能（纯清理 change）
- 不改变 CLI 接口（`ccwhat -- claude` 行为不变）

## Decisions

### Decision 1: 彻底删除而非标记废弃

**选择**: 直接删除代码，不保留向后兼容开关。

**理由**:
- 项目仍处于 pre-1.0 阶段，无外部用户依赖
- 清理后代码更简单，后续增量 diff 实现更清晰
- 保留废弃代码会增加维护负担

**替代方案**: 保留配置开关允许回退（拒绝，过度设计）。

### Decision 2: 保留 `paths` 和 `evidence_availability` 结构

**选择**: 保留这两个字典的框架，只移除具体键值。

**理由**:
- 下游诊断引擎依赖这两个字段存在
- 后续增量 diff 会重新使用 `"diff"` 键
- 避免破坏性修改 `task.json` schema

### Decision 3: Hook payload 最小化

**选择**: 从 hook payload 中删除 `integration`, `model_visible`, `agent_log_visible`, `confidence`。

**理由**:
- 这些字段原本用于 `control_events.jsonl`，现已无需
- Hook 只需传递 `command` 和 `raw_args` 给 controller
- 简化后的 payload 更易理解和维护

### Decision 4: 测试策略

**选择**: 更新现有测试，删除对废弃文件的断言，不新增测试。

**理由**:
- 本 change 是纯删除，无新增行为
- 现有测试覆盖的路径（start/finish/abort）仍应工作
- 只需验证：task 能正常创建和完成，且不再生成废弃文件

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| 下游代码依赖废弃文件 | 搜索代码库确认无直接读取 `control_events.jsonl` 或 tar.gz 的代码；诊断引擎从 `task.json` 读取 metadata |
| 用户期望看到 control_events | 该文件从未在文档中公开，无用户依赖 |
| 删除后难以调试 | 保留 `task.json` 完整信息；如需详细事件流，可从 session log 提取 |
| 测试覆盖率下降 | 确保核心路径（start/finish）测试仍通过；删除的代码不再需测试 |

## Migration Plan

**部署步骤**:
1. 开发环境验证所有测试通过
2. 手动测试：
   - `ccwhat -- claude` 启动
   - `/ccwhat:start` 创建 task
   - `/ccwhat:finish` 完成 task
   - 验证 task 目录结构符合预期（无废弃文件）

**回滚策略**:
- 本 change 是纯删除，如需回滚需从 git 恢复代码
- 无数据库迁移或数据格式变更，回滚简单

## Open Questions

1. **Q**: `task.json` 中的 `"diff"` 键在阶段二会重新使用，是否现在保留？
   **A**: 现在删除，阶段二重新添加，保持每个 change 独立。

2. **Q**: 是否需要保留 `repo_before.tar.gz` 生成代码但默认禁用？
   **A**: 不需要，阶段二的增量 diff 完全替代该功能。

3. **Q**: 测试是否需要检查"文件不存在"？
   **A**: 不需要，只需验证正常文件存在，无需显式断言废弃文件不存在。
