## 1. CSS 样式

- [x] 1.1 添加 `.fmt-btn` 样式：默认 `opacity:0`，小图标按钮，`pointer-events:none`
- [x] 1.2 添加 `.jt-row:hover .fmt-btn` 规则：`opacity:1; pointer-events:auto`
- [x] 1.3 添加 `#fmtOverlay` 遮罩样式：全屏半透明背景，居中内容卡片
- [x] 1.4 添加浮层内容卡片样式：max 90vw × 85vh，overflow scroll，标题栏+关闭按钮

## 2. 格式化浮层逻辑

- [x] 2.1 在 `<body>` 末尾添加 `<div id="fmtOverlay">` 单例 DOM，初始 `display:none`
- [x] 2.2 实现 `showFormatOverlay(str)` 函数：尝试 JSON.parse，成功则 JSON 模式，失败则 Markdown 模式
- [x] 2.3 JSON 模式：调用 `renderJsonTree(parsed, 0, 2)` 渲染（默认展开深度 2），设标题"JSON"
- [x] 2.4 Markdown 模式：调用 `renderMarkdown(str)` 渲染，设标题"Markdown"
- [x] 2.5 实现 `closeFormatOverlay()` 函数，隐藏浮层
- [x] 2.6 绑定遮罩背景点击关闭、Esc 键关闭事件

## 3. JSON tree 注入格式化按钮

- [x] 3.1 在 `renderJsonTree` 渲染字符串叶子节点时，若 `str.length >= 80`，在 `.jt-row` 内附加 `<button class="fmt-btn">` 
- [x] 3.2 按钮 onclick 调用 `showFormatOverlay(str)`，并阻止事件冒泡

## 4. 验证

- [x] 4.1 打开 req-resp.html，选择含长字符串的记录，hover 字符串节点确认按钮出现/消失
- [x] 4.2 点击按钮：JSON 内容展示 JSON 树，非 JSON 内容展示 Markdown
- [x] 4.3 Esc 和点击遮罩能关闭浮层
