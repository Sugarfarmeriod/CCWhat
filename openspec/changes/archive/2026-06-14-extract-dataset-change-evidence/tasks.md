## 1. Evidence 数据结构与抽取入口

- [x] 1.1 扩展 `ccwhat/task_dataset/models.py`，定义 change evidence 和 patch evidence 的稳定字段、枚举和类型。
- [x] 1.2 新增或等价实现 `ccwhat/task_dataset/change_evidence.py`，提供从 task events 抽取 `changes` / `patches` 的入口函数。
- [x] 1.3 实现稳定 id 生成规则，例如按 task 内 evidence 顺序生成 `change-001`、`patch-001`，并保证 change 可引用对应 patch。
- [x] 1.4 明确没有对应 patch 的 change entry 使用 `patch_id = null`，并保持 `old_string`、`new_string`、`content` 等字段稳定存在。

## 2. Normalized Event 证据保留

- [x] 2.1 检查 Claude Code `normalize_main_entries` 是否保留 `Edit`、`MultiEdit`、`Write`、`Bash` 所需 tool input；缺失时只保留最小必要字段到 `raw_ref` 或 `metadata`。
- [x] 2.2 检查 OpenCode adapter-normalized event 到 `NormalizedEvent` 的转换是否保留 `oldString/newString`、`metadata.diff/filediff`、`patchText` 所需字段；缺失时补齐最小必要字段。
- [x] 2.3 检查 Codex adapter-normalized event 到 `NormalizedEvent` 的转换是否保留 `patch_apply_end` payload 中 `changes[path].unified_diff` 和新增文件 `content`；缺失时补齐最小必要字段。
- [x] 2.4 增加回归测试，防止 future normalizer 再次丢失 evidence 抽取所需字段。

## 3. Agent-specific Evidence 抽取

- [x] 3.1 实现 Claude Code `Edit` / `MultiEdit` 抽取：生成 `source = claude_edit`、`kind = edit`、`confidence = medium` 的 change entry，不自动生成 patch。
- [x] 3.2 实现 Claude Code `Write` 抽取：生成 `source = claude_write`、`kind = write` 的 change entry，不自动生成 patch。
- [x] 3.3 实现 Claude Code / 通用 `Bash.command` 抽取：生成 `source = bash_command`、`kind = command` 的 change entry，不生成 patch。
- [x] 3.4 实现 OpenCode `oldString/newString` 抽取：生成 `source = opencode_edit`、`kind = edit`、`confidence = medium` 的 change entry。
- [x] 3.5 实现 OpenCode `metadata.diff` / `metadata.filediff` 抽取：生成 `format = opencode_diff`、`confidence = high` 的 patch entry，并生成引用它的 change entry。
- [x] 3.6 实现 OpenCode `apply_patch.patchText` 或等价 patch part 抽取：生成 `format = apply_patch`、`source = opencode_patch`、`confidence = high` 的 patch entry，并生成引用它的 change entry。
- [x] 3.7 实现 Codex `patch_apply_end.changes[path].unified_diff` 抽取：生成 `format = unified_diff`、`source = codex_patch_apply_end`、`confidence = high` 的 patch entry，并生成引用它的 change entry。
- [x] 3.8 实现 Codex 新增文件 `content` 抽取：生成可证明 change entry；只有存在 `unified_diff` 时才生成 patch entry。

## 4. Builder 与 Validator 集成

- [x] 4.1 在 Dataset builder 裁剪出每个 task 的 `task_events` 后调用 evidence 抽取入口，并写入 trace `changes` / `patches`。
- [x] 4.2 保证 evidence 抽取严格限制在当前 task 边界内，不跨 task 泄漏。
- [x] 4.3 保持没有可证明 evidence 的 trace 继续输出 `changes: []` 和 `patches: []`。
- [x] 4.4 扩展 validator 校验 `changes` entry 的必填字段和 `kind` / `confidence` 枚举。
- [x] 4.5 扩展 validator 校验 `patches` entry 的必填字段和 `format` / `confidence` 枚举。
- [x] 4.6 扩展 validator 校验非空 `patch_id` 必须引用同 trace 中存在的 patch entry。

## 5. Fixtures 与测试

- [x] 5.1 新增 Claude Code fixture，覆盖 `Edit.old_string/new_string`、`Write.content`、`Bash.command`。
- [x] 5.2 新增 OpenCode fixture，覆盖 `oldString/newString`、`metadata.diff/filediff` 和 `apply_patch.patchText`。
- [x] 5.3 新增 Codex fixture，覆盖 `patch_apply_end.changes[path].unified_diff` 和新增文件 `content`。
- [x] 5.4 新增 task 边界过滤测试，确认第二个 task 的 patch 不出现在第一个 task trace。
- [x] 5.5 新增 Bash-only 测试，确认只生成 command change，不生成 patch。
- [x] 5.6 新增 validator 负向测试，覆盖 change 缺字段、change 枚举非法、patch 缺字段、patch 枚举非法、patch_id 引用不存在。
- [x] 5.7 新增或更新测试，确认本 change 不新增 viewer 保存按钮、`POST /api/save-task-dataset`、registry 写入、tar.gz 下载入口或 evaluator score。

## 6. 验证与交接

- [x] 6.1 运行 Dataset core / change evidence 相关单元测试。
- [x] 6.2 运行 task segmentation 和 adapter-normalization 相关测试，确认 evidence 字段保留不破坏现有行为。
- [x] 6.3 运行 `openspec validate extract-dataset-change-evidence --strict`。
- [x] 6.4 更新实现交接说明，记录各 agent evidence 字段映射、confidence 规则和后续 viewer save/export change 的接入点。

## 7. Review 返修项

- [x] 7.1 修复真实 Codex adapter-normalized 路径下 `patch_apply_end` evidence 丢失的问题：`CodexAdapter.raw_to_normalized_events()` 产出的 event 经 `normalize_session_events()` 转成 `NormalizedEvent` 后，builder 必须能识别 `content.type == "patch_apply_end"` 或 `raw.payload.type == "patch_apply_end"`，并从 `changes[path].unified_diff` / `content` 抽取 `changes` 和 `patches`。
- [x] 7.2 新增回归测试，使用 `CodexAdapter.raw_to_normalized_events()` 生成 `patch_apply_end` event，再经 `normalize_session_events()` 和 `build_dataset_bundle()` 构建 Dataset，断言 Codex unified diff 生成 `source = codex_patch_apply_end`、`format = unified_diff` 的 patch entry，并生成引用该 patch 的 change entry。
