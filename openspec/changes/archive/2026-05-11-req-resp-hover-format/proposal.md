## Why

`req-resp.html` 当前展示原始请求和响应数据时，长字符串（如 message content、system prompt、tool input/output）只能以纯文本形式查看，无法快速判断内容类型（JSON 还是 Markdown），也无法美化浏览。用户需要手动复制到外部工具格式化，体验差。

## What Changes

- 在 `req-resp.html` 的 JSON tree 视图中，对字符串类型的叶子节点（leaf value）增加 hover 交互：
  - 字符串长度超过阈值（如 80 字符）时，hover 显示一个格式化按钮
  - 点击后弹出浮层（overlay/modal），根据内容自动选择渲染模式：
    - 若内容能解析为合法 JSON → 展示格式化 JSON（syntax highlight + 可折叠树）
    - 否则 → 展示 Markdown 渲染结果（复用现有 `.md-view` 样式）
  - 浮层支持关闭（点击遮罩或按 Esc）

## Capabilities

### New Capabilities

- `string-value-hover-format`: JSON tree 中长字符串 hover 显示格式化按钮，点击弹出 Markdown/JSON 浮层

### Modified Capabilities

（无）

## Impact

- 修改 `viewer/req-resp.html`：
  - `renderJsonTree()` / `jt-str` 节点增加 hover 按钮注入逻辑
  - 新增 overlay CSS 和 `showFormatOverlay(str)` 函数
  - 无新依赖，无后端变更
