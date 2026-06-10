## Context

`req-resp.html` 使用 `renderJsonTree(obj, depth)` 递归构建 DOM 树。字符串叶子节点渲染为 `<span class="jt-str">"…"</span>`。当前没有 hover 交互，也没有 overlay 基础设施。

## Goals / Non-Goals

**Goals:**
- 字符串长度 ≥ 80 字符时，hover 显示"格式化"按钮（📋 图标或文字）
- 点击弹出全屏遮罩浮层，自动判断内容类型并渲染
- 浮层内：JSON 内容用现有 `renderJsonTree` 展示；非 JSON 用 `renderMarkdown` 展示
- 按 Esc 或点击遮罩背景关闭浮层

**Non-Goals:**
- 不改变现有 JSON tree 折叠/展开逻辑
- 不在 SSE raw 事件区域添加此功能（字符串太短且格式固定）
- 不提供编辑功能

## Decisions

**hover 按钮注入方式：** 在 `renderJsonTree` 渲染 `jt-str` 节点时，若字符串长度 ≥ 80，在 span 后附加一个 `<button class="fmt-btn">` 并默认隐藏（`opacity:0`）。父 `.jt-row` 添加 `:hover` CSS 规则使按钮可见。纯 CSS hover，无需 JS 事件监听。

**内容类型判断：** 尝试 `JSON.parse(str)` — 成功则 JSON 模式，失败则 Markdown 模式。

**浮层实现：** 单例 overlay div（`id="fmtOverlay"`），body 级别，点击时复用。内容区固定宽高（max 90vw × 85vh，overflow scroll），标题行显示模式标签和关闭按钮。

**字符串阈值：** 80 字符，硬编码常量 `FMT_MIN_LEN = 80`，便于日后调整。

## Risks / Trade-offs

- [风险] 超大 JSON 字符串（>100KB）调用 `renderJsonTree` 可能卡顿 → 浮层内 JSON 树默认折叠深度 2，比正文浅一级
- [权衡] hover 按钮通过 CSS `:hover` 显示，移动端不可见 — 可接受（此工具仅桌面使用）
