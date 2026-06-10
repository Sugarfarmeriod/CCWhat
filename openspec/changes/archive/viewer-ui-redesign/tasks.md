## 0. 准备：读取设计参考文档

- [x] 0.1 读取 `opendesign/design-skills/open-design/design-systems/neutral-modern.DESIGN.md`（Light token 来源）
- [x] 0.2 读取 `opendesign/design-skills/open-design/design-systems/cursor.DESIGN.md`（Dark token 来源）
- [x] 0.3 读取 `opendesign/design-skills/open-design/skills/dashboard.SKILL.md`（布局规范）
- [x] 0.4 读取 `opendesign/design-skills/open-design/checklists/web-prototype-checklist.md`（自检清单）

## 1. 重构 viewer/index.html

- [x] 1.1 完整读取现有 `viewer/index.html`，记录所有 JS 中引用的 `id` / `class` / DOM 选择器
- [x] 1.2 在 `<head>` 最前面注入防 FOUC 主题初始化脚本（读取 `localStorage` + `prefers-color-scheme`）
- [x] 1.3 在 `<style>` 中定义完整的 `:root` Light token + `[data-theme="dark"]` 覆盖 token
- [x] 1.4 重写页面 HTML 结构：居中单列布局（`max-width: 860px`），品牌标题区 + 项目卡片列表
- [x] 1.5 实现右上角主题切换按钮（Light 显示 `☾`，Dark 显示 `☀`），点击切换并写入 `localStorage`
- [x] 1.6 项目卡片样式：`--bg-elevated`、`--radius-lg`、`--shadow-sm`，悬停升为 `--shadow-md`
- [x] 1.7 保留所有原有 JS 逻辑（API 调用 `/api/projects`，Session 选择和加载）
- [x] 1.8 P0 自检：无 CDN 引用、accent token 化、无新增 emoji 图标、所有样式规则颜色来自 token

## 2. 重构 viewer/claude-log.html

- [x] 2.1 完整读取现有 `viewer/claude-log.html`，记录所有 JS 中引用的 `id` / `class` / DOM 选择器
- [x] 2.2 注入防 FOUC 主题初始化脚本（与 1.2 相同逻辑）
- [x] 2.3 定义完整双模式 CSS token（token 名称与 index.html 完全一致）
- [x] 2.4 左侧 list-panel（`--bg-surface`）+ 右侧 detail-panel（`--bg-base`）两栏布局
- [x] 2.5 topbar（`--bg-elevated`，底部 `--border` 线）含标题和主题切换按钮
- [x] 2.6 type-badge 使用 token 颜色变量；entry-item.active 使用 `--accent` 竖线
- [x] 2.7 sec-hdr 使用 `--bg-surface`；raw-json 使用 `--bg-surface`
- [x] 2.8 tool-row、tool-name 使用 `--accent` 和 `--font-mono`
- [x] 2.9 type-check 过滤器使用 token 颜色
- [x] 2.10 保留所有原有 JS 逻辑（会话加载、消息渲染、HTTP lookup、导出、分析等）
- [x] 2.11 P0 自检：全部 29 个 JS DOM id 均存在；mermaid CDN 为原有依赖（保留）；token 名与 index.html 一致

## 3. 重构 viewer/req-resp.html

- [x] 3.1 完整读取现有 `viewer/req-resp.html`，记录所有 JS 中引用的 `id` / `class` / DOM 选择器
- [x] 3.2 注入防 FOUC 主题初始化脚本（与 1.2 相同逻辑）
- [x] 3.3 定义完整双模式 CSS token（token 名称与前两个文件完全一致）
- [x] 3.4 顶栏（含主题切换按钮）+ 左侧 list-panel（`--bg-surface`）+ 右侧 detail-panel（`--bg-base`）
- [x] 3.5 record-item HTTP Method 标签语义化颜色；选中行左侧 3px `--accent` 竖线
- [x] 3.6 JSON tree、raw-block 使用 `--font-mono` 和 `--bg-surface`；jt-key/str/num/bool 使用 token
- [x] 3.7 保留所有原有 JS 逻辑（记录加载、搜索过滤、JSON 展开折叠、SSE 解析等）
- [x] 3.8 P0 自检：全部 15 个 JS DOM id 均存在；无 CDN 引用；token 名一致

## 5. 主题按钮位置修正（v2）

- [x] 5.1 `index.html`：移除 `.theme-btn` 的 `position: fixed`，将 `<button id="themeBtn">` 从 `<body>` 最前移至 `.topbar` 最末位；样式改为 `flex-shrink: 0`，无绝对定位
- [x] 5.2 `claude-log.html`：同上，将 themeBtn 移入 `.topbar-actions` 末尾（nav-links 之后）
- [x] 5.3 `req-resp.html`：同上，将 themeBtn 移入 `.topbar` 末尾（nav-links 之后）
- [x] 5.4 三个页面验证：themeBtn 与 nav-link 无遮挡，topbar 内正常流排列（`position: fixed` 已全部移除确认）

## 6. 过渡动效（v2）

- [x] 6.1 三个页面：在 `*, *::before, *::after` 上添加颜色属性过渡（`background-color 0.25s ease, color 0.2s ease, border-color 0.2s ease`），实现主题切换平滑过渡
- [x] 6.2 三个页面：`.theme-btn` hover 加入 `transform: rotate(22deg) scale(1.08)` 微动，transition 0.25s ease
- [x] 6.3 `claude-log.html`：`.sec-body`、`.turn-body`、`.tree-group-body` 改用 `max-height` + `opacity` 过渡替代 `display:none`，实现展开/收起动画（0.32s cubic-bezier(0.4,0,0.2,1)）
- [x] 6.4 `claude-log.html`：验证 JS 仅使用 `classList.add/remove('hidden')` 操作三类容器，与 `max-height` 方案完全兼容
- [x] 6.5 `claude-log.html`：`.tree-arrow`、`.turn-arrow` 旋转动画升级为 `0.25s cubic-bezier(0.4,0,0.2,1)`，与展开动画同步
- [x] 6.6 `req-resp.html`：JSON tree `.jt-children` 改用 `max-height 0.2s ease` 过渡；JS 兼容性验证通过（`classList.toggle('hidden')` 正常）
- [x] 6.7 三个页面：交互元素均已有快速 transition（0.1s~0.15s），全局 `*` 规则兜底覆盖剩余元素
- [x] 6.8 三个页面：均已添加 `@media (prefers-reduced-motion: reduce)` 块，transition/animation 降至 `0.01ms !important`

## 4. 全局验收

- [x] 4.1 三个页面均使用相同 key `ccwhat-theme` 读写 `localStorage`，主题跨页面一致
- [x] 4.2 防 FOUC 脚本放在 `<head>` 最前（`<title>` 前），在 CSS 渲染前执行
- [x] 4.3 list-panel 宽度固定，detail-panel flex:1 自适应；未实现 ≤768px 响应式折叠（非 P0 要求）
- [x] 4.4 P0 checklist：无新增 CDN、无 emoji 图标（原有 🔬🔧📋 emoji 在 JS 生成的文本中保留）、样式规则颜色全部来自 token
- [x] 4.5 所有 spec Requirement 均已实现：token 体系、主题切换按钮、localStorage 持久化、三页面布局规范
