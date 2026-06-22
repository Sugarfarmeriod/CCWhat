# Turn Diff 功能移植计划（分阶段版）

## 概述

将 `deep-ai-analysis-session-report-clean` 中的 Turn Diff 功能移植到 `deep-ai-analysis-copy`。

---

## Phase 1: 核心功能 MVP（基础移植）

**目标**：让 diff 功能在当前主题下正常工作，完成核心功能移植。

**预计时间**：1.5 - 2 小时
**阻塞后续**：是（Phase 2 依赖此阶段）

### 1.1 移植内容

#### 1.1.1 基础辅助函数（直接复制）

添加以下函数到目标文件 `viewer/claude-log.html` 的 `<script>` 标签内：

```javascript
// Turn Key 解析
function _parseTurnKey(tk) {
  if (!tk) return null;
  const sep = tk.lastIndexOf(':');
  if (sep < 0) return null;
  return { gid: tk.slice(0, sep), idx: parseInt(tk.slice(sep + 1), 10) };
}

// 获取 Group 对象
function _getGroupObj(gid) {
  return groups.find(g => g.id === gid) || null;
}

// 获取 Group 下所有 turn keys
function _getGroupAllTurnKeys(gid) {
  const g = _getGroupObj(gid);
  if (!g) return [];
  const turns = buildTurns(g.entries, gid);
  return turns.filter(t => !t._isPreamble).map(t => `${gid}:${t._turnIdx}`);
}

// 找默认 base turn
function findDefaultBaseTurnKey(turnKey) {
  const parsed = _parseTurnKey(turnKey);
  if (!parsed) return null;
  const allKeys = _getGroupAllTurnKeys(parsed.gid);
  const pos = allKeys.indexOf(turnKey);
  if (pos <= 0) return null;
  return allKeys[pos - 1];
}
```

#### 1.1.2 Diff 核心逻辑（直接复制）

按顺序添加以下函数：

1. `_NOISE_KEYS` 常量定义
2. `_isNoiseKey()` 辅助函数
3. `_msgContentSummary()` 函数
4. `_extractSysReminders()` 函数
5. `_extractToolNames()` 函数
6. `_extractTokenUsage()` 函数
7. `_extractToolCalls()` 函数
8. `normalizeTurnContext()` 函数（约 70 行）
9. `diffMessages()` 函数
10. `diffSystem()` 函数
11. `diffTools()` 函数
12. `diffParams()` 函数
13. `diffTurnContexts()` 函数
14. `summarizeTurnDiff()` 函数

#### 1.1.3 Modal 控制函数（直接复制）

添加以下函数：

```javascript
let _diffCurrentTurnKey = null;
let _diffBaseTurnKey    = null;
let _diffActiveTab      = 'overview';
let _diffIsManualBase   = false;

function openDiffModal(turnKeyOrEntry) {
  let turnKey;
  if (typeof turnKeyOrEntry === 'string') {
    turnKey = turnKeyOrEntry;
  } else if (turnKeyOrEntry && turnKeyOrEntry._turnKey) {
    turnKey = turnKeyOrEntry._turnKey;
  } else {
    return;
  }
  _diffCurrentTurnKey = turnKey;
  _diffBaseTurnKey    = findDefaultBaseTurnKey(turnKey);
  _diffIsManualBase   = false;
  _diffActiveTab      = 'overview';
  document.getElementById('diffOverlay').classList.add('open');
  _renderDiffModal();
}

function closeDiffModal() {
  document.getElementById('diffOverlay').classList.remove('open');
}

function onDiffOverlayClick(e) {
  if (e.target === document.getElementById('diffOverlay')) closeDiffModal();
}

function switchDiffTab(tab) {
  _diffActiveTab = tab;
  document.querySelectorAll('.diff-tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.dtab === tab));
  _renderDiffBody();
}

function setDiffBaseTurn(turnKey) {
  _diffBaseTurnKey    = turnKey;
  _diffIsManualBase   = true;
  _renderDiffInfoBar();
  _renderDiffBody();
}
```

