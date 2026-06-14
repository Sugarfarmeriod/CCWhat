## Context

前两个 Dataset change 已完成：

- `add-task-dataset-core`：提供 Dataset v1 builder、writer、validator，能从 normalized session events 和 task segments 构建 Dataset 文件集合。
- `extract-dataset-change-evidence`：扩展 Dataset trace 的 `changes` / `patches` evidence 抽取。

当前还缺少产品入口：用户在 Viewer 完成 task segmentation 或 Task Trace Overlay 校正后，无法把结果保存为本地 Dataset Registry 中的稳定数据资产，也无法从浏览器下载分享用 `.tar.gz`。

本 change 负责把 Dataset core 接到 Viewer 的 Tasks 页面和 viewer server API。它是本阶段第三个 change，不继续扩展 schema，也不进入 evaluator。

## Goals / Non-Goals

**Goals:**

- 在 Tasks 页面提供“保存为 Dataset”入口。
- 提供保存确认 modal，展示本次保存范围和 Dataset v1 必选内容。
- 提供 `POST /api/save-task-dataset`，保存当前 session 的全部 tasks 到 `~/.ccwhat/datasets/<dataset-id>/`。
- 保存 API 接收完整 task source payload，并校验 session、provenance、overlay version 和 source trace 等来源信息。
- 支持可选下载 `dataset-*.tar.gz`，包内根目录为 `ccwhat-dataset/`。
- 保存后使用 Dataset validator 校验目录；下载前或打包后校验 tar 包。
- 明确处理未加载 session、未切分 task、overlay 未保存、保存失败和打包失败状态。

**Non-Goals:**

- 不做 evaluator，不自动写入 score。
- 不包含 raw session log 和 raw req/resp。
- 不新增 CLI 主入口。
- 不做 Dataset Registry 管理页面、列表、删除或重命名。
- 不改变 Dataset v1 schema。
- 不要求 Dataset 可复现完整 repo 环境。

## Decisions

### Decision 1: 保存源优先级使用 saved overlay，其次 task segmentation result

默认口径：

1. 如果当前 session 存在 active overlay 且 dirty，前端 SHALL 阻止保存并提示先保存或撤销编辑。
2. 如果当前 session 存在 saved overlay，保存 API 请求使用 `taskSource = "activeOverlay"` 并携带完整 saved overlay payload、overlay version、provenance 和 source trace 信息，让后端基于请求 payload 构建 Dataset。
3. 如果没有 saved overlay，但存在 task segmentation result，保存 API 请求使用 `taskSource = "taskSegments"` 并携带完整 segmentation payload、provenance 和 source trace 信息。
4. 如果两者都不存在，提示用户先进行任务切分。
5. server cache 只能作为 fallback 或辅助校验，不得作为唯一数据源。

原因：

- 用户人工校正后的 saved overlay 比自动切分结果更接近最终意图。
- dirty overlay 代表用户正在编辑，直接导出会制造“看起来已保存但其实不是最终版本”的混乱。

替代方案：永远导出当前 active overlay。放弃原因是会绕过“有未保存编辑”的产品边界。

### Decision 1.5: 请求 payload 必须带 provenance 并由后端校验

`POST /api/save-task-dataset` 不只传 `sessionId` 和 source 类型，还必须传完整 source payload：

```json
{
  "sessionId": "...",
  "taskSource": "activeOverlay",
  "source": {
    "kind": "overlay",
    "overlay": {},
    "overlayVersion": "task-trace-overlay-v1",
    "provenance": {
      "source": "manual | edited | auto",
      "sessionId": "...",
      "sourceTraceId": "...",
      "savedAt": "2026-06-14T12:00:00Z"
    }
  }
}
```

后端必须校验：

- 请求 `sessionId` 与 provenance / source payload 中的 session id 一致。
- overlay payload 的版本受支持。
- source trace / task 边界能与当前 session 的 normalized events 对齐。
- dirty overlay 不允许发送；前端必须先保存 overlay，后端也应拒绝缺少 saved provenance 的 overlay payload。
- Dataset bundle 构建后必须通过 Dataset validator。

原因：

- 前端 overlay 是用户校正后的最终来源，不能假设 server cache 一定有同一份状态。
- provenance 让后续 evaluator 和审计能知道 Dataset 来自自动切分、手动切分还是编辑后的 overlay。

### Decision 2: Registry 写入位置和 id 稳定

Dataset Registry 根目录：

```text
~/.ccwhat/datasets/
```

Dataset id：

```text
dataset-YYYYMMDD-HHMMSS-<session-short-id>
```

保存路径：

```text
~/.ccwhat/datasets/<dataset-id>/
  manifest.json
  dataset.jsonl
  traces/
  scores.jsonl
```

