## ADDED Requirements

### Requirement: Tasks 页面提供 Dataset 保存入口
Viewer SHALL 在 Tasks 页面为当前 session 提供“保存为 Dataset”入口，用于将已切分 Task 保存为 Task Dataset v1。

#### Scenario: 未加载 session 时入口不可用
- **WHEN** 用户尚未加载 session
- **THEN** “保存为 Dataset”入口 SHALL disabled
- **AND** 页面 SHALL 不发起 Dataset 保存请求

#### Scenario: 未切分 task 时提示先切分
- **WHEN** 用户已加载 session
- **AND** 当前 session 没有 saved Task Trace Overlay
- **AND** 当前 session 没有 task segmentation result
- **THEN** 用户点击“保存为 Dataset” SHALL 看到明确提示先进行任务切分
- **AND** 页面 SHALL NOT 调用 `POST /api/save-task-dataset`

#### Scenario: 有未保存 overlay 时阻止保存
- **WHEN** 当前 session 存在 dirty Task Trace Overlay
- **THEN** 用户点击“保存为 Dataset” SHALL 看到提示先保存或撤销编辑
- **AND** 页面 SHALL NOT 调用 `POST /api/save-task-dataset`

#### Scenario: 有可保存 task source 时打开确认弹窗
- **WHEN** 当前 session 存在 saved Task Trace Overlay 或 task segmentation result
- **AND** 当前 session 没有 dirty overlay
- **THEN** 用户点击“保存为 Dataset” SHALL 打开保存确认 modal

### Requirement: 保存确认 modal 展示 Dataset 范围和内容
Viewer SHALL 在保存确认 modal 中展示本次 Dataset 的范围、必选内容和操作按钮。

#### Scenario: 显示保存范围
- **WHEN** 保存确认 modal 打开
- **THEN** modal SHALL 显示范围为当前 session 的全部 tasks
- **AND** modal SHALL 显示 task 数量

#### Scenario: 显示必选 Dataset 内容
- **WHEN** 保存确认 modal 打开
- **THEN** modal SHALL 显示 `manifest.json`
- **AND** modal SHALL 显示 `dataset.jsonl`
- **AND** modal SHALL 显示 `traces/*.json`
- **AND** modal SHALL 显示 `scores.jsonl` 空文件

#### Scenario: raw sources 选项第一版完全隐藏
- **WHEN** 保存确认 modal 打开
- **THEN** modal SHALL NOT 展示 raw session 选项
- **AND** modal SHALL NOT 展示 raw req/resp 选项
- **AND** modal SHALL NOT 展示不可用 raw source checkbox

#### Scenario: 提供保存和保存下载操作
- **WHEN** 保存确认 modal 打开
- **THEN** modal SHALL 提供“保存 Dataset”操作
- **AND** modal SHALL 提供“保存并下载 .tar.gz”操作
- **AND** modal SHALL 提供取消操作

### Requirement: 后端 API 保存 Task Dataset
Viewer server SHALL 提供 `POST /api/save-task-dataset`，将当前 session 的 task source 构建为 Dataset v1 并保存到本地 Dataset Registry。

#### Scenario: 成功保存 Dataset
- **WHEN** 前端调用 `POST /api/save-task-dataset`
- **AND** 请求包含有效 `sessionId`
- **AND** 请求包含可用 task source payload
- **AND** 请求包含 provenance、overlay version 或 source schema version、source trace 信息
- **THEN** 后端 SHALL 构建 Dataset v1
- **AND** 后端 SHALL 保存到 `~/.ccwhat/datasets/<dataset-id>/`
- **AND** 后端 SHALL 返回 HTTP 200
- **AND** 响应 SHALL 包含 `ok: true`
- **AND** 响应 SHALL 包含 `datasetId`
- **AND** 响应 SHALL 包含 `datasetPath`
- **AND** 响应 SHALL 包含 `downloadUrl`

#### Scenario: Dataset id 命名
- **WHEN** 后端创建 Dataset
- **THEN** `datasetId` SHALL 使用 `dataset-YYYYMMDD-HHMMSS-<session-short-id>` 形式
- **AND** 如果发生目录名冲突，后端 SHALL 生成唯一 `datasetId`

#### Scenario: 保存后校验 Dataset 目录
- **WHEN** Dataset 文件写入完成
- **THEN** 后端 SHALL 使用 Dataset validator 校验保存目录
- **AND** validator 通过后 SHALL 返回成功响应
- **AND** validator 失败时 SHALL 返回 HTTP 500 和可读错误