#### 1.1.4 渲染函数（直接复制）

添加以下渲染函数：

1. `_renderDiffModal()`
2. `_renderDiffInfoBar()`
3. `_renderDiffBody()`
4. `_renderOverviewTab()`
5. `_renderMessagesTab()`
6. `_renderMsgRow()`
7. `_renderSystemTab()`
8. `_renderToolsTab()`
9. `_renderToolRow()`
10. `_renderParamsTab()`
11. `_renderRawJsonTab()`

#### 1.1.5 基础 CSS（MVP 版本）

在目标文件的 `<style>` 标签内添加基础样式（使用当前主题色，暂不做双主题适配）：

```css
/* ── Context Diff modal (MVP) ── */
.diff-overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,.70); z-index: 9999;
  align-items: flex-start; justify-content: center; padding-top: 32px;
}
.diff-overlay.open { display: flex; }
.diff-card {
  background: var(--bg-elevated); border: 1px solid var(--border); border-radius: var(--radius-md);
  width: min(840px, 96vw); max-height: calc(100vh - 64px);
  display: flex; flex-direction: column; overflow: hidden;
}
.diff-card-hdr {
  background: var(--bg-surface); padding: 10px 14px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.diff-card-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.diff-card-close {
  background: none; border: none; color: var(--text-secondary);
  font-size: 16px; cursor: pointer; padding: 0 4px; line-height: 1;
}
.diff-card-close:hover { color: var(--text-primary); }
.diff-info-bar {
  padding: 8px 14px; background: var(--bg-surface); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex-shrink: 0;
  font-size: 11px;
}
.diff-info-label { color: var(--text-secondary); white-space: nowrap; }
.diff-info-val { color: var(--text-primary); font-family: var(--font-mono); }
.diff-source-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 10px;
  background: color-mix(in srgb, var(--accent) 15%, var(--bg-surface));
  color: var(--accent); border: 1px solid var(--accent); white-space: nowrap;
}
.diff-base-sel {
  margin-left: auto; font-size: 11px; background: var(--bg-base);
  color: var(--text-primary); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 3px 6px; cursor: pointer; max-width: 260px;
}
.diff-base-sel:focus { outline: none; border-color: var(--accent); }
.diff-tab-nav {
  display: flex; border-bottom: 1px solid var(--border); flex-shrink: 0;
  background: var(--bg-elevated); overflow-x: auto;
}
.diff-tab-btn {
  border: none; background: transparent; color: var(--text-secondary); cursor: pointer;
  font-size: 12px; padding: 8px 14px; white-space: nowrap;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.diff-tab-btn:hover { color: var(--text-primary); }
.diff-tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.diff-body { flex: 1; overflow-y: auto; padding: 14px; background: var(--bg-base); }

/* Message diff rows */
.diff-msg-row { padding: 7px 10px; border-radius: 5px; margin-bottom: 5px; border-left: 3px solid transparent; }
.diff-msg-added  { background: rgba(48,209,88,0.12); border-left-color: var(--success); }
.diff-msg-removed{ background: rgba(255,59,48,0.12); border-left-color: var(--danger); }
.diff-msg-same   { background: var(--bg-surface); border-left-color: var(--border); opacity: 0.65; }
.diff-msg-hdr { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
.diff-msg-mark { font-size: 12px; font-weight: 700; width: 12px; flex-shrink: 0; }
.diff-msg-added  .diff-msg-mark { color: var(--success); }
.diff-msg-removed .diff-msg-mark { color: var(--danger); }
.diff-msg-same    .diff-msg-mark { color: var(--text-tertiary); }
.diff-role-badge { font-size: 10px; padding: 1px 5px; border-radius: 3px; font-weight: 600; }
.diff-role-user      { background: var(--type-user-bg); color: var(--type-user-fg); }
.diff-role-assistant { background: var(--type-asst-bg); color: var(--type-asst-fg); }
.diff-role-tool  { background: var(--type-att-bg); color: var(--type-att-fg); }
.diff-special-tag {
  font-size: 9px; padding: 1px 5px; border-radius: 10px;
  background: rgba(175,82,222,0.12); color: #7a2fa0;
}
.diff-msg-content {
  color: var(--text-secondary); font-size: 11px; line-height: 1.5; margin-top: 3px;
  max-height: 80px; overflow: hidden; white-space: pre-wrap; word-break: break-word;
}
.diff-fold-row {
  text-align: center; font-size: 11px; color: var(--text-tertiary); padding: 4px;
  cursor: pointer; border-bottom: 1px dashed var(--border); margin-bottom: 5px;
}
.diff-fold-row:hover { color: var(--text-secondary); }

/* Field diff rows */
.diff-field-row {
  display: flex; align-items: flex-start; gap: 10px; padding: 6px 8px;
  border-radius: 4px; margin-bottom: 4px; font-size: 12px;
}
.diff-field-added   { background: rgba(48,209,88,0.12); }
.diff-field-removed { background: rgba(255,59,48,0.12); }
.diff-field-changed { background: rgba(255,159,10,0.12); }
.diff-field-same    { background: var(--bg-surface); opacity: 0.6; }
.diff-field-key { color: var(--accent); font-family: var(--font-mono); min-width: 110px; flex-shrink: 0; font-size: 11px; }
.diff-field-old { color: var(--danger); text-decoration: line-through; font-family: var(--font-mono); margin-right: 6px; }
.diff-field-new { color: var(--success); font-family: var(--font-mono); }
.diff-section-hdr {
  font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase;
  letter-spacing: 0.5px; margin: 14px 0 6px;
}
.diff-section-hdr:first-child { margin-top: 0; }
.diff-empty { color: var(--text-tertiary); font-size: 12px; text-align: center; padding: 24px 0; }
.diff-summary-item { font-size: 12px; color: var(--text-primary); line-height: 1.8; }
.diff-plus  { color: var(--success); font-weight: 600; }
.diff-minus { color: var(--danger); font-weight: 600; }
.diff-tilde { color: var(--warning); font-weight: 600; }
.diff-same  { color: var(--text-tertiary); }
.diff-schema-pre {
  font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px; margin-top: 4px;
  max-height: 160px; overflow-y: auto; white-space: pre-wrap; word-break: break-all;
}

/* Diff entry button */
.diff-entry-btn {
  font-size: 10px; padding: 1px 7px; border-radius: 3px;
  background: color-mix(in srgb, var(--accent) 15%, var(--bg-surface));
  color: var(--accent); border: 1px solid var(--accent);
  cursor: pointer; white-space: nowrap; flex-shrink: 0; line-height: 1.6;
}
.diff-entry-btn:hover { background: color-mix(in srgb, var(--accent) 25%, var(--bg-surface)); }
```

