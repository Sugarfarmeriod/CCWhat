## Context

当前 `trace_extractor.py` 的实现中，`extract_task_trace()` 函数在以下情况返回 `None`：
- agent 不是 claude（unsupported_agent）
- 时间窗口解析失败（invalid_time_bounds）
- 找不到项目目录或日志文件（log_not_found）
- 时间窗内无事件（no_events）

这导致 `staging.py` 的 `finish_task()` 必须处理复杂的分支逻辑：

```python
if trace is not None:
    self._write_json(task_dir / "task_trace.json", trace)
    task["paths"]["task_trace"] = "task_trace.json"
    task["evidence_availability"]["task_trace"] = True
else:
    task["evidence_availability"]["task_trace"] = False
```

这种设计带来几个问题：
1. **下游消费不确定性**：消费 task dataset 的工具必须检查 `evidence_availability.task_trace` 再决定是否读取文件
2. **信息丢失**：返回 `None` 时，调用方无法区分是"不支持"、"找不到日志"还是"无事件"
3. **代码复杂度高**：需要维护 `trace is not None` 分支，容易出错

## Goals / Non-Goals

**Goals:**
- 确保每个 finalized task 目录都包含 `task_trace.json`
- 通过 `extraction_status` 字段显式表达提取结果状态
- 简化 `staging.py` 代码，消除 `trace is None` 分支
- 保持向后兼容：正常提取的 task_trace.json 结构不变

**Non-Goals:**
- 不修改正常提取的 task_trace.json 字段结构
- 不添加新的提取字段或证据类型
- 不扩展对非 Claude agent 的完整支持（仅标记为 unsupported_agent）

## Decisions

### Decision: 始终返回 dict，用 extraction_status 替代 None

**Rationale:**
- 消除 `None` 分支后，staging.py 代码从 8 行减至 3 行，逻辑更清晰
- 下游工具可以统一读取文件，通过 `extraction_status` 判断可用性
- 符合"失败也是一种结果"的理念，比隐性失败更健壮

**Alternative considered:** 保持现有设计，添加更多 `evidence_availability` 子字段来区分失败类型。Rejected：增加复杂度且不解决核心问题（文件可能不存在）。

### Decision: extraction_status 枚举值使用 snake_case 字符串

**Rationale:**
- 与现有代码风格保持一致（如 `evidence_availability`）
- 便于人类阅读和日志记录
- 不依赖外部枚举定义，减少导入复杂度

**Values:**
- `ok`: 正常提取
- `unsupported_agent`: agent 不是 claude
- `invalid_time_bounds`: 时间窗口解析失败
- `log_not_found`: 找不到项目目录或日志文件
- `no_events`: 时间窗内无事件

### Decision: 异常情况下仍返回完整字段结构（空值填充）

**Rationale:**
- 下游工具可以用统一方式解析 JSON，无需处理缺失字段
- 明确表达"哪些数据确实不存在" vs "哪些字段被遗漏"

**结构示例（unsupported_agent）:**
```json
{
  "task_id": "task-001",
  "run_id": "run-001",
  "agent": "codex",
  "extraction_status": "unsupported_agent",
  "extraction_status_reason": "Agent 'codex' is not supported for trace extraction",
  "time_window": {"started_at": null, "finished_at": null},
  "events": [],
  "commands": [],
  "test_commands": [],
  "files": {"read": [], "changed": []},
  "changes": [],
  "patches": [],
  "errors": [],
  "final_claim": null,
  "repo_state": {"cwd": null, "base_commit": null, "head_commit": null}
}
```

## Risks / Trade-offs

**Risk: 磁盘空间增加** → 即使提取失败也会写入 task_trace.json（约 500 字节）。Mitigation: 相比 repo_before/after.tar.gz，此开销可忽略。

**Risk: 下游工具未适配 extraction_status** → 现有工具可能假设 `task_trace.json` 存在即表示有数据。Mitigation: 文档明确说明此变更，extraction_status 为 `ok` 时才表示数据可用。

**Trade-off: 正常提取的 task_trace.json 也会包含 extraction_status** → 文件大小增加 30 字节，但获得一致性收益。

## Migration Plan

此变更不需要数据迁移：
- 新产生的 task 会包含 extraction_status 字段
- 历史 task 保持不变（已有 task_trace.json 的不会被修改）

代码迁移：
1. 更新 `trace_extractor.py` 返回类型和错误处理
2. 更新 `staging.py` 移除 `if trace is not None` 分支
3. 更新测试断言，使用 `extraction_status` 替代 `trace is None` 检查
