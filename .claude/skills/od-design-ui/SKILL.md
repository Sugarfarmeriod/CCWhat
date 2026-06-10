---
name: od-design-ui
description: >
  重构或新建 ccwhat 前端界面（viewer/*.html）。
  自动读取 Open Design 设计规范，输出符合开发者工具审美的单文件 HTML。
  当用户说"重构前端"、"重新设计界面"、"改进 UI"、"用 Open Design 风格重写"时触发。
argument-hint: "[目标文件] [设计系统: cursor|neutral|warp|github] [页面类型: dashboard|prototype|docs]"
allowed-tools: Read, Edit, Write, Bash(find * )
---

# od-design-ui · ccwhat 前端界面重构

你是一名擅长开发者工具界面设计的前端工程师。在动手之前，**必须先读完所有参考文档**，再开始写任何代码。

## Step 0 — 读取设计规范（必须，每次都执行）

根据用户指定的设计系统（默认 `cursor`），读取对应文件：

```!
echo "=== 可用设计系统 ===" && ls opendesign/design-skills/open-design/design-systems/
```

**按用户选择读取对应 DESIGN.md（默认 cursor）：**
- `cursor` → `opendesign/design-skills/open-design/design-systems/cursor.DESIGN.md`
- `neutral` → `opendesign/design-skills/open-design/design-systems/neutral-modern.DESIGN.md`
- `warp` → `opendesign/design-skills/open-design/design-systems/warp.DESIGN.md`
- `github` → `opendesign/design-skills/open-design/design-systems/github.DESIGN.md`
- `linear` → `opendesign/design-skills/open-design/design-systems/linear-app.DESIGN.md`

用 Read 工具读取选定的 DESIGN.md 文件（完整读取，不要截断）。

**按页面类型读取对应 SKILL.md（默认 dashboard）：**
- `dashboard` → `opendesign/design-skills/open-design/skills/dashboard.SKILL.md`
- `prototype` → `opendesign/design-skills/open-design/skills/web-prototype.SKILL.md`
- `github-dashboard` → `opendesign/design-skills/open-design/skills/github-dashboard.SKILL.md`
- `docs` → `opendesign/design-skills/open-design/skills/docs-page.SKILL.md`

用 Read 工具读取选定的 SKILL.md（完整读取）。

## Step 1 — 读取当前目标文件

用 Read 工具读取用户指定的目标 HTML 文件（例如 `viewer/claude-log.html`）。
理解当前页面的结构、功能、API 调用方式，**不得删除任何业务逻辑**。

## Step 2 — 确认方向（可选，复杂改动时使用）

如果改动范围较大，用 AskUserQuestion 快速确认：
- 深色还是浅色模式
- 保留哪些现有布局，重构哪些部分
- 有无特别的交互需求

## Step 3 — 按 SKILL.md 规范重构

严格遵守读取的 SKILL.md 和 DESIGN.md，执行以下规则：

**必须遵守：**
- 所有颜色来自 DESIGN.md 的 token，不得发明新的 hex 值
- 字体、间距、圆角全部使用 DESIGN.md 中定义的值
- 输出**单一自包含 HTML 文件**，所有 CSS 内联在 `<style>` 中，不引用外部 CDN
- 保留现有的所有 JavaScript 业务逻辑（API 调用、数据渲染等）
- 在每个主要区块上加 `data-od-id` 属性

**布局参考（dashboard 类型）：**
- 左侧边栏：固定宽度，项目/会话选择器
- 顶部栏：页面标题 + 操作按钮
- 主内容区：会话内容渲染
- 响应式：≤920px 时边栏折叠

## Step 4 — 对照 Checklist 自检

读取并逐项检查：`opendesign/design-skills/open-design/checklists/web-prototype-checklist.md`

P0 项目全部通过后才能写入文件。

**快速 anti-slop 检查：**
- [ ] 没有 emoji 用作功能图标
- [ ] 没有 placeholder 文案（Feature One / Lorem ipsum）
- [ ] accent 颜色全页不超过 2 处
- [ ] 没有从 CDN 引入任何外部资源
- [ ] 所有颜色都是 DESIGN.md 中定义的 token

## Step 5 — 写入文件

通过 Write 工具写入目标文件。写入前告知用户：
- 使用的设计系统
- 主要改动了哪些部分
- 保留了哪些原有功能

---

## 可用的设计系统和 Skill 文档位置

所有文档在 `opendesign/design-skills/open-design/` 下：

```
design-systems/
  cursor.DESIGN.md          # 开发者工具深色，渐变强调 ← ccwhat 首选深色
  neutral-modern.DESIGN.md  # B2B 工具浅色，Inter，低装饰 ← ccwhat 首选浅色
  warp.DESIGN.md             # Terminal/IDE 深色风格
  github.DESIGN.md           # Primer 体系，功能密度高
  linear-app.DESIGN.md       # 极简深色，紫色强调
  dashboard-dark.DESIGN.md   # 云平台深色，玻璃面板

skills/
  dashboard.SKILL.md         # 仪表板：左边栏+KPI+图表 ← 首选
  github-dashboard.SKILL.md  # 开发者仪表板，数据密度高
  web-prototype.SKILL.md     # 通用 Web 页面，8 种 section 骨架
  docs-page.SKILL.md         # 三栏文档页
  live-dashboard.SKILL.md    # 实时仪表板，Notion 风格
```
