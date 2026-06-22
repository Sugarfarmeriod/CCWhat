# Task Agent Slash Command Integration Design

## 背景

Runtime Task Dataset 需要用户在 Coding Agent 运行过程中手动标记 Task 边界。交互目标不是让用户记住并手打长命令，而是让 CCWhat 命令出现在 Agent 原生 slash command 菜单中：

```text
/ccwhat:start
/ccwhat:finish
/ccwhat:abort
/ccwhat:status
/ccwhat:note
```

用户通过 `ccwhat -- <agent>` 启动 Codex、OpenCode 或 Claude Code 后，应在该 Agent 的 slash 菜单里看到 CCWhat 命令。命令执行后应优先调用 CCWhat 本地后台程序，标记 Task 边界并更新 runtime Dataset staging。

核心约束：

```text
菜单必须原生可见。
Task 边界命令默认不发送给云端模型。
命令不应污染 Agent 对话上下文。
能不落进 Agent 自身 session log 就不落。
如果某个 Agent 做不到完全无痕，必须显式标记证据来源和置信度。
```

## 调研结论

### Codex

官方文档确认：

- Codex CLI 有 slash command 菜单，用于控制交互式会话。
- Codex 支持自定义 prompt/skills 作为可复用 workflow，并可通过 slash command 或 skill 方式显式调用。
- Codex 支持 lifecycle hooks，包括 `UserPromptSubmit`，该 hook 能在 prompt 发送前运行，并可以返回 `decision: "block"` 阻止 prompt。
- Codex hooks 可来自用户、项目、插件等配置层；插件也可以打包 hooks。

相关官方文档：

- https://developers.openai.com/codex/cli/slash-commands
- https://developers.openai.com/codex/custom-prompts
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/plugins/build

结论：

```text
Codex 可以实现“菜单可见 + 提交前本地 hook block”的方案。
官方没有确认自定义 slash command 可以直接绑定本地程序且完全跳过 prompt 机制。
所以 Codex 第一方案是：用 prompt/skill 注册菜单项，再用 UserPromptSubmit hook 捕获 marker 并 block。
```

### Claude Code

官方文档确认：

- Claude Code skills/custom commands 会出现在 slash 命令体系中。
- `.claude/commands/<name>.md` 和 `.claude/skills/<name>/SKILL.md` 都可以创建 slash command。
- Claude Code hooks 支持 `UserPromptSubmit`，可在 prompt 被处理前 block，并可设置 `suppressOriginalPrompt`。
- Claude Code hooks 还支持 `UserPromptExpansion`，该事件专门覆盖用户直接输入 slash command 的路径，能看到 `command_name`、`command_args`、`command_source` 和原始 prompt，并可以 block expansion。
- 官方说明 `decision: "block"` 可防止 prompt 被处理，并从上下文中擦除；`suppressOriginalPrompt` 可避免 block 提示中展示原始 prompt。

相关官方文档：

- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/hooks

结论：

```text
Claude Code 是三者中最适合做“原生菜单 + 本地拦截”的。
推荐用 skill/custom command 注册菜单项，用 UserPromptExpansion hook 捕获 /ccwhat:* 并 block expansion。
必要时再用 UserPromptSubmit hook 做兜底。
```

### OpenCode

官方文档确认：

- OpenCode 支持自定义 commands，创建 `.opencode/commands/<name>.md` 或在 config 的 `command` 字段声明。
- OpenCode custom commands 的文档明确说 template 是要发送给 LLM 的 prompt。
- OpenCode 支持 plugins，插件能订阅事件，包括 `command.executed`、`tui.command.execute`、`message.updated`、`tool.execute.before/after`、`session.*` 等。
- OpenCode TUI 启动时会启动 server，server API 支持列出 commands，也支持执行 slash command。
- OpenCode skills 会被 Agent 通过 native skill tool 加载，偏向 Agent 能力扩展，不等价于本地控制命令。

相关官方文档：

- https://opencode.ai/docs/commands/
- https://opencode.ai/docs/plugins/
- https://opencode.ai/docs/server/
- https://opencode.ai/docs/skills/

结论：

```text
OpenCode custom command 原生是 prompt-based，会发送给 LLM。
要实现“菜单可见 + 不发模型”，需要用 OpenCode plugin 事件做拦截。
当前官方文档显示存在 command/tui/message 事件，但需要实测 command.executed 或 tui.command.execute 是否能在 prompt 发送前阻止默认行为。
如果不能阻止，OpenCode 需要 CCWhat PTY 拦截作为硬兜底，或接受降级证据来源。
```

