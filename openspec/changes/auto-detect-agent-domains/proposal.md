## Why

用户当前必须在启动 ccwhat 前执行 `ccwhat setup` 手动填写录制 domain，门槛过高且容易遗漏。各主流 coding agent（opencode、claude、codex）本身已在固定路径的配置文件中存储了 API 网关地址，ccwhat 完全可以自动读取，实现真正的零配置启动。

## What Changes

- **新增** `ccwhat/agent_config.py` 模块，负责按 agent 名读取其配置文件，提取所有 provider 的 baseURL 并返回 domain 列表
- **修改** `ccwhat/commands/run.py`：当 `~/.ccwhat/config.toml` 未配置 domain 时，自动调用上述模块填充录制 domain，跳过 setup wizard
- 支持三个 agent 的配置读取：
  - **opencode**：`~/.config/opencode/opencode.jsonc`，提取 `provider.*.options.baseURL` 全量 domain
  - **claude**：`~/.claude/settings.json`，提取 `env.ANTHROPIC_BASE_URL`，无则回退 `api.anthropic.com`
  - **codex**：`~/.codex/config.toml`，提取 `shell_environment_policy.set` 中 `*_BASE_URL` 字段，无则回退 `api.openai.com`
- `ccwhat setup` 命令保留，作为高级用户手动覆盖配置的入口

## Capabilities

### New Capabilities

- `agent-config-reader`：从各 coding agent 的配置文件路径自动解析 API baseURL，返回录制所需的 domain 列表

### Modified Capabilities

- `proxy-interceptor`：录制 domain 的来源从「用户在 config.toml 手动配置」扩展为「优先读 config.toml，其次自动从 agent 配置文件提取」

## Impact

- **新增文件**：`ccwhat/agent_config.py`
- **修改文件**：`ccwhat/commands/run.py`（domain 填充逻辑）
- **不影响**：录制器 `ccwhat/addons/recorder.py`、viewer、setup 命令、现有 config.toml 格式
- **依赖**：opencode 配置为 JSONC 格式（含注释），需在解析前剥离注释；codex 配置为 TOML 格式，直接用 `tomllib` 读取