#### Scenario: session 不存在
- **WHEN** 请求的 `sessionId` 不存在
- **THEN** 后端 SHALL 返回 HTTP 404
- **AND** 响应 SHALL 包含 `ok: false`

#### Scenario: session 尚未切分 task
- **WHEN** 请求的 session 没有可用 task source
- **THEN** 后端 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 包含明确错误信息

#### Scenario: raw sources 请求第一版被拒绝
- **WHEN** 请求中 `includeRawSession` 或 `includeReqResp` 为 `true`
- **THEN** 后端 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 说明 raw source inclusion 不属于当前版本
- **AND** 后端 SHALL NOT warning 后忽略该请求继续保存

#### Scenario: 缺少 provenance 时拒绝保存
- **WHEN** 请求缺少 provenance 信息
- **THEN** 后端 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 说明 Dataset source provenance 缺失

#### Scenario: provenance session 不一致时拒绝保存
- **WHEN** 请求 `sessionId` 与 source payload 或 provenance 中的 session id 不一致
- **THEN** 后端 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 说明 session provenance 不一致

#### Scenario: overlay version 不受支持时拒绝保存
- **WHEN** 请求使用 overlay source
- **AND** overlay payload 缺少 version 或 version 不受支持
- **THEN** 后端 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 说明 overlay version 无效

#### Scenario: source trace 无法对齐时拒绝保存
- **WHEN** 请求 source trace 或 task 边界无法与当前 session normalized events 对齐
- **THEN** 后端 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 说明 source trace 无法校验

### Requirement: task source 选择
Viewer SHALL 使用 saved overlay 优先、task segmentation result 兜底的规则选择保存来源，并在保存请求中发送完整 source payload 与 provenance。

#### Scenario: saved overlay 优先
- **WHEN** 当前 session 同时存在 saved Task Trace Overlay 和 task segmentation result
- **THEN** 保存请求 SHALL 使用 saved Task Trace Overlay 作为 task source
- **AND** 保存请求 SHALL 包含完整 saved overlay payload
- **AND** 保存请求 SHALL 包含 overlay version、provenance 和 source trace 信息

#### Scenario: task segmentation result 兜底
- **WHEN** 当前 session 没有 saved Task Trace Overlay
- **AND** 当前 session 存在 task segmentation result
- **THEN** 保存请求 SHALL 使用 task segmentation result 作为 task source
- **AND** 保存请求 SHALL 包含完整 task segmentation payload
- **AND** 保存请求 SHALL 包含 provenance 和 source trace 信息

#### Scenario: dirty overlay 不参与保存
- **WHEN** 当前 session 存在 dirty Task Trace Overlay
- **THEN** Viewer SHALL 阻止保存
- **AND** dirty overlay SHALL NOT 被静默发送为 Dataset source

#### Scenario: server cache 只作为辅助
- **WHEN** 后端处理 Dataset 保存请求
- **THEN** 后端 SHALL 以请求中的完整 source payload 为主要数据源
- **AND** server cache SHALL 只作为 fallback 或辅助校验
- **AND** server cache SHALL NOT 作为唯一 task source 数据源

### Requirement: source provenance 校验
Viewer server SHALL 在构建 Dataset 前校验 task source payload 的 provenance、版本和来源 trace 信息。

#### Scenario: 校验 overlay payload provenance
- **WHEN** 请求使用 saved overlay source
- **THEN** 后端 SHALL 校验 overlay payload 存在
- **AND** 后端 SHALL 校验 overlay version 受支持
- **AND** 后端 SHALL 校验 provenance 表明 overlay 已保存
- **AND** 后端 SHALL 校验 provenance 的 session id 与请求 session id 一致

#### Scenario: 校验 task segmentation payload provenance
- **WHEN** 请求使用 task segmentation source
- **THEN** 后端 SHALL 校验 task segmentation payload 存在
- **AND** 后端 SHALL 校验 provenance 的 session id 与请求 session id 一致
- **AND** 后端 SHALL 校验 source trace 或 task boundary 能与当前 session 对齐

#### Scenario: Dataset schema 校验是保存前置条件
- **WHEN** 后端使用 source payload 构建 Dataset bundle
- **THEN** 后端 SHALL 使用 Dataset validator 校验 Dataset schema
- **AND** validator 失败时 SHALL NOT 返回保存成功