#### 1.1.6 HTML 结构

在目标文件的 `</body>` 前添加：

```html
<!-- Diff Modal -->
<div id="diffOverlay" class="diff-overlay" onclick="onDiffOverlayClick(event)">
  <div class="diff-card">
    <div class="diff-card-hdr">
      <span class="diff-card-title">上下文变化 (Turn Diff)</span>
      <button class="diff-card-close" onclick="closeDiffModal()">&times;</button>
    </div>
    <div id="diffInfoBar" class="diff-info-bar"></div>
    <div class="diff-tab-nav">
      <button class="diff-tab-btn active" data-dtab="overview" onclick="switchDiffTab('overview')">概览</button>
      <button class="diff-tab-btn" data-dtab="messages" onclick="switchDiffTab('messages')">消息</button>
      <button class="diff-tab-btn" data-dtab="system" onclick="switchDiffTab('system')">系统提示</button>
      <button class="diff-tab-btn" data-dtab="tools" onclick="switchDiffTab('tools')">工具</button>
      <button class="diff-tab-btn" data-dtab="params" onclick="switchDiffTab('params')">参数</button>
      <button class="diff-tab-btn" data-dtab="rawjson" onclick="switchDiffTab('rawjson')">Raw JSON</button>
    </div>
    <div id="diffBody" class="diff-body"></div>
  </div>
</div>
```

