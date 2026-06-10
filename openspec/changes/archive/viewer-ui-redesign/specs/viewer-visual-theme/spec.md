# viewer-visual-theme Specification

## Purpose

为 ccwhat 的三个 Viewer 页面（index.html、claude-log.html、req-resp.html）定义统一的双模式视觉主题规范。Light 模式参考 Apple 官网设计语言，Dark 模式参考 Codex Mac App 设计语言。

## Requirements

### Requirement: CSS Token 体系

所有三个页面 SHALL 在 `<style>` 块内的 `:root` 中定义相同名称的 CSS 自定义属性（token），涵盖颜色、字体、间距、圆角、阴影六个维度。

#### Scenario: Light 模式 token 值

- **WHEN** `[data-theme="light"]` 或系统为浅色且无手动覆盖
- **THEN** 使用以下 token 值（Apple 风格）：

```css
--bg-base:      #ffffff;
--bg-surface:   #f5f5f7;
--bg-elevated:  #ffffff;
--border:       rgba(0,0,0,0.08);
--border-strong: rgba(0,0,0,0.15);
--text-primary: #1d1d1f;
--text-secondary: #6e6e73;
--text-tertiary: #aeaeb2;
--accent:       #0071e3;
--accent-hover: #0077ed;
--success:      #30d158;
--warning:      #ff9f0a;
--danger:       #ff3b30;
--font-sans:    -apple-system, "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
--font-mono:    "SF Mono", ui-monospace, "Cascadia Code", monospace;
--radius-sm:    6px;
--radius-md:    10px;
--radius-lg:    14px;
--shadow-sm:    0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
--shadow-md:    0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04);
```

#### Scenario: Dark 模式 token 值

- **WHEN** `[data-theme="dark"]` 或系统为深色且无手动覆盖
- **THEN** 使用以下 token 值（Codex 风格）：

```css
--bg-base:      #0d0d0d;
--bg-surface:   #161616;
--bg-elevated:  #1e1e1e;
--border:       rgba(255,255,255,0.08);
--border-strong: rgba(255,255,255,0.15);
--text-primary: #f0f0f0;
--text-secondary: #8a8a8a;
--text-tertiary: #555555;
--accent:       #57b5ff;
--accent-hover: #7ac4ff;
--success:      #30d158;
--warning:      #ff9f0a;
--danger:       #ff453a;
--font-sans:    -apple-system, "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
--font-mono:    "SF Mono", ui-monospace, "Cascadia Code", monospace;
--radius-sm:    6px;
--radius-md:    10px;
--radius-lg:    14px;
--shadow-sm:    0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
--shadow-md:    0 4px 16px rgba(0,0,0,0.4), 0 1px 4px rgba(0,0,0,0.3);
```

---

### Requirement: 主题切换按钮

所有三个页面 SHALL 在右上角提供一个主题切换按钮。

#### Scenario: 按钮外观

- **WHEN** 页面渲染
- **THEN** 右上角固定位置显示一个圆形图标按钮：Light 模式显示 `☾`（切换到 Dark），Dark 模式显示 `☀`（切换到 Light）

#### Scenario: 切换行为

- **WHEN** 用户点击主题切换按钮
- **THEN** 立即切换 `<html>` 的 `data-theme` 属性，并将选择写入 `localStorage`（key: `ccwhat-theme`）

#### Scenario: 初始化优先级

- **WHEN** 页面加载
- **THEN** 按以下优先级确定初始主题：
  1. `localStorage` 中有 `ccwhat-theme` 值 → 使用该值
  2. 否则 → 读取 `window.matchMedia('(prefers-color-scheme: dark)')` 结果
  3. 三个页面使用相同的初始化逻辑，保证跨页面一致

#### Scenario: 跨页面一致性

- **WHEN** 用户在 index.html 切换主题后导航到 claude-log.html
- **THEN** claude-log.html 读取 `localStorage` 并应用相同主题，无闪烁

---

### Requirement: index.html 布局规范

#### Scenario: 整体布局

- **WHEN** 渲染 index.html
- **THEN** 采用居中单列布局（`max-width: 860px`），顶部有品牌标题区，下方为项目列表卡片区

#### Scenario: 项目卡片

- **WHEN** 渲染项目列表
- **THEN** 每个项目显示为独立卡片（`--bg-elevated`，`--radius-lg`，`--shadow-sm`），内含项目名称、会话数量、最近会话时间；悬停时 `--shadow-md`

#### Scenario: Session 选择器

- **WHEN** 用户点击展开项目
- **THEN** 会话列表以列表形式展开在卡片内，每行显示 Session ID（截断显示）和时间戳；选中行高亮为 `--accent`

---

### Requirement: claude-log.html 布局规范

#### Scenario: 整体布局

- **WHEN** 渲染 claude-log.html
- **THEN** 采用两栏布局：左侧固定宽度侧边栏（240px，`--bg-surface`）显示会话选择器和统计信息；右侧主内容区（`--bg-base`）渲染对话

#### Scenario: 消息气泡

- **WHEN** 渲染 user 消息
- **THEN** 右对齐气泡，背景 `--accent`，文字白色，`--radius-lg`，`max-width: 72%`

