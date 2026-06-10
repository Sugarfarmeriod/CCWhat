## Context

ccwhat 的三个 Viewer 页面当前样式零散、无设计系统支撑。本次改造纯前端视觉层，所有 JS 业务逻辑保持不变。设计参考来源已内置在项目中：`opendesign/design-skills/open-design/`。

## Goals / Non-Goals

**Goals:**
- 为三个页面建立统一 CSS token 体系
- Light 模式参考 Apple 官网（`neutral-modern.DESIGN.md` + Apple 系统字体栈）
- Dark 模式参考 Codex Mac App（`cursor.DESIGN.md` 深色方案）
- 新增跟随系统 + 可手动覆盖的 Light/Dark 切换，偏好持久化到 `localStorage`
- 使用 `od-design-ui` skill 驱动实际重构

**Non-Goals:**
- 不修改任何 Python 后端代码
- 不修改任何 JS 业务逻辑（API 调用、数据渲染、导出导入）
- 不引入外部 CSS 框架、字体 CDN、图标库
- 不改变页面的 URL 结构和路由

## Decisions

### 1. Token 注入方式：`<html data-theme>` + CSS 变量

在 `<html>` 标签上设置 `data-theme="light"` 或 `data-theme="dark"`，用 CSS 属性选择器切换两套 token：

```css
:root { /* light 默认值 */ }
[data-theme="dark"] { /* 覆盖为 dark 值 */ }
```

这样无需 JS 动态修改任何样式，切换主题只需改一个属性，CSS 过渡动画自然生效。

### 2. 三个页面各自自包含，不共享外部 CSS 文件

现有架构是 `viewer/server.py` 静态服务 HTML 文件，引入外部 CSS 文件需要修改服务端路由。为保持 Non-Goals 约束，每个 HTML 的 `<style>` 块包含完整的 token 定义和页面样式。三个文件的 token 名完全相同，便于维护一致性。

### 3. 主题切换脚本放在 `<head>` 最前面，防止 FOUC

```html
<script>
  (function() {
    const stored = localStorage.getItem('ccwhat-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute(
      'data-theme',
      stored || (prefersDark ? 'dark' : 'light')
    );
  })();
</script>
```

此脚本在任何 CSS 渲染前执行，避免深浅色闪烁（FOUC）。

### 4. 设计参考文件读取策略

执行时，`od-design-ui` skill 将读取：
- `opendesign/design-skills/open-design/design-systems/neutral-modern.DESIGN.md`（Light token 来源）
- `opendesign/design-skills/open-design/design-systems/cursor.DESIGN.md`（Dark token 来源）
- `opendesign/design-skills/open-design/skills/dashboard.SKILL.md`（整体布局规范）
- `opendesign/design-skills/open-design/checklists/web-prototype-checklist.md`（自检）

### 5. 各页面布局核心结构

**index.html**
```
<body>
  [右上角] 主题切换按钮
  <main class="container">
    <header> 品牌标题 + 副标题 </header>
    <section class="project-list">
      <div class="project-card"> 项目名 + Session 列表 </div>
      ...
    </section>
  </main>
</body>
```

**claude-log.html**
```
<body>
  <aside class="sidebar"> 会话选择 + 统计 </aside>
  <main class="log-main">
    <header class="topbar"> 标题 + [主题切换按钮] </header>
    <div class="messages"> 消息气泡区 </div>
  </main>
</body>
```

**req-resp.html**
```
<body>
  <header class="topbar"> 搜索栏 + [主题切换按钮] </header>
  <div class="split-view">
    <aside class="req-list"> 请求列表 </aside>
    <main class="req-detail"> Request/Response 标签面板 </main>
  </div>
</body>
```

### 6. 保留现有 JS 的策略

重写过程中：
1. 先完整读取原始 HTML 文件
2. 提取所有 `<script>` 标签内容，原样保留
3. 仅重写 `<style>` 和 HTML 结构（class 名可以变，但功能性 `id` 和 `data-*` 属性保留）
4. 功能性 JS 依赖的 DOM 选择器（`getElementById`、`querySelector` 等）保持兼容

### 7. 主题切换按钮位置修正（v2）

当前实现将 `.theme-btn` 设为 `position: fixed; top: 10px; right: 12px`，与三个页面 topbar 右侧的导航链接（`Raw Req/Resp` / `Claude Log`）在视觉上产生遮挡。