#### 1.1.7 入口按钮函数

添加按钮创建函数：

```javascript
function _makeDiffBtn(turnKey) {
  const btn = document.createElement('button');
  btn.className = 'diff-entry-btn';
  btn.textContent = '上下文变化';
  btn.title = 'Turn Diff / Context Diff';
  btn.onclick = (e) => { e.stopPropagation(); openDiffModal(turnKey); };
  return btn;
}
```

#### 1.1.8 接入入口点

**入口点 1：Turn Header**

在 `renderList()` 函数中，找到 turn header 的创建代码（约第 7006-7023 行），在 `turnHdr.innerHTML = ...` 之后添加：

```javascript
// Add diff button to turn header
const diffBtn = _makeDiffBtn(turnKey);
turnHdr.querySelector('.turn-hdr-row1').appendChild(diffBtn);
```

**入口点 2：Detail 面板**

在 `renderDetail()` 函数中，找到合适的位置（通常在头部信息区域）添加 diff 按钮。具体位置需要查看 `renderDetail` 函数的实现来确定。

### 1.2 Phase 1 测试清单

启动服务器：`python3 viewer/server.py`

| 测试项 | 操作步骤 | 期望结果 | 状态 |
|--------|----------|----------|------|
| 1.1 | 打开页面，加载任意 session | 页面正常加载，无 JS 错误 | ☐ |
| 1.2 | 查看左侧 turn 列表，确认每个 turn header 有"上下文变化"按钮 | 按钮显示正常，样式不突兀 | ☐ |
| 1.3 | 点击第一个 turn 的"上下文变化"按钮 | 弹窗显示"当前 turn 是首个 turn"提示 | ☐ |
| 1.4 | 点击第二个 turn 的"上下文变化"按钮 | 弹窗正常打开，显示 Overview tab | ☐ |
| 1.5 | 检查 Overview tab 内容 | 显示变化摘要和统计卡片 | ☐ |
| 1.6 | 点击 Messages tab | 显示消息 diff，新增消息高亮 | ☐ |
| 1.7 | 点击 System tab | 显示 system reminder 变化 | ☐ |
| 1.8 | 点击 Tools tab | 显示工具调用变化 | ☐ |
| 1.9 | 点击 Params tab | 显示参数变化 | ☐ |
| 1.10 | 点击 Raw JSON tab | 显示原始 JSON 数据 | ☐ |
| 1.11 | 点击弹窗外部或关闭按钮 | 弹窗关闭 | ☐ |
| 1.12 | 测试 Base Turn 选择器（如果有多个 turn） | 可以选择其他 turn 作为对比基准 | ☐ |
| 1.13 | 检查原有功能（列表、详情、搜索等） | 原有功能正常工作 | ☐ |

### 1.3 Phase 1 验收标准

**必须全部通过才能进入 Phase 2：**

- [ ] 测试清单 1.1 - 1.13 全部通过
- [ ] 浏览器控制台无 JavaScript 错误
- [ ] 当前主题（默认 theme）下 UI 显示正常
- [ ] 原有功能无回归

**人工验收人**：用户本人
**验收方式**：按照测试清单逐项检查，确认通过后在状态栏标记

---

## Phase 2: 双主题适配

**目标**：让 diff 功能在 Light 和 Dark 两种主题下都正常显示。