## 统一产品决策

### 决策 1：必须注册进原生 slash 菜单

CCWhat runtime recording 不接受“用户记住命令并手打”为主路径。

用户通过 `ccwhat -- <agent>` 启动 Agent 后，应能输入 `/` 并看到 CCWhat 命令。

### 决策 2：允许修改 Agent 配置

为了最终目标，可以写入三类 Agent 的配置或命令目录：

```text
Codex:
  ~/.codex/prompts/
  ~/.codex/skills/
  ~/.codex/hooks.json
  Codex plugin marketplace / local plugin

Claude Code:
  ~/.claude/commands/
  ~/.claude/skills/
  hooks settings

OpenCode:
  ~/.config/opencode/commands/
  ~/.config/opencode/plugins/
  ~/.config/opencode/skills/
  project-local .opencode/
```

但所有写入都必须：

- 可重复执行
- 可升级
- 可卸载
- 记录由 CCWhat 管理
- 尽量避免覆盖用户同名文件

### 决策 3：命令语义统一

三类 Agent 的菜单命令统一为：

```text
/ccwhat:start <title>
/ccwhat:finish
/ccwhat:abort
/ccwhat:status
/ccwhat:note <text>
```

如果某个 Agent 不支持带冒号的 command name，可降级为等价命名：

```text
/ccwhat-start
/ccwhat-finish
/ccwhat-abort
/ccwhat-status
/ccwhat-note
```

降级命名必须在菜单描述中保持一致：

```text
CCWhat: start task recording
CCWhat: finish current task
```

### 决策 4：默认不发送云端

命令执行目标是 CCWhat 本地 runtime controller：

```text
/ccwhat:start 修复导出
  -> Agent 原生菜单选中
  -> 触发 command/prompt/skill/hook path
  -> CCWhat adapter 捕获
  -> 调用 runtime run controller
  -> 阻止默认 prompt 发送
```

如果某个 Agent 官方机制不能在发送前阻止，必须降级标记：

```json
{
  "boundary_source": "agent_visible_command",
  "model_visible": true,
  "confidence": "medium"
}
```

强证据路径必须标记：

```json
{
  "boundary_source": "ccwhat_local_command",
  "model_visible": false,
  "confidence": "high"
}
```

## 目标架构

```text
ccwhat -- <agent>
  |
  |-- ensure agent integration installed
  |     |-- menu command files / skills / plugin
  |     |-- hook or plugin interceptor
  |
  |-- create runtime run
  |     |-- run_id
  |     |-- control socket / local route
  |     |-- proxy/viewer ports
  |
  |-- launch Agent
        |
        |-- user selects native slash command
        |-- integration calls CCWhat local route
        |-- default prompt path is blocked
```

## Agent 适配方案

### Claude Code 方案

推荐方案：

```text
菜单注册：
  写入 .claude/commands 或 .claude/skills

本地拦截：
  UserPromptExpansion hook

兜底：
  UserPromptSubmit hook
```

菜单文件示意：

```text
~/.claude/commands/ccwhat-start.md
~/.claude/commands/ccwhat-finish.md
~/.claude/commands/ccwhat-abort.md
~/.claude/commands/ccwhat-status.md
~/.claude/commands/ccwhat-note.md
```

每个 command 文件只需要提供描述和最小 marker，不承担真实逻辑。真实逻辑在 hook 中完成。

Hook 行为：

```text
if command_name in ccwhat commands:
  parse command_args
  call ccwhat runtime controller
  return decision:block
  suppress original prompt where supported
```

预期结果：

- 出现在 Claude Code 原生 slash 菜单。
- 命令不会展开成给 Claude 的 prompt。
- CCWhat 本地记录 Task 边界。
- Dataset 标记 `model_visible=false`。

风险点：

- `UserPromptExpansion` 的 block 是否会写入 transcript，需要实测。
- block reason 是否会显示给用户，需要控制成简洁成功提示。

### Codex 方案

推荐方案：

```text
菜单注册：
  Codex prompt/skill/plugin 让命令出现在 slash 菜单

本地拦截：
  UserPromptSubmit hook 捕获 CCWhat marker 并 block
```

命令内容采用 marker 模板：

```text
CCWHAT_CONTROL_COMMAND start {{args}}
```

Hook 行为：

```text
if prompt starts with CCWHAT_CONTROL_COMMAND:
  parse action and args
  call ccwhat runtime controller
  return decision:block
```

预期结果：

- 出现在 Codex slash 菜单。
- prompt 在发送模型前被 hook block。
- CCWhat 本地记录 Task 边界。