### Requirement: Dataset Registry 写入
Viewer server SHALL 将保存成功的 Dataset 作为文件集合写入本地 Dataset Registry。

#### Scenario: 写入 registry 目录结构
- **WHEN** Dataset 保存成功
- **THEN** registry SHALL 包含 `~/.ccwhat/datasets/<dataset-id>/manifest.json`
- **AND** registry SHALL 包含 `~/.ccwhat/datasets/<dataset-id>/dataset.jsonl`
- **AND** registry SHALL 包含 `~/.ccwhat/datasets/<dataset-id>/traces/*.json`
- **AND** registry SHALL 包含 `~/.ccwhat/datasets/<dataset-id>/scores.jsonl`

#### Scenario: 不写入 evaluator score
- **WHEN** Dataset 保存成功
- **THEN** `scores.jsonl` SHALL 存在
- **AND** `scores.jsonl` SHALL 为空或不包含自动 evaluator score

#### Scenario: 保存失败不报告成功
- **WHEN** registry 目录创建、文件写入或 validator 校验失败
- **THEN** 后端 SHALL 返回失败响应
- **AND** 前端 SHALL 显示保存失败状态
- **AND** 前端 SHALL NOT 显示保存成功提示

### Requirement: Dataset tar.gz 下载
Viewer SHALL 支持将已保存 Dataset 通过浏览器下载为 `.tar.gz`。

#### Scenario: 保存并下载
- **WHEN** 用户在 modal 中点击“保存并下载 .tar.gz”
- **THEN** Viewer SHALL 先保存 Dataset
- **AND** 保存成功后 SHALL 请求响应中的 `downloadUrl`
- **AND** 浏览器 SHALL 下载 `dataset-*.tar.gz`

#### Scenario: 下载包结构
- **WHEN** 用户下载 Dataset tar.gz
- **THEN** 压缩包内部根目录 SHALL 为 `ccwhat-dataset/`
- **AND** 根目录下 SHALL 包含 `manifest.json`
- **AND** 根目录下 SHALL 包含 `dataset.jsonl`
- **AND** 根目录下 SHALL 包含 `traces/*.json`
- **AND** 根目录下 SHALL 包含 `scores.jsonl`

#### Scenario: 下载包通过 validator
- **WHEN** 后端生成 Dataset tar.gz
- **THEN** 生成的 tar.gz SHALL 能通过 Dataset validator 校验

#### Scenario: 下载失败
- **WHEN** Dataset 打包或下载失败
- **THEN** 前端 SHALL 显示下载失败状态
- **AND** 如果保存已经成功，前端 SHALL 保留并显示 `datasetId` 和 `datasetPath`

### Requirement: 保存成功反馈
Viewer SHALL 在 Dataset 保存成功后向用户展示可复用的 registry 信息。

#### Scenario: 保存成功后展示结果
- **WHEN** Dataset 保存成功
- **THEN** modal 或 Tasks 页面 SHALL 显示 `datasetId`
- **AND** SHALL 显示 `datasetPath`
- **AND** SHALL 显示保存成功状态

#### Scenario: 关闭后不丢失当前页面状态
- **WHEN** 用户关闭保存成功 modal
- **THEN** Viewer SHALL 保持当前 session 和 Tasks 页面上下文
- **AND** SHALL NOT 清空当前 task segmentation 或 saved overlay 状态

### Requirement: 不引入后续阶段能力
Task Dataset Save Export SHALL 不引入 evaluator、raw source inclusion、CLI 主入口或 Dataset Registry 管理页面。

#### Scenario: 不做 evaluator
- **WHEN** Dataset 保存或下载完成
- **THEN** 系统 SHALL NOT 自动运行 evaluator
- **AND** 系统 SHALL NOT 写入非空 evaluator score

#### Scenario: 不包含 raw session 或 req-resp
- **WHEN** Dataset 保存或下载完成
- **THEN** Dataset SHALL NOT 包含原始 session log
- **AND** Dataset SHALL NOT 包含 raw req/resp

#### Scenario: 不新增 CLI 主入口
- **WHEN** 本 change 完成
- **THEN** 系统 SHALL NOT 新增 Dataset save/export 的 CLI 主命令

#### Scenario: 不新增 registry 管理页面
- **WHEN** 本 change 完成
- **THEN** Viewer SHALL NOT 要求提供 Dataset 列表、删除、重命名或管理页面