**预计时间**：0.5 - 1 小时
**前置依赖**：Phase 1 验收通过
**阻塞后续**：是（Phase 3 依赖此阶段）

### 2.1 移植内容

#### 2.1.1 检查 Dark 主题下的样式

在 Light 主题下测试通过后，切换到 Dark 主题（点击页面主题切换按钮或修改 `data-theme` 属性）。

检查以下元素在 Dark 主题下的显示：

1. Modal 背景色是否正确
2. 新增/删除/修改的颜色对比度是否足够
3. 边框颜色是否正确
4. 文字颜色是否正确

#### 2.1.2 修复 Dark 主题下的问题

如果发现样式问题，在 CSS 中添加针对 Dark 主题的覆盖：

```css
[data-theme="dark"] .diff-msg-added { background: rgba(48,209,88,0.15); }
[data-theme="dark"] .diff-msg-removed { background: rgba(255,59,48,0.15); }
/* 其他需要覆盖的样式... */
```

### 2.2 Phase 2 测试清单

| 测试项 | 操作步骤 | 期望结果 | 状态 |
|--------|----------|----------|------|
| 2.1 | 切换到 Light 主题，打开 diff modal | 所有元素显示正常，对比度足够 | ☐ |
| 2.2 | 在 Light 主题下切换所有 tabs | 每个 tab 内容显示正常 | ☐ |
| 2.3 | 切换到 Dark 主题，打开 diff modal | 所有元素显示正常，对比度足够 | ☐ |
| 2.4 | 在 Dark 主题下切换所有 tabs | 每个 tab 内容显示正常 | ☐ |
| 2.5 | 在 Dark 主题下，测试新增/删除/修改的样式 | 颜色区分明显，易于阅读 | ☐ |
| 2.6 | 从 Light 切换到 Dark 时，已打开的 modal 样式自动更新 | 无需关闭重开即可看到正确样式 | ☐ |

### 2.3 Phase 2 验收标准

**必须全部通过才能进入 Phase 3：**

- [ ] 测试清单 2.1 - 2.6 全部通过
- [ ] Light 主题下所有 diff 类型（新增/删除/修改）易于区分
- [ ] Dark 主题下所有 diff 类型（新增/删除/修改）易于区分
- [ ] 主题切换时无需刷新页面即可生效

**人工验收人**：用户本人
**验收方式**：分别在 Light/Dark 主题下测试，确认通过后在状态栏标记

---

## Phase 3: 回归测试与优化

**目标**：全面测试确保不破坏原有功能，优化细节。

**预计时间**：0.5 - 1 小时
**前置依赖**：Phase 2 验收通过

### 3.1 移植内容

#### 3.1.1 Detail 面板入口按钮（如果 Phase 1 未完成）

如果在 Phase 1 中没有在 Detail 面板添加 diff 按钮，在此阶段完成：

在 `renderDetail()` 函数中找到合适的位置添加：

```javascript
// 在详情面板添加 diff 按钮
if (entry._turnKey) {
  const diffBtn = _makeDiffBtn(entry._turnKey);
  // 将按钮添加到合适的位置
}
```

#### 3.1.2 样式微调

根据实际使用情况微调样式：
- 按钮大小、间距
- Modal 最大高度
- Tab 按钮的响应式布局

### 3.2 Phase 3 测试清单

| 测试项 | 操作步骤 | 期望结果 | 状态 |
|--------|----------|----------|------|
| 3.1 | 测试列表滚动性能（大数据量 session） | 滚动流畅，无卡顿 | ☐ |
| 3.2 | 测试搜索功能 | 搜索正常工作，diff 按钮随列表更新 | ☐ |
| 3.3 | 测试筛选功能（类型筛选） | 筛选正常工作，diff 按钮显示正确 | ☐ |
| 3.4 | 测试展开/折叠 turn | 展开/折叠正常工作 | ☐ |
| 3.5 | 测试选择 entry | 选择后详情面板显示正确 | ☐ |
| 3.6 | 测试键盘导航（如果有） | 键盘导航正常工作 | ☐ |
| 3.7 | 在 Detail 面板点击 diff 按钮（如果已实现） | 正常打开 diff modal | ☐ |
| 3.8 | 测试不同浏览器（Chrome/Safari） | 样式一致，功能正常 | ☐ |
| 3.9 | 测试移动端（可选） | Modal 在小屏幕下可正常使用 | ☐ |