风险点：

- Codex 文档确认 `UserPromptSubmit` 可以 block prompt，但没有明确说明 block 后 transcript 中是否完全无痕。
- Codex custom prompt/skill 是否能保留原始 args 并稳定生成 marker，需要实测。
- 如果 skills 进入模型选择流程而不是纯 prompt expansion，可能需要用 deprecated custom prompts 或 plugin 打包来确保菜单项可见。

### OpenCode 方案

推荐方案需要实测后定稿：

```text
菜单注册：
  .opencode/commands 或 config.command

本地拦截候选：
  OpenCode plugin: command.executed
  OpenCode plugin: tui.command.execute
  OpenCode server command route
  CCWhat PTY wrapper fallback
```

命令内容采用 marker 模板：

```text
CCWHAT_CONTROL_COMMAND start {{args}}
```

理想 plugin 行为：

```text
if command is ccwhat command:
  call ccwhat runtime controller
  prevent default prompt execution
  show TUI toast / status message
```

风险点：

- OpenCode 文档明确 custom command template 会发送给 LLM。
- 官方 plugin event 列表中有 command/tui 事件，但文档片段未确认这些事件能 cancel 或 prevent default。
- 如果 plugin 只能 observe 不能 cancel，必须采用 PTY wrapper 拦截，或接受 OpenCode 第一版 `model_visible=true` 降级。

OpenCode 必做 spike：

```text
1. 创建 .opencode/commands/ccwhat-start.md
2. 创建 .opencode/plugins/ccwhat.js
3. 在 plugin 中监听 command.executed 和 tui.command.execute
4. 验证能否阻止 custom command prompt 发送给 LLM
5. 验证命令是否进入 OpenCode session log
```

## 安装和注册策略

### 安装时机

`ccwhat -- <agent>` 启动前执行：

```text
ensure_agent_slash_integration(agent)
```

该函数负责：

- 检查对应 Agent 的 CCWhat 命令是否存在。
- 检查版本 hash 是否匹配当前 CCWhat。
- 缺失时写入。
- 过期时升级。
- 冲突时提示用户。

### 管理标记

所有写入文件都包含 CCWhat 管理标记：

```text
<!-- managed-by: ccwhat -->
<!-- ccwhat-version: 2.x -->
<!-- ccwhat-integration-version: runtime-slash-v1 -->
```

JSON/TOML 配置则写入等价字段：

```json
{
  "managed_by": "ccwhat",
  "integration_version": "runtime-slash-v1"
}
```

### 冲突处理

如果用户已有同名命令：

```text
/ccwhat:start
/ccwhat-start
```

且不是 CCWhat 管理文件，不覆盖。启动时报错：

```text
CCWhat cannot install slash command /ccwhat:start because it already exists.
Move or rename the existing command, or run:
  ccwhat integrations doctor
```

### 卸载

提供：

```bash
ccwhat integrations uninstall --agent codex
ccwhat integrations uninstall --agent claude
ccwhat integrations uninstall --agent opencode
ccwhat integrations uninstall --all
```

只删除 CCWhat 管理标记匹配的文件。

## Runtime Controller 接口

所有 Agent integration 最终调用同一套本地接口。

推荐第一版用 Unix domain socket：

```text
~/.ccwhat/runtime-runs/<run-id>/control.sock
```

命令 payload：

```json
{
  "command": "start",
  "args": "修复 dataset runtime recording",
  "source": {
    "agent": "claude",
    "integration": "claude-user-prompt-expansion",
    "model_visible": false
  }
}
```

返回：

```json
{
  "ok": true,
  "message": "CCWhat: started task-001",
  "task_id": "task-001"
}
```

如果 Agent hook/plugin 不方便访问 Unix socket，可降级为 localhost HTTP：

```text
POST http://127.0.0.1:<control-port>/runtime/command
```

control port 仍写入 `run.json`，不暴露给普通用户。

## 证据记录要求

每次 slash command invocation 都写入：

```text
tasks/<task-id>/control_events.jsonl
```

示例：

```json
{
  "time": "2026-06-22T16:31:12+08:00",
  "command": "start",
  "raw_args": "修复导出",
  "agent": "claude",
  "integration": "claude-user-prompt-expansion",
  "model_visible": false,
  "agent_log_visible": false,
  "confidence": "high"
}
```

如果发生降级：

```json
{
  "integration": "opencode-visible-command-fallback",
  "model_visible": true,
  "agent_log_visible": true,
  "confidence": "medium"
}
```

