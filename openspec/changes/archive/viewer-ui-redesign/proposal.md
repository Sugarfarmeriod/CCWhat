## Why

ccwhat 的三个 Viewer 页面（index.html、claude-log.html、req-resp.html）当前使用手写的临时样式，视觉层级混乱、缺乏统一设计语言，且没有深色模式支持，不符合开发者工具的审美预期。本次改造在不触碰任何后端逻辑和数据渲染代码的前提下，为三个页面统一引入 Apple / Codex 双模式视觉风格，并新增 Light/Dark 主题切换。

## What Changes

- 为三个 Viewer HTML 文件建立统一的 CSS token 体系（`:root` 变量），覆盖颜色、字体、间距、圆角、阴影
- Light 模式参考 Apple 官网设计语言：大量留白、SF Pro 字体栈、细边框、圆角卡片
- Dark 模式参考 Codex Mac App 设计语言：深色背景、monospace 代码感、高对比强调色
- 新增主题切换按钮（☀ / ☾），固定在所有页面右上角，偏好存入 `localStorage`，默认跟随 `prefers-color-scheme`
- 重写三个页面的布局和视觉层，**保留所有 JavaScript 业务逻辑和 API 调用完整不变**
- 所有页面使用相同的 token 变量名，确保风格完全统一

**补充（v2）：**
- 主题切换按钮当前以 `position: fixed` 悬浮，与 topbar 右侧导航链接（Raw Req/Resp / Claude Log）产生遮挡，需移入 topbar 内作为普通流元素
- 当前页面缺乏动效，展开/折叠、hover、主题切换等交互过于生硬，需补充流线型过渡动画

## Capabilities

### New Capabilities

- `viewer-visual-theme`: 统一的双模式（Light Apple / Dark Codex）视觉主题规范，适用于所有三个 Viewer 页面，包含 token 体系、主题切换行为和三个页面的布局规范

### Modified Capabilities

- `session-viewer`: 前端渲染层的视觉改造（布局、颜色、字体、间距），不改变任何 Requirement 级别的功能行为

## Impact

- 修改文件：`viewer/index.html`、`viewer/claude-log.html`、`viewer/req-resp.html`
- 不修改：`viewer/server.py`、`viewer/__init__.py`、所有后端逻辑
- 不新增依赖：所有样式内联，不引入外部 CSS 框架或 CDN
- 不影响导出/导入功能：HTML 文件的 JS 逻辑完整保留
