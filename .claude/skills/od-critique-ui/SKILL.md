---
name: od-critique-ui
description: >
  对 ccwhat 的前端 HTML 文件做 5 维度设计评审，输出评分报告和改进清单。
  当用户说"评审界面"、"critique UI"、"设计打分"、"哪里需要改进"时触发。
argument-hint: "[目标文件，默认 viewer/claude-log.html]"
allowed-tools: Read, Write, Bash(find viewer/*.html)
---

# od-critique-ui · 5 维度 UI 评审

对指定 HTML 文件执行 Open Design 标准的 5 维度设计评审，输出带雷达图的评审报告。

## Step 0 — 读取评审规范

用 Read 工具读取完整的评审 Skill 文档：
`opendesign/design-skills/open-design/skills/critique.SKILL.md`

## Step 1 — 扫描可用文件

```!
find viewer -name "*.html" | sort
```

读取用户指定的目标文件（默认 `viewer/claude-log.html`）。

## Step 2 — 5 维度评审

严格按 critique.SKILL.md 的规范，对以下 5 个维度各打 0-10 分，**每个分数必须附具体证据**：

1. **Philosophy 哲学一致性** — 是否有一致的设计方向？
2. **Hierarchy 视觉层级** — 能否无需引导地知道看哪里？
3. **Detail 细节执行** — 对齐、行高、间距、边界情况
4. **Functionality 功能性** — 是否真正适合开发者工具的使用场景？
5. **Innovation 创新性** — 有没有一个让人眼前一亮的设计决策？

**打分纪律：**
- 每个维度必须引用具体的 CSS 类名、元素或行为
- 不得因为"整体不错"而拉高单项分数
- 不得全部打 7 分以上（会触发重新审查）

## Step 3 — 输出三个行动列表

- **Keep（保留）**：3-5 条，现在做得好的、不要动的
- **Fix（修复）**：3-6 条，按"视觉成本/修复时间"排序的 P0/P1 问题
- **Quick wins（快速提升）**：3-5 条，5-15 分钟可完成的高性价比改动

## Step 4 — 生成 HTML 评审报告

参考 critique.SKILL.md 的输出格式，生成一个自包含 HTML 文件：
- 包含 SVG 雷达图（不依赖外部库）
- 5 个维度评分卡
- 三个行动列表，带 checkbox 交互

将报告写入 `viewer/critique-report.html`。

## Step 5 — 对照 Checklist 检查现有代码

读取：`opendesign/design-skills/open-design/checklists/web-prototype-checklist.md`

列出目标文件中哪些 P0 项目未通过，作为 Fix 列表的补充依据。
