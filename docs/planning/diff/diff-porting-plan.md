# Turn Diff 功能移植计划

## 源与目标

| 项目 | 路径 | 说明 |
|------|------|------|
| **源 (Source)** | `/Users/elon-ge/workspace/deep-ai-analysis-session-report-clean/` | 包含完整 diff 功能 (commit 72d7faa) |
| **目标 (Target)** | `/Users/elon-ge/workspace/deep-ai-analysis-copy/` | 需要移植 diff 功能的工作区 |

---

## 1. 兼容性分析

### 1.1 数据结构兼容性 ✅

两个工作区共享相同的数据结构：

```javascript
// 两者都有
let groups = [];                    // 会话分组数组
entry._turnKey                      // "gid:idx" 格式，如 "main:5"
function buildTurns(entries, gid)   // 构建 turn 列表
```

### 1.2 目标工作区缺失的函数 ❌

需要从源工作区补充：

| 函数名 | 用途 | 行数估计 |
|--------|------|----------|
| `_parseTurnKey(tk)` | 解析 turnKey 为 {gid, idx} | ~10 行 |
| `_getGroupObj(gid)` | 根据 gid 获取 group | ~5 行 |
| `_getGroupAllTurnKeys(gid)` | 获取 group 下所有 turnKey | ~10 行 |
| `findDefaultBaseTurnKey(turnKey)` | 找默认对比 turn | ~15 行 |

---

## 2. 移植内容清单

### 2.1 CSS 样式 (直接复制)

**源文件位置**: `viewer/claude-log.html` 第 447-553 行

需要复制的 CSS 区块：
1. `.diff-overlay` - 弹窗遮罩层
2. `.diff-card` / `.diff-card-hdr` - 弹窗卡片
3. `.diff-info-bar` - 顶部信息栏
4. `.diff-tab-nav` / `.diff-tab-btn` - Tab 导航
5. `.diff-body` - 内容区域
6. `.diff-msg-*` - 消息 diff 样式
7. `.diff-field-*` - 字段 diff 样式

**注意**: 如果目标工作区已有类似样式（如 modal、tab），可能需要合并而非覆盖。

### 2.2 HTML 结构 (添加到 body)

**源文件位置**: `viewer/claude-log.html` 中搜索 `diffOverlay`

需要在目标文件 body 中添加的 DOM：

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

### 2.3 JavaScript 函数 (按依赖顺序移植)

#### 阶段 1: 基础辅助函数

```javascript
// 1. Turn Key 解析
function _parseTurnKey(tk) {
  if (!tk) return null;
  const sep = tk.lastIndexOf(':');
  if (sep < 0) return null;
  return { gid: tk.slice(0, sep), idx: parseInt(tk.slice(sep + 1), 10) };
}

// 2. 获取 Group 对象
function _getGroupObj(gid) {
  return groups.find(g => g.id === gid) || null;
}

// 3. 获取 Group 下所有 turn keys
function _getGroupAllTurnKeys(gid) {
  const g = _getGroupObj(gid);
  if (!g) return [];
  const turns = buildTurns(g.entries, gid);
  return turns.filter(t => !t._isPreamble).map(t => `${gid}:${t._turnIdx}`);
}

// 4. 获取 entry 的 turn index
function _getEntryTurnIdx(e) {
  if (e._turnIdx != null) return e._turnIdx;
  if (!e._turnKey) return null;
  const parsed = _parseTurnKey(e._turnKey);
  return parsed ? parsed.idx : null;
}

// 5. 找默认 base turn
function findDefaultBaseTurnKey(turnKey) {
  const parsed = _parseTurnKey(turnKey);
  if (!parsed) return null;
  const allKeys = _getGroupAllTurnKeys(parsed.gid);
  const pos = allKeys.indexOf(turnKey);
  if (pos <= 0) return null;
  return allKeys[pos - 1];
}
```

#### 阶段 2: 上下文归一化

```javascript
// 6. 归一化 turn 上下文
function normalizeTurnContext(turnKey) {
  const parsed = _parseTurnKey(turnKey);
  if (!parsed) return null;
  const g = _getGroupObj(parsed.gid);
  if (!g) return null;
  
  const entries = g.entries.filter(e => {
    const turnIdx = _getEntryTurnIdx(e);
    return typeof turnIdx === 'number' && turnIdx <= parsed.idx;
  }).sort((a,b) => (a._fileLine||0) - (b._fileLine||0));

  // ... 消息、system、tools、params 抽取逻辑
  // 约 80 行
}
```

#### 阶段 3: Diff 计算

