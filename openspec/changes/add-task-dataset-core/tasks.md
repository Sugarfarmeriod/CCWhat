## 1. 数据契约与模块结构

- [x] 1.1 新增 `ccwhat/task_dataset/` 模块结构，包含 `models.py`、`builder.py`、`validator.py` 和 `__init__.py`。
- [x] 1.2 定义 Dataset v1 常量与类型结构，覆盖 `manifest.json`、`dataset.jsonl` row、trace JSON、score row 和 validation result。
- [x] 1.3 实现 Dataset bundle 的序列化辅助，能生成 `manifest.json`、`dataset.jsonl`、`traces/*.json` 和空 `scores.jsonl` 的字节或文本内容。
- [x] 1.4 明确允许 `base_commit`、`head_commit`、`success_criteria` 等无法取得的字段为 `null`，并保持字段稳定存在。

## 2. Dataset Builder

- [x] 2.1 实现从 session metadata、normalized events 和 `TaskSegmentationResult` 构建 Dataset bundle。
- [x] 2.2 为每个 `TaskSegment` 生成一个 dataset item，并写入 `metadata.trace_id`、`metadata.trace_path`、task source、session id、agent、起止 event id。
- [x] 2.3 为每个 `TaskSegment` 生成一个 trace JSON，并保证 `trace.task_id` 与 dataset item `id` 一致。
- [x] 2.4 按 `start_event_id` / `end_event_id` 从 normalized events 中裁剪 trace `events` 闭区间；`end_event_id` 为空时延伸到 session 末尾。
- [x] 2.5 从 task evidence 和边界内 events 填充 `commands`、`test_commands`、`files.read`、`files.changed`、`errors`、`final_claim` 和 `repo_state`。
- [x] 2.6 在本 change 中保留 `changes` 与 `patches` 为空数组，不做 agent-specific patch/diff 抽取。
- [x] 2.7 对找不到 task 边界 event、空 task 列表或 trace 引用异常返回清晰错误。

## 3. Dataset Validator

- [x] 3.1 实现 validator 对 Dataset 目录的读取和校验。
- [x] 3.2 实现 validator 对已存在 tar 包的读取和校验，复用同一套结构与 schema 校验逻辑。
- [x] 3.3 校验必需路径：`manifest.json`、`dataset.jsonl`、`scores.jsonl`、`traces/`。
- [x] 3.4 校验 JSON / JSONL 可解析，并在失败时报告文件路径和行号或字段位置。
- [x] 3.5 校验 `manifest.schema_version == "ccwhat-dataset-v1"`。
- [x] 3.6 校验 manifest counts 与实际 dataset item、trace、score 数量一致。
- [x] 3.7 校验每个 dataset item 的 `metadata.trace_path` 存在，且对应 trace 的 `task_id` 与 dataset item `id` 一致。

## 4. Fixtures 与测试

- [x] 4.1 新增最小 Claude Code fixture，覆盖至少一个 task 的 Dataset 构建和 validator 通过。
- [x] 4.2 新增最小 Codex fixture，覆盖至少一个 task 的 Dataset 构建和 validator 通过。
- [x] 4.3 新增最小 OpenCode fixture，覆盖至少一个 task 的 Dataset 构建和 validator 通过。
- [x] 4.4 新增 builder 单元测试，覆盖 dataset item、trace、event 裁剪、空 `scores.jsonl`、空 `changes` / `patches`。
- [x] 4.5 新增 validator 单元测试，覆盖合法目录、合法 tar 包、缺少必需文件、坏 JSONL、trace 引用缺失、task id 不一致、counts 不一致。
- [x] 4.6 新增或更新测试，确认本 change 不新增 viewer 保存按钮、`POST /api/save-task-dataset` 或 evaluator score 行为。

## 5. 验证与交接

- [x] 5.1 运行 Dataset core 相关单元测试。
- [x] 5.2 运行现有 task segmentation 相关测试，确认 builder 输入仍与 `TaskSegmentationResult` 兼容。
- [x] 5.3 运行 `openspec validate add-task-dataset-core --strict`。
- [x] 5.4 更新实现交接说明，记录 Dataset v1 字段、validator 使用方式和后续 change 接入点。

## 6. Review 返修项

- [x] 6.1 Validator 必须补齐 Dataset v1 基础 schema / 必填字段校验：`manifest.json` 需校验 `created_at`、`tool == "ccwhat"`、`session`、`counts`；`dataset.jsonl` 每行需校验 `id`、`input.instruction`、`input.repo`、`input.base_commit`、`expected.success_criteria`、`expected.tests`、`metadata.agent`、`metadata.session_id`、`metadata.task_source`、`metadata.trace_id`、`metadata.trace_path`、`metadata.start_event_id`、`metadata.end_event_id` 等稳定字段存在；`traces/*.json` 需校验 `trace_id`、`task_id`、`session_id`、`agent`、`boundary`、`events`、`commands`、`test_commands`、`files.read`、`files.changed`、`changes`、`patches`、`errors`、`final_claim`、`repo_state` 等稳定字段存在。
- [x] 6.2 新增 validator 负向测试：构造 counts 和 trace 引用都一致、但删除 Dataset v1 必填字段的数据包，必须返回失败并报告对应路径/字段；至少覆盖 manifest、dataset row、trace 三类文件。
- [x] 6.3 Validator 必须对包内所有 `traces/*.json` 执行基础 schema / 必填字段校验，不能只校验被 `dataset.jsonl` 引用到的 trace；当存在未引用但格式合法 JSON、schema 缺字段的 trace 文件且 manifest trace count 一致时，也必须返回失败并报告该 trace path/field。
- [x] 6.4 新增 validator 负向测试：构造一个 Dataset，其中正常 dataset row 引用的 trace 合法，同时额外放入一个 `traces/extra.json` 并更新 `manifest.counts.traces` 使 count 一致；`traces/extra.json` 缺少 `events`、`files` 或 `repo_state` 等必填字段时，validator 必须失败。
