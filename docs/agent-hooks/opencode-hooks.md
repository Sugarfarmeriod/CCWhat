# OpenCode Hooks 参考

## 一、OpenCode 配置体系

OpenCode 使用以下配置路径：

```
~/.local/share/opencode/opencode.db  # SQLite 数据库（会话存储）
~/.opencode/                          # 用户配置目录
~/.opencode/package.json              # Plugin 依赖
```

### Plugin 系统

OpenCode 有官方 Plugin SDK：`@opencode-ai/plugin`

```json
// ~/.opencode/package.json
{
  "dependencies": {
    "@opencode-ai/plugin": "1.15.5"
  }
}
```

## 二、Hook 支持现状

### ⚠️ 关键结论：OpenCode **可能支持** Plugin 拦截，但需进一步调研

OpenCode 的 Plugin 系统允许开发自定义插件，但是否支持**用户输入拦截**尚不确定。

### OpenCode 架构

```
OpenCode App (Electron)
├── Core Engine
├── Plugin System (@opencode-ai/plugin)
├── Tool Registry
└── Session Manager (SQLite)
```

### Plugin 能力矩阵（待验证）

| 能力 | 是否支持 | 验证状态 |
|------|----------|----------|
| 注册自定义命令 | 待验证 | ❓ |
| 拦截用户输入 | 待验证 | ❓ |
| 修改模型响应 | 待验证 | ❓ |
| 访问会话数据 | ✅ 支持 | 通过 SQLite |

## 三、CCWhat 集成路径评估

### 方案对比

| 方案 | 可行性 | 复杂度 | 备注 |
|------|--------|--------|------|
| A. 开发 OpenCode Plugin | ⚠️ 未知 | 高 | 需验证 Plugin API |
| B. MCP Server 集成 | ✅ 可行 | 中 | OpenCode 支持 MCP |
| C. 外部 Wrapper | ✅ 可行 | 中 | 类似 Codex |
| D. 手动命令触发 | ✅ 可行 | 低 | 降级方案 |

### 推荐方案：B. MCP Server + D. 手动命令（组合）

#### 第一步：MCP Server 方案

OpenCode 支持 MCP (Model Context Protocol)，可以注册工具：

```json
// ~/.opencode/mcp-config.json (假设路径)
{
  "mcpServers": {
    "ccwhat": {
      "command": "python",
      "args": ["-m", "ccwhat.runtime.mcp_server"],
      "env": {
        "CCWHAT_RUNTIME_CONTROL_PORT": "7790"
      }
    }
  }
}
```

用户在对话中可以通过 `@ccwhat/start` 触发 MCP 工具调用。

#### 第二步：降级到手动命令

如果 MCP 方案用户体验不佳，使用纯文本命令作为 fallback：

```
用户输入: @ccwhat-start task title
或
用户输入: /ccwhat-start task title
```

### 降级标记

```json
{
  "model_visible": true,
  "agent_log_visible": false,
  "confidence": "medium",
  "integration": "opencode_mcp_or_manual"
}
```

## 四、Spike 任务：验证 OpenCode Plugin 能力

在正式开发前，建议进行以下验证：

```bash
# 1. 检查 OpenCode Plugin API 文档
npm show @opencode-ai/plugin

# 2. 查看 OpenCode 安装目录结构
ls -la /Applications/OpenCode.app/Contents/Resources/

# 3. 检查是否有 plugin/hook 配置项
strings /Applications/OpenCode.app/Contents/Resources/app.asar | grep -i "hook\|plugin" | head -20
```

## 五、OpenCode 特有考量

### 多 Agent 支持

OpenCode 支持多个内置 Agent（通过 `agent` 字段区分）：

```json
{
  "opencodeAgent": "default",
  "agent": "opencode"
}
```

CCWhat 集成需要兼容不同 Agent 的行为差异。

### SQLite 数据库结构

OpenCode 将数据存储在 SQLite 中，表结构：

```sql
-- 主要表
session      -- 会话信息
message      -- 消息
part         -- 消息分段
project      -- 项目
```

CCWhat 可以通过监听数据库变化或轮询来检测命令。

## 六、相关文件

- 适配器实现：`ccwhat/adapters/opencode.py`
- 数据库路径：`~/.local/share/opencode/opencode.db`