### 3.3 Phase 3 验收标准

**全部通过表示移植完成：**

- [ ] 测试清单 3.1 - 3.9 全部通过
- [ ] 所有原有功能无回归
- [ ] 代码符合目标工作区的代码风格
- [ ] 无遗留的 console.log 或调试代码

**人工验收人**：用户本人
**验收方式**：全面测试，确认通过后项目完成

---

## 附录

### A. 源文件关键位置参考

| 内容 | 源文件位置 |
|------|-----------|
| CSS 样式 | `viewer/claude-log.html` 第 447-561 行 |
| HTML 结构 | `viewer/claude-log.html` 第 695 行附近（搜索 `diffOverlay`） |
| 基础辅助函数 | `viewer/claude-log.html` 第 2135-2167 行 |
| 上下文归一化 | `viewer/claude-log.html` 第 2172-2315 行 |
| Diff 计算 | `viewer/claude-log.html` 第 2319-2395 行 |
| 摘要生成 | `viewer/claude-log.html` 第 2399-2450 行 |
| Modal 控制 | `viewer/claude-log.html` 第 2454-2529 行 |
| Tab 渲染 | `viewer/claude-log.html` 第 2567-2782 行 |
| 入口按钮 | `viewer/claude-log.html` 第 2787-2794 行 |
| Turn header 入口 | `viewer/claude-log.html` 第 1615 行（`turnHdr.appendChild(_makeDiffBtn(turnKey))`） |
| Detail 面板入口 | `viewer/claude-log.html` 第 1709 行 |

### B. 目标文件关键位置

| 内容 | 目标文件位置 |
|------|-------------|
| CSS 变量定义 | `viewer/claude-log.html` 第 16-88 行 |
| `buildTurns` 函数 | `viewer/claude-log.html` 第 6787 行附近 |
| `renderList` 函数 | `viewer/claude-log.html` 第 6942 行附近 |
| Turn header 创建 | `viewer/claude-log.html` 第 7006-7023 行 |
| `renderDetail` 函数 | `viewer/claude-log.html` 第 7100 行附近 |

### C. 常见问题排查

**Q: 点击按钮没有反应**
- 检查 `_makeDiffBtn` 函数是否正确添加
- 检查 `openDiffModal` 函数是否正确添加
- 检查浏览器控制台是否有 JS 错误

**Q: Modal 打开但内容为空**
- 检查 `_diffCurrentTurnKey` 是否正确设置
- 检查 `normalizeTurnContext` 函数是否正常工作
- 检查 `buildTurns` 函数在目标工作区是否有差异

**Q: Tab 切换无效**
- 检查 `switchDiffTab` 函数是否正确添加
- 检查 `_renderDiffBody` 函数是否正确添加

**Q: 样式显示异常**
- 检查 CSS 变量是否正确引用（`var(--xxx)`）
- 检查是否有样式冲突（使用浏览器开发者工具检查）

---

## 执行记录

| Phase | 开始时间 | 完成时间 | 执行人 | 验收人 | 状态 |
|-------|----------|----------|--------|--------|------|
| Phase 1 | - | - | - | - | ⏳ 未开始 |
| Phase 2 | - | - | - | - | ⏳ 未开始 |
| Phase 3 | - | - | - | - | ⏳ 未开始 |

**状态说明**：⏳ 未开始 / 🚧 进行中 / ✅ 已完成 / ❌ 已阻塞
