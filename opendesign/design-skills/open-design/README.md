# Open Design 前端设计参考文档

从 Open Design App 提取的核心设计规范，供 Claude Code 直接读取参考，用于重构 ccwhat 前端界面。

不需要运行 Open Design App，不需要配置 MCP，直接把这些文件路径告诉 Claude Code 即可。

---

## 目录结构

```
open-design/
├── skills/          # 页面生成 Skill（告诉 Agent 如何构建各类页面）
├── design-systems/  # 设计系统 DESIGN.md（颜色/字体/间距/组件规范）
└── checklists/      # 生成前自检清单（防止 AI 生成丑 UI）
```

---

## Skills — 页面生成指令

| 文件 | 适用场景 | 推荐度 |
|------|---------|--------|
| `dashboard.SKILL.md` | 通用 Admin/Analytics 仪表板，左侧边栏+KPI卡片+图表 | ⭐⭐⭐⭐⭐ **首选** |
| `github-dashboard.SKILL.md` | 开发者工具类仪表板，数据密度高，Soft Paper 风格 | ⭐⭐⭐⭐⭐ **首选** |
| `live-dashboard.SKILL.md` | 实时数据仪表板，含 Notion 风格、活动流、自动刷新 | ⭐⭐⭐⭐ |
| `web-prototype.SKILL.md` | 通用单页 Web 原型，含布局骨架和 8 种 section 模板 | ⭐⭐⭐⭐ |
| `docs-page.SKILL.md` | 三栏文档页（左导航+正文+右侧 TOC） | ⭐⭐⭐ |
| `critique.SKILL.md` | 5 维度设计评审报告（Philosophy/Hierarchy/Detail/Function/Innovation） | ⭐⭐⭐⭐ **评审用** |
| `wireframe-sketch.SKILL.md` | 线框草图，快速验证布局方案 | ⭐⭐ |

**重构 ccwhat 日志观测界面推荐使用：`dashboard.SKILL.md` + `github-dashboard.SKILL.md`**

---

## Design Systems — 设计系统规范

| 文件 | 风格描述 | 适合 CCWhat 程度 |
|------|---------|----------------|
| `neutral-modern.DESIGN.md` | Neutral Modern，B2B 工具默认，浅色，Inter，低装饰 | ⭐⭐⭐⭐⭐ **首选** |
| `cursor.DESIGN.md` | Cursor 风格，开发者工具，深色+渐变强调，现代感强 | ⭐⭐⭐⭐⭐ **首选** |
| `warp.DESIGN.md` | Warp Terminal 风格，深色 IDE 感，块状命令 UI | ⭐⭐⭐⭐ |
| `github.DESIGN.md` | GitHub Primer 风格，功能密度高，蓝白精准 | ⭐⭐⭐⭐ |
| `linear-app.DESIGN.md` | Linear 风格，深色优先，紫色强调，极简精准 | ⭐⭐⭐ |
| `dashboard-dark.DESIGN.md` | 深色云平台风格（Vercel/Heroku 感），玻璃面板 | ⭐⭐⭐ |

**CCWhat 是 Claude Code 日志观测平台（开发者工具），推荐：**
- **浅色方案**：`neutral-modern.DESIGN.md`
- **深色方案**：`cursor.DESIGN.md`

---

## Checklists — 生成前自检清单

| 文件 | 用途 |
|------|-----|
| `web-prototype-checklist.md` | P0/P1/P2 三级自检，防止颜色乱用、emoji 滥用、占位符等 AI 常见丑化问题 |
| `live-dashboard-checklist.md` | 仪表板专项检查：对比度、数据真实性、响应式、动画等 |

**每次生成完前端代码后，让 Claude Code 对照这两份清单做自检。**

---

## 使用方式

在对话中告诉 Claude Code：

```
请读取以下文件作为设计参考：
- opendesign/design-skills/open-design/design-systems/neutral-modern.DESIGN.md （设计系统）
- opendesign/design-skills/open-design/skills/dashboard.SKILL.md （页面结构规范）
- opendesign/design-skills/open-design/checklists/web-prototype-checklist.md （自检清单）

然后按照这些规范重构 viewer/claude-log.html
```