```javascript
// 7. Diff 计算函数
function diffMessages(oldMsgs, newMsgs) { /* ~30 行 */ }
function diffSystem(oldSys, newSys) { /* ~20 行 */ }
function diffTools(oldNames, newNames, oldObjs, newObjs) { /* ~20 行 */ }
function diffParams(oldP, newP) { /* ~20 行 */ }
function diffTurnContexts(baseTurnKey, curTurnKey) { /* ~30 行 */ }
function summarizeTurnDiff(diff) { /* ~60 行 */ }
```

#### 阶段 4: 渲染函数

```javascript
// 8. Modal 渲染
function openDiffModal(turnKeyOrEntry) { /* ~30 行 */ }
function closeDiffModal() { /* ~5 行 */ }
function onDiffOverlayClick(e) { /* ~5 行 */ }
function switchDiffTab(tab) { /* ~10 行 */ }
function _renderDiffInfoBar() { /* ~30 行 */ }
function _renderDiffModal() { /* ~15 行 */ }
function _renderDiffBody() { /* ~25 行 */ }

// 9. Tab 渲染
function _renderOverviewTab(diff) { /* ~50 行 */ }
function _renderMessagesTab(diff) { /* ~80 行 */ }
function _renderSystemTab(diff) { /* ~40 行 */ }
function _renderToolsTab(diff) { /* ~50 行 */ }
function _renderParamsTab(diff) { /* ~40 行 */ }
function _renderRawJsonTab(diff) { /* ~40 行 */ }
```

#### 阶段 5: 入口按钮

```javascript
// 10. 创建 diff 按钮
function _makeDiffBtn(turnKey) {
  const btn = document.createElement('button');
  btn.className = 'diff-entry-btn';  // 需要添加对应 CSS
  btn.textContent = '上下文变化';
  btn.title = 'Turn Diff / Context Diff';
  btn.onclick = (e) => { e.stopPropagation(); openDiffModal(turnKey); };
  return btn;
}
```

### 2.4 入口点接入 (需要适配)

这是**最需要人工判断**的部分，需要查看目标工作区的：

1. **Turn 列表渲染位置**
   - 源: `renderList()` 函数中的 turn header
   - 目标: 找到对应的 turn 渲染逻辑，添加 `_makeDiffBtn()`

2. **详情面板渲染位置**
   - 源: `renderDetail()` 函数
   - 目标: 找到对应的详情渲染逻辑，添加 diff 按钮

---

## 3. 移植步骤

### Step 1: 备份目标文件
```bash
cp /Users/elon-ge/workspace/deep-ai-analysis-copy/viewer/claude-log.html \
   /Users/elon-ge/workspace/deep-ai-analysis-copy/viewer/claude-log.html.bak
```

### Step 2: 添加 CSS
在目标文件的 `<style>` 标签内（约第 400-600 行之间），添加 diff 相关 CSS。

### Step 3: 添加 HTML
在目标文件的 `</body>` 前，添加 diff modal DOM。

### Step 4: 添加 JavaScript
在目标文件的 `</script>` 前，按顺序添加所有 diff 函数。

### Step 5: 接入入口
- 在 turn header 渲染处添加 `_makeDiffBtn()`
- 在详情面板渲染处添加 diff 按钮

### Step 6: 测试验证
1. 启动服务器: `python3 viewer/server.py`
2. 打开页面测试 diff 功能
3. 检查各 tab 是否正常显示

---

## 4. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 数据结构不兼容 | 低 | 高 | 移植前验证 `_turnKey` 和 `buildTurns` |
| 样式冲突 | 中 | 中 | 使用特定的 `.diff-*` 前缀 class |
| 入口点难以定位 | 中 | 中 | 先阅读目标文件的 turn 渲染逻辑 |
| 功能回归 | 中 | 高 | 移植后全面测试原有功能 |

---

## 5. 工作量估计

| 任务 | 估计时间 |
|------|----------|
| 阅读目标文件结构 | 15 分钟 |
| 复制 CSS + HTML | 10 分钟 |
| 复制 JavaScript 函数 | 30 分钟 |
| 适配入口点 | 30 分钟 |
| 测试验证 | 30 分钟 |
| **总计** | **约 2 小时** |

---

## 6. 验证清单

- [ ] diff 弹窗能正常打开
- [ ] Overview tab 显示摘要
- [ ] Messages tab 左右分栏显示
- [ ] System tab 显示 system 变化
- [ ] Tools tab 显示工具变化
- [ ] Params tab 显示参数变化
- [ ] Raw JSON tab 显示原始数据
- [ ] 左右箭头导航可用
- [ ] 原有功能（列表、详情、导出等）正常
