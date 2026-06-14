## Context

`task-dataset-core` 已经提供 Dataset v1 文件契约、builder 和 validator。当前 trace 中已有 `events`、`commands`、`files`、`errors`、`final_claim`、`repo_state`，但 `changes` / `patches` 仍为空数组。

这两个字段是 Dataset 后续被 evaluator、失败归因和离线分析使用的关键证据层：

- `changes` 表达“发生过什么改动证据”，包括 edit、write、patch、command 等。
- `patches` 只表达“真实存在或可确定性派生的 diff / patch 文本”。

三类 agent 的日志形态不同：

| Agent | 可用证据 | 第一版策略 |
| --- | --- | --- |
| Claude Code | tool input 中的 `Edit.old_string/new_string`、`Write.content`、`Bash.command` | 记录 change evidence；不把 `old_string/new_string` 强行当标准 patch |
| OpenCode | tool input / part state 中的 `oldString/newString`、`metadata.diff/filediff`、`apply_patch.patchText` | 有 diff/patch 字段时记录 patch evidence |
| Codex | `patch_apply_end` payload 中的 `changes[path].unified_diff` 或新增文件 `content` | 有 `unified_diff` 时记录 patch evidence；新增文件 content 作为 change evidence |

当前 `NormalizedEvent` 已有 `raw_ref` 和 `metadata` 字段，但 Codex / OpenCode 的 adapter-normalized events 转换为 `NormalizedEvent` 时可能只保留 `eventId`。本 change 需要保证 builder 能读取抽取 evidence 必需的原始片段，但不要求把完整 raw session 写进 Dataset。

## Goals / Non-Goals

**Goals:**

- 定义稳定的 `DatasetChangeEvidence` 和 `DatasetPatchEvidence` 结构。
- 在 Dataset builder 生成 trace 时，从 task 边界内的 events 抽取 `changes` / `patches`。
- 覆盖 Claude Code、OpenCode、Codex 的核心 edit / write / patch / command evidence。
- 对每条 evidence 标注 `source`、`kind`、`confidence`，patch evidence 还要标注 `format`。
- 保证 evidence 只来自 session/event 中已有的可证明字段。
- 增加 validator 对 `changes` / `patches` 基础 schema 的校验。
- 增加 fixtures 和测试，覆盖三类 agent、task 边界过滤、Bash-only 不生成 patch、禁止 LLM 猜测。

**Non-Goals:**

- 不新增 viewer 保存入口、HTTP API、registry 或 tar.gz 下载入口。
- 不做 evaluator，不写入 `scores.jsonl`。
- 不做 repo 现场 `git diff`，不读取当前工作区文件生成 patch。
- 不通过 LLM 或 heuristic 猜测缺失 patch。
- 不要求 Claude Code 的 `old_string/new_string` 变成标准 unified diff。
- 不做 before/after 全量文件快照。

## Decisions

### Decision 1: 在 `ccwhat/task_dataset/` 内新增 evidence 抽取层

建议新增或等价实现：

```text
ccwhat/task_dataset/
  change_evidence.py
```

核心函数：

```text
extract_change_evidence(events, agent) -> tuple[list[change], list[patch]]
```

builder 在裁剪出每个 task 的 `task_events` 后调用该函数，并把返回值写入 trace。

原因：

- evidence 抽取依赖 Dataset trace 的目标 schema，但不应污染 task segmentation 的边界判断逻辑。
- 后续 `extract-dataset-change-evidence` 可独立测试，不需要启动 viewer 或 API。

替代方案：把逻辑写进 `builder.py`。放弃原因是三类 agent 的字段映射会让 builder 过胖，测试也不清楚。

### Decision 2: 统一 changes / patches schema

`changes` entry 使用稳定字段：

```json
{
  "change_id": "change-001",
  "event_id": "main:51",
  "file": "viewer/claude-log.html",
  "kind": "edit | write | patch | command | git_diff",
  "source": "claude_edit | claude_write | bash_command | opencode_edit | opencode_patch | codex_patch_apply_end",
  "old_string": null,
  "new_string": null,
  "content": null,
  "patch_id": "patch-001",
  "confidence": "high | medium | low"
}
```

`patches` entry 使用稳定字段：

