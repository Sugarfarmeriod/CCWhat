# Codex Hooks 参考

## 一、Codex 配置体系

Codex 使用 TOML 配置文件，位于 `~/.codex/config.toml`。

### 配置文件结构

```toml
# 基本设置
model = "gpt-5.5"
personality = "pragmatic"

# 特性开关
[features]
js_repl = false

# 插件系统
[plugins."documents@openai-primary-runtime"]
enabled = true

# MCP 服务器
[mcp_servers.node_repl]
command = "/Applications/Codex.app/Contents/Resources/node_repl"
startup_timeout_sec = 120

# 项目信任级别
[projects."/path/to/workspace"]
trust_level = "trusted"
```

## 二、Hook 支持现状

### ⚠️ 关键结论：Codex **不支持**类似 Claude Code 的 `UserPromptSubmit` Hook

Codex 目前没有提供在用户提交 prompt 前拦截并执行自定义命令的机制。

### Codex 支持的机制

| 机制 | 用途 | 能否拦截 prompt |
|------|------|----------------|
| `notify` | 外部程序通知（如 Computer Use） | ❌ 否 |
| `plugins` | 官方插件系统（PDF、Browser 等） | ❌ 否 |
| `mcp_servers` | MCP 工具服务器 | ❌ 否 |

### notify 配置示例

```toml
notify = [
    "/path/to/Codex Computer Use.app/Contents/.../SkyComputerUseClient",
    "turn-ended",
]
```

`notify` 只在回合结束时触发，**不能用于拦截用户输入**。

## 三、CCWhat 集成路径评估

### 方案对比

| 方案 | 可行性 | 复杂度 | 用户体验 |
|------|--------|--------|----------|
| A. 原生 Hook 拦截 | ❌ 不可行 | - | - |
| B. MCP Tool 模拟 | ⚠️ 部分可行 | 高 | 差（需要用户 @mention） |
| C. 外部 Wrapper 脚本 | ✅ 可行 | 中 | 中（需包装 codex 命令） |
| D. 手动命令触发 | ✅ 可行 | 低 | 低（纯文本命令） |

### 推荐方案：D. 手动命令触发（降级）

由于 Codex 不支持原生 Hook 拦截，建议采用**手动命令触发**的降级方案：

```
用户输入: /ccwhat-start my task title
Codex 处理: 发送给模型
CCWhat 检测: 通过解析 Codex 日志检测到命令
CCWhat 响应: 在 viewer 中标记任务开始
```

### 降级标记

使用此方案时，Dataset 必须标记：

```json
{
  "model_visible": true,
  "agent_log_visible": false,
  "confidence": "low",
  "integration": "codex_manual_command"
}
```

## 四、未来可能性

Codex 团队可能会在未来版本添加 Hook 支持。建议关注：

- Codex CLI 的 GitHub releases
- `~/.codex/config.toml` 的新配置项
- 官方文档更新

## 五、相关文件

- 适配器实现：`ccwhat/adapters/codex.py`
- 配置检测：`ccwhat/agent_config.py:_detect_codex_domains()`