如果同一秒发生冲突，实施可以追加短 suffix 或重试到唯一目录，但响应中必须返回最终 `datasetId` 和 `datasetPath`。

原因：

- 可读、可排序、可和 session 关联。
- 后续 evaluator 可以直接扫描 registry。

### Decision 3: API 保存和下载分离，但保存请求可要求返回 downloadUrl

`POST /api/save-task-dataset` 请求：

```json
{
  "sessionId": "...",
  "taskSource": "activeOverlay | taskSegments",
  "source": {
    "kind": "overlay | taskSegments",
    "payload": {},
    "overlayVersion": "task-trace-overlay-v1",
    "provenance": {
      "source": "auto | manual | edited",
      "sessionId": "...",
      "sourceTraceId": "..."
    }
  },
  "download": false,
  "includeRawSession": false,
  "includeReqResp": false
}
```

响应：

```json
{
  "ok": true,
  "datasetId": "dataset-20260614-153000-aabb1122",
  "datasetPath": "~/.ccwhat/datasets/dataset-20260614-153000-aabb1122",
  "downloadUrl": "/api/task-datasets/dataset-20260614-153000-aabb1122/download"
}
```

默认选择：

- `download = false` 时只保存并返回 `downloadUrl`。
- “保存并下载 .tar.gz” 由前端先调用保存 API，再请求 `downloadUrl` 触发浏览器下载。
- `includeRawSession` / `includeReqResp` 第一版必须为 `false` 或缺省；若为 `true`，API SHALL 返回 400，不能 warning 后忽略。

原因：

- 保存是产品主路径，下载是分享/迁移动作。
- 分离后，保存成功但下载失败时用户仍然得到本地 Dataset。

### Decision 4: tar.gz 只打包 Dataset v1 文件集合

下载文件名：

```text
dataset-YYYYMMDD-HHMMSS-<session-short-id>.tar.gz
```

包内结构：

```text
ccwhat-dataset/
  manifest.json
  dataset.jsonl
  traces/
  scores.jsonl
```

下载包不包含 registry 目录名，不包含 raw session / req-resp，不包含 diagnostic export 的 README / view.command，除非后续 change 明确加入。

### Decision 4.5: raw session / req-resp 选项第一版完全隐藏

保存确认 modal 第一版只展示 Dataset v1 必选内容，不展示 raw session 或 raw req/resp 选项，也不展示 disabled checkbox。

原因：

- 隐藏未实现选项可以避免用户误解 Dataset 已包含原始日志。
- API 层仍对 raw inclusion 请求返回 400，防止外部调用误用。

### Decision 5: 保存后必须 validator 通过

保存流程：

1. 加载 session。
2. 校验请求中的 task source payload、provenance、overlay version 和 source trace 信息。
3. 调用 Dataset builder。
4. 写入临时目录或目标目录。
5. 调用 Dataset validator。
6. validator 通过后完成保存；失败则返回 500 并报告可读错误。

实现可以先写临时目录再原子 rename，降低半成品目录留在 registry 的风险。

## Risks / Trade-offs

- [Risk] 前端 overlay 状态只存在浏览器内存，后端不知道 active saved overlay。→ Mitigation: API 必须接收完整 overlay payload、provenance、overlay version 和 source trace；server cache 只做 fallback 或辅助校验。
- [Risk] `datasetPath` 暴露本机路径。→ Mitigation: 这是本地开发工具，按 plan 默认返回；如需脱敏后续单独改。
- [Risk] 保存成功但下载失败。→ Mitigation: 保存和下载分离，UI 明确显示 dataset id / path，下载失败单独报错。
- [Risk] `includeRawSession` / `includeReqResp` 用户期望可用。→ Mitigation: modal 第一版完全隐藏 raw 选项；API 对 true 返回 400。
- [Risk] registry 目录写入失败或权限问题。→ Mitigation: API 返回 500，并显示保存失败原因；不吞错。

## Migration Plan

这是新增产品能力，不需要迁移旧 Dataset。

后续增强路径：

1. `include-raw-sources-in-dataset-export` 增加 raw session / req-resp inclusion。
2. `evaluate-dataset-scores` 读取 registry 中的 Dataset 并写入 `scores.jsonl`。
3. 可另开 change 增加 Dataset Registry 列表/删除/管理 UI。

## Confirmed Decisions

- raw session / req-resp 选项第一版完全隐藏，不展示不可用选项。
- API 对 `includeRawSession = true` / `includeReqResp = true` 返回 400，不能 warning 后忽略。
- 保存 API 接收完整 overlay payload 或 task segmentation payload，并要求 session、task source、provenance、overlay version、source trace 信息；server cache 只能作为 fallback 或辅助校验，不作为唯一数据源。