```json
{
  "patch_id": "patch-001",
  "scope": "step | task",
  "file": "viewer/claude-log.html",
  "source": "codex_patch_apply_end",
  "format": "unified_diff | apply_patch | git_diff | opencode_diff",
  "confidence": "high | medium",
  "patch": "@@ -10,7 +10,7 @@\n-old\n+new\n"
}
```

规则：

- 原生日志已有 diff / patch 字段：`confidence = "high"`。
- `old_string/new_string` 这类可确定性 edit evidence：change `confidence = "medium"`，不强制生成 patch。
- Bash / shell 命令修改文件但没有 diff：只记录 command change，`confidence = "low"` 或按可用字段设为 `medium`，不生成 patch。
- `patch_id` 只在 change 对应某条 patch evidence 时填写，否则为 `null`。

### Decision 3: evidence 必须按 task 边界过滤

抽取层只接收 builder 已经裁剪好的 `task_events`。这保证：

- task A 的 patch 不会泄漏到 task B。
- open-ended task 仍然按 builder 当前规则延伸到 session 末尾。
- tests 可以用两个 task 的 fixture 验证边界隔离。

### Decision 4: 必要时扩展 normalizer 保留原始 evidence 片段

如果当前 normalized events 没有保留字段，实施可以扩展：

- Claude Code `normalize_main_entries`：在 `raw_ref` 或 `metadata` 中保留 tool input 的最小子集，例如 `tool_input`。
- Codex / OpenCode `_normalize_from_events`：在 `raw_ref` 或 `metadata` 中保留 adapter-normalized event 的最小子集，例如 `raw_event`、`content`、`summary`、`toolName`。

保留策略应遵守最小必要原则：

- 保留 evidence 抽取所需字段。
- 不把 raw req/resp 或完整 session 包进 Dataset trace。
- Dataset trace 的 `events` 可以继续是当前 normalized event dict；change/patch evidence 是面向消费方的结构化摘要。

### Decision 5: validator 校验 evidence schema，不验证 patch 可应用

validator 应新增基础 schema 校验：

- `changes` 必须是数组，每条 entry 必须包含 `change_id`、`event_id`、`kind`、`source`、`confidence`。
- `kind` 必须属于允许枚举。
- `confidence` 必须属于允许枚举。
- `patch_id` 非空时必须引用同 trace 的 `patches` entry。
- `patches` 必须是数组，每条 entry 必须包含 `patch_id`、`source`、`format`、`confidence`、`patch`。
- `format` 必须属于允许枚举。

validator 不检查 patch 能否应用，不检查 file 是否存在于当前工作区，不推断 command 是否真的修改文件。

## Risks / Trade-offs

- [Risk] Codex / OpenCode normalizer 目前可能丢失 patch payload。→ Mitigation: 扩展 normalized event 的 `raw_ref` / `metadata` 最小保留字段，并增加回归测试防止再次丢失。
- [Risk] Claude Code `old_string/new_string` 被误当成标准 patch。→ Mitigation: spec 明确只生成 change evidence，不生成 patch evidence，除非日志中已有真实 patch/diff。
- [Risk] Bash 命令可能修改文件但没有 diff。→ Mitigation: 只记录 command evidence，不制造 patch。
- [Risk] 不同 agent 的字段名会继续变化。→ Mitigation: 抽取层用小函数分 agent 处理，fixture 覆盖已知字段；未知字段保持忽略而不是猜测。
- [Risk] `content` 可能较大。→ Mitigation: 本 change 先保留可证明内容；如需截断或脱敏，后续以独立 change 定义规则，避免静默丢失 evidence。

## Migration Plan

这是 Dataset v1 的向前兼容增强：

1. 既有 Dataset trace 中 `changes: []` 和 `patches: []` 仍合法。
2. 新 builder 在有可证明 evidence 时填充数组。
3. validator 增加 schema 校验后，应继续接受空数组。

## Open Questions

- Claude Code `Write.content` 是否允许完整写入 Dataset change evidence，还是需要在实现阶段设置大小上限或摘要字段？
- Bash command evidence 的默认 `confidence` 应固定为 `low`，还是区分明确写文件命令为 `medium`？
- 是否需要在 `changes` entry 中增加 `tool_name` / `tool_use_id` 作为可选字段，方便后续 UI 或 evaluator 对齐原始 event？
