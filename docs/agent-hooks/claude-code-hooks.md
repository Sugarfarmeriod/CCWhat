# Claude Code Hooks 参考

## 一、Hook 是什么

Claude Code 的 Hook 机制允许在会话生命周期的特定节点注入自定义 shell 命令。Hook 配置写在 `.claude/settings.local.json` 或 `settings.json` 中。

```json
{
  "hooks": {
    "<EventType>": [
      {
        "matcher": "<正则>",
        "hooks": [
          { "type": "command", "command": "<shell命令>", "timeout": 10 }
        ]
      }
    ]
  }
}
```

Hook 命令从 stdin 读取 JSON 事件，通过 exit code 或 stdout JSON 控制行为：
- exit 0：放行，不干预
- exit 2：阻止，配合 stdout 输出 `{"decision":"block","reason":"..."}` 给用户反馈

---

## 二、全部 Hook 事件类型

### 会话级（每个会话一次）

| 事件 | 触发时机 |
|------|---------|
| `SessionStart` | 会话启动或恢复 |
| `SessionEnd` | 会话终止 |

### 每轮用户输入

| 事件 | 触发时机 |
|------|---------|
| `UserPromptSubmit` | 用户按 Enter 提交后、Claude 处理前 |
| `UserPromptExpansion` | slash 命令被展开为完整 prompt 时（含导航预览） |
| `Stop` | Claude 完成一轮响应时 |
| `StopFailure` | API 错误导致轮次中断时 |

### 每次工具调用

| 事件 | 触发时机 |
|------|---------|
| `PreToolUse` | 工具执行前，可阻止 |
| `PostToolUse` | 工具成功执行后 |
| `PostToolUseFailure` | 工具执行失败后 |
| `PostToolBatch` | 一批并行工具全部完成后 |

### 其他

| 事件 | 触发时机 |
|------|---------|
| `Notification` | Claude Code 发出通知时 |
| `FileChanged` | 监视的文件在磁盘上变动时 |
| `ConfigChange` | 配置文件在会话期间变更时 |
| `SubagentStart` / `SubagentStop` | 子 Agent 生成/完成时 |

---

## 三、UserPromptExpansion vs UserPromptSubmit

这两个事件是最容易混淆、也最容易用错的。

### 执行时序

```
用户在 slash 命令列表按方向键
        ↓
  [UserPromptExpansion]  ← 每次高亮切换都触发（导航阶段）
        ↓
  Claude Code 展开命令内容作为预览
        ↓
  用户按 Enter 确认提交
        ↓
  [UserPromptSubmit]     ← 只触发一次（提交阶段）
        ↓
  Claude 处理 prompt
```

### 对比

| | `UserPromptExpansion` | `UserPromptSubmit` |
|---|---|---|
| 触发节点 | slash 命令展开/预览时 | 用户按 Enter 提交时 |
| 触发频率 | 方向键每切换一次触发一次 | 每次提交触发一次 |
| 设计用途 | 动态注入命令上下文、修改展开内容 | 拦截/审计/清理用户 prompt |
| 阻止语义 | 阻止命令展开 | 阻止 prompt 发给模型 |

### 典型误用及后果

在 CCWhat runtime hook 场景中，将 hook 注册到 `UserPromptExpansion` 而非 `UserPromptSubmit`：

- 用户在 slash 命令列表里按方向键 → 每次都 spawn 一个 Python 进程
- Python 进程启动有耗时 → 终端短暂卡顿
- Claude Code UI 重绘 → slash 命令列表滚动回顶部
- 用户无法正常用方向键浏览命令列表

**正确做法**：拦截命令不让其发给模型，应使用 `UserPromptSubmit`。

---

## 四、CCWhat Runtime Hook 正确配置

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "ccwhat:(start|finish|abort|status|note)|ccwhat-(start|finish|abort|status|note)",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/ccwhat-runtime-hook.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Hook 脚本在匹配到 ccwhat 命令时返回 exit 2 + block payload，阻止命令发给模型；不匹配时返回 exit 0，不干预正常 prompt。
