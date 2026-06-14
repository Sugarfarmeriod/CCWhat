## 1. 后端保存服务

- [x] 1.1 新增 Dataset Registry 路径解析，默认根目录为 `~/.ccwhat/datasets/`。
- [x] 1.2 实现稳定 `datasetId` 生成：`dataset-YYYYMMDD-HHMMSS-<session-short-id>`，冲突时生成唯一 id。
- [x] 1.3 实现 `POST /api/save-task-dataset` 请求解析与校验，支持 `sessionId`、`taskSource`、完整 `source` payload、`download`、`includeRawSession`、`includeReqResp`。
- [x] 1.4 对不存在 session 返回 404，对无 task source payload 返回 400，对 `includeRawSession/includeReqResp = true` 返回 400，不能 warning 后忽略。
- [x] 1.5 校验请求 provenance：`sessionId` 必须与 source payload / provenance 中的 session id 一致，且必须包含 source trace 或 task boundary 来源信息。
- [x] 1.6 校验 overlay source：必须接收完整 saved overlay payload，overlay version 必须受支持，provenance 必须表明 overlay 已保存；dirty overlay 不得作为保存 source。
- [x] 1.7 校验 task segmentation source：必须接收完整 task segmentation payload，并校验 provenance 和 source trace / task boundary 能与当前 session normalized events 对齐。
- [x] 1.8 将通过校验的 task source payload 转换为 Dataset builder 可消费的输入；server cache 只能作为 fallback 或辅助校验，不作为唯一数据源。
- [x] 1.9 将 Dataset bundle 写入 registry 目录，并在成功响应中返回 `datasetId`、`datasetPath`、`downloadUrl`。
- [x] 1.10 保存后调用 Dataset validator 校验 registry 目录；校验失败时返回 500 和可读错误。

## 2. Dataset 下载与打包

- [x] 2.1 新增 Dataset 下载 handler，例如 `GET /api/task-datasets/<dataset-id>/download`。
- [x] 2.2 下载 handler 只允许读取 `~/.ccwhat/datasets/<dataset-id>/` 下的已保存 Dataset，避免路径穿越。
- [x] 2.3 生成 `dataset-*.tar.gz`，包内根目录固定为 `ccwhat-dataset/`。
- [x] 2.4 tar.gz 仅包含 `manifest.json`、`dataset.jsonl`、`traces/*.json`、`scores.jsonl`，不包含 raw session、req/resp、diagnostic README 或 view.command。
- [x] 2.5 下载前或打包后使用 Dataset validator 校验 tar 包结构。
- [x] 2.6 设置 `Content-Type: application/gzip` 和 `Content-Disposition`，触发浏览器标准下载。

## 3. 前端 Tasks 页面入口

- [x] 3.1 在 Tasks 页面右上角新增“保存为 Dataset”按钮。
- [x] 3.2 未加载 session 时按钮 disabled。
- [x] 3.3 已加载 session 但无 saved overlay 和 task segmentation result 时，点击后提示先进行任务切分。
- [x] 3.4 存在 dirty Task Trace Overlay 时，点击后提示先保存或撤销编辑，并阻止保存请求。
- [x] 3.5 有 saved overlay 时优先使用 saved overlay 作为保存 source，并发送完整 overlay payload、overlay version、provenance 和 source trace 信息。
- [x] 3.6 无 saved overlay 但有 task segmentation result 时，发送完整 task segmentation payload、provenance 和 source trace 信息。

## 4. 保存确认 modal 与反馈

- [x] 4.1 新增保存确认 modal，展示当前 session 全部 tasks、task 数量和 Dataset v1 必选内容。
- [x] 4.2 在 modal 中展示 `manifest.json`、`dataset.jsonl`、`traces/*.json`、`scores.jsonl` 空文件。
- [x] 4.3 第一版完全隐藏 raw session 和 raw req/resp 选项，不展示不可用 checkbox。
- [x] 4.4 实现“保存 Dataset”：调用 `POST /api/save-task-dataset`，成功后展示 `datasetId` 和 `datasetPath`。
- [x] 4.5 实现“保存并下载 .tar.gz”：先保存 Dataset，再请求 `downloadUrl` 触发浏览器下载。
- [x] 4.6 保存失败、validator 失败或打包失败时显示明确错误；保存成功但下载失败时仍显示 registry 信息。
- [x] 4.7 关闭 modal 后保持当前 session、Tasks 页面、task segmentation 和 saved overlay 状态。

## 5. 测试覆盖

- [x] 5.1 新增后端 API 成功测试：请求携带完整 overlay 或 task segmentation payload、provenance、source trace 后，可保存到临时 Dataset Registry，响应包含 `datasetId`、`datasetPath`、`downloadUrl`。
- [x] 5.2 新增后端 API 失败测试：session 不存在返回 404，无 task source payload 返回 400，raw source inclusion 返回 400。
- [x] 5.3 新增 provenance 负向测试：session id 不一致、overlay version 缺失或不受支持、source trace / task boundary 无法对齐时返回 400。
- [x] 5.4 新增 registry 目录结构测试：保存后目录包含 Dataset v1 必需文件，且 validator 通过。
- [x] 5.5 新增 tar.gz 下载测试：下载包根目录为 `ccwhat-dataset/`，内容符合 Dataset v1，validator 通过。
- [x] 5.6 新增前端静态或 DOM 冒烟测试：Tasks 页面存在“保存为 Dataset”入口、modal、保存和保存下载操作。
- [x] 5.7 新增前端状态测试：未加载 session disabled，未切分提示，dirty overlay 阻止，saved overlay 优先，raw source 选项不出现。
- [x] 5.8 新增请求 payload 测试：保存请求包含 source payload、provenance、overlay version 或 source schema version、source trace 信息。
- [x] 5.9 新增或更新测试，确认本 change 不新增 evaluator、CLI 主入口、raw session/req-resp inclusion 或 registry 管理页面。

## 6. 验证与交接

- [x] 6.1 运行 Dataset core 相关测试，确认 builder / validator 仍兼容。
- [x] 6.2 运行 viewer server API 相关测试。
- [x] 6.3 运行前端静态 / DOM 冒烟相关测试。
- [x] 6.4 运行 `openspec validate save-and-export-task-dataset-from-viewer --strict`。
- [x] 6.5 更新实现交接说明，记录 API 请求/响应、source payload/provenance 校验、registry 路径、downloadUrl、raw 选项完全隐藏和 raw inclusion 请求返回 400 的口径。

## 7. Review 返修项

- [x] 7.1 后端 raw inclusion 拒绝逻辑必须覆盖显式真值请求，不只覆盖 JSON boolean `true`；例如 `includeRawSession: "true"`、`includeReqResp: "true"` 或其他可被视为启用 raw inclusion 的值，都必须返回 HTTP 400 且不得落盘。
- [x] 7.2 新增后端负向测试，分别覆盖 `includeRawSession` / `includeReqResp` 以字符串 `"true"` 或等价显式启用值提交时返回 400，并确认 registry 未创建 Dataset。
