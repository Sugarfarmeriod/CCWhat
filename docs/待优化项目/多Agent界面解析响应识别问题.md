# 多 Agent 界面解析响应识别问题

## 问题概述

当前 ccwhat 前端界面的详情面板（Detail Panel）在处理不同 Agent（Claude Code、OpenCode、Codex 等）的数据格式时存在解析不一致的问题。不同 Agent 的日志格式差异导致 System Prompt 识别错误、System Reminder 缺失等问题。

## 问题详情

### 问题 1: System Prompt 识别错误

**现象**: 
在 OpenCode 的 Session 中，详情面板的"系统提示词"卡片显示错误的内容或显示为空。

**根本原因**:
不同 Agent 存储 System Prompt 的位置完全不同：

| Agent | System Prompt 存储位置 |
|-------|------------------------|
| **Claude Code** | 1. Session 文件第一个 user entry 的 `system` 字段<br>2. 或单独的 `type: "system"` entry |
| **OpenCode** | **不存储 System Prompt**。经检查 SQLite 数据库 (`opencode.db`)，`session`/`message`/`part` 三张表中均无 System Prompt 字段 |
| **Codex** | 待调查 |

**当前代码问题**:
`extractSystemPrompt()` 函数只检查 `type === "system"`，导致误判：
- 将 OpenCode 的 `type: "system"`, `subtype: "step: step-start"` 误判为 System Prompt
- 实际上这是一个 Step 开始事件，不是 System Prompt

**期望行为**:
- 正确识别不同 Agent 的 System Prompt 位置
- 对于不存储 System Prompt 的 Agent（如 OpenCode），显示"当前 Agent 不存储系统提示词"
- 排除带有 `subtype` 为 `step-start` 等的事件

---

### 问题 2: System Reminder 显示缺失

**现象**:
用户消息卡片中没有显示 System Reminder 折叠块。

**根本原因**:
不同 Agent 的消息格式完全不同，System Reminder 的存在形式和位置也不同：

| Agent | System Reminder 存在性 | 存储位置/格式 |
|-------|------------------------|---------------|
| **Claude Code** | ✅ 有 | 存储在 user message content 数组中，`type: "system_reminder"` 或 `type: "systemReminder"` 的 block |
| **OpenCode** | ❌ 无 | OpenCode 的 user message 只有 `text` 和 `input` 类型，**没有 System Reminder 概念** |
| **Codex** | 待调查 | 待调查 |

**当前代码问题**:
`extractUserContent()` 函数只检查了 Claude Code 的格式（`system_reminder` block），没有针对不同 Agent 做适配。

**期望行为**:
- 根据当前 Agent 类型使用不同的提取逻辑
- Claude Code: 提取 `system_reminder` block
- OpenCode: 不显示 System Reminder（因为不存在）
- 在 UI 上明确区分"无内容"和"当前 Agent 不支持"

---

## 相关代码位置

- `viewer/claude-log.html`:
  - `extractSystemPrompt()` - 系统提示词提取
  - `extractUserContent()` - 用户消息内容提取
  - `buildSystemPromptSection()` - 系统提示词卡片构建
  - `buildMessageSection()` - 用户消息卡片构建

- `ccwhat/adapters/claude.py` - Claude Code 适配器
- `ccwhat/adapters/opencode.py` - OpenCode 适配器
- `ccwhat/adapters/codex.py` - Codex 适配器

## 建议解决方案

### 短期方案
1. 修复 `extractSystemPrompt()` 的判断逻辑，排除 `subtype` 为 `step-start` 等事件
2. 在 `extractUserContent()` 中根据 `entry.agent` 或 `allEntries[0].agent` 判断当前 Agent 类型，使用不同的提取逻辑
3. 对于不支持的字段，显示"当前 Agent 不存储此信息"而非空内容

### 长期方案
1. 在 Adapter 层规范化数据，统一输出格式（参考 `raw_to_normalized_events`）
2. 前端只处理标准化后的数据，无需关心原始 Agent 类型
3. 为每个 Adapter 添加元数据说明支持哪些字段

## 附录：各 Agent 原始数据格式对比

### Claude Code User Entry 结构
```json
{
  "type": "user",
  "message": {
    "content": [
      {"type": "text", "text": "用户输入"},
      {"type": "system_reminder", "text": "System Reminder 内容"},
      {"type": "tool_result", "tool_use_id": "...", "content": "..."}
    ]
  },
  "system": "System Prompt 内容（可能在 entry 级别）"
}
```

### OpenCode User Entry 结构
```json
{
  "role": "user",
  "parts": [
    {"data": {"type": "text", "text": "用户输入"}}
  ],
  // 无 system 字段
  // 无 system_reminder
}
```

### OpenCode Step Start（被误判为 System Prompt）
```json
{
  "type": "system",
  "subtype": "step: step-start",
  "message": {"content": [{"type": "text", "text": ""}]}
}
```

---

**创建日期**: 2026-06-20  
**优先级**: P1  
**影响范围**: 前端详情面板展示（所有 Agent 类型）