**修正方案：将主题按钮移入 topbar，作为普通流元素放在最右侧。**

- 移除 `position: fixed` 和 `top/right` 定位
- 按钮本身改为 `flex-shrink: 0`，在 topbar 末尾通过 `margin-left: auto`（或 flex 布局末位）自然靠右
- 三个页面 topbar HTML 结构均需将 `<button id="themeBtn">` 从 `<body>` 最前移入 `.topbar` 最末位

具体每个页面的 topbar 结构：

**index.html** — topbar 末尾追加按钮：
```html
<div class="topbar">
  ... [原有控件] ...
  <button class="theme-btn" id="themeBtn">☾</button>
</div>
```

**claude-log.html** — topbar-actions 末尾追加：
```html
<div class="topbar-actions">
  ... [原有按钮 / nav-links] ...
  <button class="theme-btn" id="themeBtn">☾</button>
</div>
```

**req-resp.html** — topbar 末尾 nav-links 之后追加：
```html
<div class="topbar">
  ... [原有控件 + nav-links] ...
  <button class="theme-btn" id="themeBtn">☾</button>
</div>
```

### 8. 动效设计（v2）

补充以下六类过渡动画，全部使用 CSS，不引入 JS 动画库：

**① 主题切换全局过渡**
```css
*, *::before, *::after {
  transition: background-color 0.25s ease, color 0.2s ease,
              border-color 0.2s ease, box-shadow 0.2s ease;
}
```
注意：`transition: all` 会影响 transform/width 等会引起 layout thrash 的属性，应只声明颜色相关属性。

**② 主题按钮 hover 微动**
```css
.theme-btn { transition: background 0.2s, border-color 0.2s, transform 0.25s ease; }
.theme-btn:hover { transform: rotate(22deg) scale(1.08); }
```
深浅色各有意义：月亮 hover 时微微旋转，太阳 hover 时同样旋转——符合天体转动的直觉。

**③ 折叠/展开区块：高度动画（claude-log.html 的 sec-body、turn-body、tree-group-body）**

纯 CSS `max-height` 过渡方案（无需 JS 测量真实高度）：
```css
.sec-body, .turn-body, .tree-group-body {
  overflow: hidden;
  max-height: 4000px;
  transition: max-height 0.32s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.25s ease;
  opacity: 1;
}
.sec-body.hidden, .turn-body.hidden, .tree-group-body.hidden {
  max-height: 0;
  opacity: 0;
}
```
`cubic-bezier(0.4, 0, 0.2, 1)` 是 Material Design 的标准 easing，展开快、收起带缓冲，符合"流线型"感受。

**④ 折叠箭头旋转**
```css
.tree-arrow, .turn-arrow, .sec-toggle-icon {
  display: inline-block;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.tree-arrow.open, .turn-arrow.open { transform: rotate(90deg); }
```
箭头旋转与内容展开同步，动作一致。

**⑤ 列表项 hover 背景过渡**
```css
.entry-item, .record-item, .turn-hdr, .turn-child {
  transition: background-color 0.15s ease;
}
```
快速响应，避免 hover 感觉迟钝。

**⑥ 按钮 / 链接 hover**
```css
.btn, .adv-btn, .btn-secondary, .btn-export, .nav-link {
  transition: background-color 0.15s ease, color 0.15s ease,
              border-color 0.15s ease, opacity 0.15s ease;
}
```

**动效约束（不能破坏 `prefers-reduced-motion`）：**
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
```

## Risks / Trade-offs

- [Risk] JS 中硬编码了某些 class 名做样式操作 → Mitigation: 读取原文件时检查 JS 中所有 DOM 操作，保留被 JS 引用的 class/id
- [Risk] 三个文件 token 定义手动同步可能出现漂移 → Mitigation: tasks.md 要求每个文件写完后对照 spec 检查 token 名称

## Migration Plan

1. 读取 `od-design-ui` skill + 设计参考文档
2. 依次重构 `index.html` → `claude-log.html` → `req-resp.html`
3. 每个文件重构完成后：
   - 对照 `web-prototype-checklist.md` P0 自检
   - 检查 JS 中引用的 DOM 选择器是否仍然有效
4. 全部完成后，目视验证 Light/Dark 切换在三个页面的一致性