## 需要实测确认的关键点

### P0：Claude Code block 是否完全不污染 transcript

需要确认：

- `UserPromptExpansion` block 后，原始 `/ccwhat:start` 是否写入 transcript。
- `suppressOriginalPrompt` 是否能用于 slash expansion 路径。
- block reason 是否会作为用户可见消息落盘。

### P0：Codex hook block 后 transcript 行为

需要确认：

- marker prompt 被 `UserPromptSubmit` block 后是否写入 transcript。
- slash menu 中 custom prompt/skill 是否能稳定传 args。
- plugin-bundled hook 是否能随 CCWhat 自动安装并被信任。

### P0：OpenCode plugin 是否能 cancel command execution

需要确认：

- `command.executed` 是 before 还是 after。
- `tui.command.execute` 是否能 prevent default。
- plugin 抛错是否阻止 prompt 发送，还是只显示错误。
- custom command marker 是否会写入 session log。

### P1：命名限制

需要确认三类 Agent 是否都允许命令名包含冒号：

```text
/ccwhat:start
```

如果不允许，统一降级为：

```text
/ccwhat-start
```

## 实施顺序

### Phase 1：spike 验证

目标：确认三类 Agent 的菜单注册和本地 block 能力。

产物：

- Claude Code 最小 command + hook demo
- Codex 最小 command/skill + hook demo
- OpenCode 最小 command + plugin demo
- 一张兼容性矩阵

兼容性矩阵：

| Agent | 菜单可见 | 可本地执行 | 可阻止模型发送 | 不写 Agent log | 推荐路径 |
| --- | --- | --- | --- | --- | --- |
| Claude Code | 待测 | 待测 | 待测 | 待测 | command/skill + UserPromptExpansion |
| Codex | 待测 | 待测 | 待测 | 待测 | prompt/skill + UserPromptSubmit |
| OpenCode | 待测 | 待测 | 待测 | 待测 | command + plugin / PTY fallback |

### Phase 2：CCWhat integration installer

新增：

```bash
ccwhat integrations install --agent claude
ccwhat integrations install --agent codex
ccwhat integrations install --agent opencode
ccwhat integrations doctor
```

并在：

```bash
ccwhat -- <agent>
```

启动时自动 ensure 对应 integration 已安装。

### Phase 3：Runtime controller

新增：

- run registry
- control socket
- `/ccwhat:start` route
- `/ccwhat:finish` route
- control event logging
- Dataset task boundary 写入

### Phase 4：三类 Agent 正式适配

按 spike 结果实现：

- Claude adapter
- Codex adapter
- OpenCode adapter

每个 adapter 都必须报告自身能力：

```json
{
  "agent": "claude",
  "menu_visible": true,
  "model_visible": false,
  "agent_log_visible": false,
  "confidence": "high"
}
```

## 推荐最终方案

当前最稳的总体方案是：

```text
原生菜单入口必须做。
菜单注册可以改 Agent 配置。
真实执行统一走 CCWhat runtime controller。
Claude 优先用 UserPromptExpansion block。
Codex 优先用 UserPromptSubmit block。
OpenCode 先 spike plugin cancel；不行则 PTY fallback 或 medium-confidence visible fallback。
所有路径都写 evidence source，不把降级路径伪装成 high-confidence runtime evidence。
```

## 不开放的问题

以下问题已按当前产品目标收口：

- 是否要求原生菜单：要求。
- 是否允许修改 Agent 配置：允许。
- 是否默认发送云端：不允许。
- 是否接受用户手打作为主路径：不接受。
- 是否要同时支持三类 Agent：要。

## 仍需决策的问题

### 1. 命令名冒号降级

如果某个 Agent 不支持 `/ccwhat:start` 这种冒号命令名，是否接受统一改为 `/ccwhat-start`？

推荐：接受。菜单描述仍保持 CCWhat namespace。

### 2. OpenCode 降级策略

如果 OpenCode 无法在 prompt 发送前 cancel custom command，是否接受第一版 OpenCode 标记为：

```json
"model_visible": true,
"confidence": "medium"
```

推荐：短期可接受，但必须作为 P0 后续优化，因为自动归因核心数据最好保持本地强证据。

### 3. 自动写入全局配置还是项目配置

推荐：

```text
默认写用户级全局配置，保证所有项目都可用。
项目级配置作为高级选项。
```

原因：

- 用户是通过 CCWhat 启动 Agent，不是每个 repo 单独安装。
- runtime recording 是 CCWhat 的产品能力，不是某个 repo 的业务规则。