- **WHEN** 渲染 assistant 消息
- **THEN** 左对齐，背景 `--bg-elevated`，边框 `--border`，`--radius-lg`，`max-width: 88%`

#### Scenario: 工具调用展示

- **WHEN** 渲染 tool call
- **THEN** 使用 `--font-mono`，背景 `--bg-surface`，左侧 3px `--accent` 色竖线，折叠/展开动画

#### Scenario: Subagent 标签页

- **WHEN** 有多个 subagent
- **THEN** 顶部标签页样式，激活标签底部 2px `--accent` 线条

---

### Requirement: req-resp.html 布局规范

#### Scenario: 整体布局

- **WHEN** 渲染 req-resp.html
- **THEN** 顶部固定搜索/筛选栏（`--bg-elevated`，`--border` 底部线），下方为请求列表（左 35%）+ 详情面板（右 65%）分栏

#### Scenario: 请求列表项

- **WHEN** 渲染每条请求记录
- **THEN** 显示 HTTP 方法标签（GET 蓝、POST 绿、其他灰，全部用 `--accent` 体系色）、URL 截断、时间戳；选中项背景 `--bg-surface`，左侧 3px `--accent` 竖线

#### Scenario: 详情面板

- **WHEN** 选中一条请求
- **THEN** 右侧面板分 Request / Response 两个标签，JSON 内容使用 `--font-mono` 渲染，关键字段高亮

---

### Requirement: 排版规范

所有页面 SHALL 遵守以下排版规则。

#### Scenario: 字体层级

- **THEN** 页面标题：`--font-sans`，weight 700，letter-spacing -0.02em
- **THEN** 正文：`--font-sans`，weight 400，line-height 1.6
- **THEN** 代码/工具调用内容：`--font-mono`，size 13px
- **THEN** 辅助信息（时间戳、计数）：`--text-secondary`，size 12px

#### Scenario: 禁止事项

- **THEN** 不使用纯黑（`#000000`）或纯白（`#ffffff`）作为背景色
- **THEN** 不使用超过 2 种 accent 颜色
- **THEN** 不引入任何外部 CSS 框架、字体 CDN 或图标库
- **THEN** 不使用 emoji 作为功能性图标

---

### Requirement: 主题切换按钮位置（v2）

主题切换按钮 SHALL 作为 topbar 内的普通流元素，不得使用 `position: fixed` 悬浮在页面上方。

#### Scenario: 按钮在 topbar 内

- **WHEN** 三个页面渲染 topbar
- **THEN** `#themeBtn` 作为 topbar 的最后一个子元素存在，靠右对齐
- **THEN** 按钮不与 topbar 内的导航链接（Raw Req/Resp / Claude Log）发生视觉遮挡

#### Scenario: 不使用 fixed 定位

- **WHEN** 检查 `.theme-btn` 的 CSS
- **THEN** 不存在 `position: fixed` 声明
- **THEN** 不存在绝对 `top` / `right` 定位值

---

### Requirement: 过渡动效（v2）

所有三个页面 SHALL 为以下交互加入 CSS 过渡动效，不引入任何 JS 动画库。

#### Scenario: 主题切换全局颜色过渡

- **WHEN** `data-theme` 属性切换
- **THEN** 背景色、文字色、边框色在 0.2–0.25s 内平滑过渡，不出现颜色跳变
- **THEN** 只对颜色相关属性设置 transition，不对 width/height/transform 设置全局 transition

#### Scenario: 主题按钮 hover 微动

- **WHEN** 鼠标 hover `.theme-btn`
- **THEN** 按钮产生约 20° 旋转 + 轻微放大（scale 1.05~1.1）的过渡效果，时长 0.2–0.25s

#### Scenario: 折叠区块展开/收起动画

- **WHEN** 用户点击折叠箭头展开或收起 `.sec-body`、`.turn-body`、`.tree-group-body`
- **THEN** 区块高度以 `max-height` 过渡方式平滑展开/收起，时长约 0.3s
- **THEN** 使用 `cubic-bezier(0.4, 0, 0.2, 1)` easing，展开快、收起带缓冲
- **THEN** 同时伴随 `opacity` 从 0 到 1（展开）/ 1 到 0（收起）的淡入淡出

#### Scenario: 折叠箭头旋转动画

- **WHEN** 折叠区块展开时，对应箭头图标（`.tree-arrow`、`.turn-arrow`）
- **THEN** 箭头以 0.25s `cubic-bezier(0.4, 0, 0.2, 1)` 旋转 90°
- **THEN** 收起时旋转回 0°，与区块收起动画同步

#### Scenario: 列表项 hover 背景过渡

- **WHEN** 鼠标 hover `.entry-item`、`.record-item`、`.turn-hdr`、`.turn-child`
- **THEN** 背景色在 0.12–0.15s 内平滑过渡，不出现闪动

#### Scenario: 无障碍——尊重减弱动效偏好

- **WHEN** 系统设置 `prefers-reduced-motion: reduce`
- **THEN** 所有 transition 和 animation 时长缩短至 ≤ 0.01ms，动效实质消失
