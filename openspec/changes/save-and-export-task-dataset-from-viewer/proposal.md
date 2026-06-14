## Why

前两个 change 已经让 CCWhat 可以从已切分 Task 构建并校验 Dataset v1，且 trace 中包含三类 agent 的文件改动 evidence。下一步不应继续扩展底层 schema，而应把 Dataset 变成用户可在 Viewer 中保存、复用和下载的数据资产。

本 change 将 Dataset Save / Export 接到 Tasks 页面：用户完成 task segmentation 或保存后的 overlay 校正后，可以将当前 session 的全部 tasks 保存到本地 Dataset Registry，并可选下载 `.tar.gz`。

## What Changes

- 在 Tasks 页面增加“保存为 Dataset”入口。
- 新增保存确认 modal，展示本次 Dataset 范围和必选内容：`manifest.json`、`dataset.jsonl`、`traces/*.json`、空 `scores.jsonl`。
- 新增 `POST /api/save-task-dataset`，接收完整 task source payload、provenance 信息，并从 saved overlay 或 task segmentation result 构建 Dataset。
- 新增本地 Dataset Registry 目录：`~/.ccwhat/datasets/<dataset-id>/`。
- 保存后调用 Dataset validator，确保落盘目录符合 Dataset v1。
- 支持“保存并下载 .tar.gz”，下载文件名为 `dataset-<timestamp>-<session-short-id>.tar.gz`。
- 下载包内部根目录固定为 `ccwhat-dataset/`，包含 Dataset v1 文件集合。
- 处理未加载 session、未切分 task、overlay 未保存或无效、保存失败、打包失败等状态。
- 第一版完全隐藏 raw session log 和 raw req/resp 选项；如果 API 收到 raw inclusion 请求，必须返回 400。
- 保存请求必须携带 session、task source、provenance、overlay version 和 source trace 信息；后端必须校验这些来源信息和 Dataset schema。

## Capabilities

### New Capabilities

- `task-dataset-save-export`: 定义 Viewer 中保存 Task Dataset 到本地 registry，并可选通过浏览器下载 `.tar.gz` 的产品流程、API、状态和验收行为。

### Modified Capabilities

- 无。

## Impact

- 预计影响 `viewer/server.py`：新增保存 API 和 Dataset 下载 API / handler。
- 预计影响 `viewer/claude-log.html`：Tasks 页面按钮、保存确认 modal、保存/下载状态反馈。
- 预计复用 `ccwhat/task_dataset/` 的 builder、writer 和 validator。
- 预计复用或参考现有 diagnostic export 的 tar.gz 打包风格，但 Dataset 下载内容与 diagnostic package 不同。
- 不新增 CLI 主入口。
- 不做 evaluator，不写入非空 score。
- 不支持 raw session / req-resp inclusion；该能力留给后续 `include-raw-sources-in-dataset-export`。
- 不依赖 server cache 作为唯一数据源；server cache 只能作为 fallback 或辅助校验。
