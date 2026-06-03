## Why

当前 `proxy` 命令的 `--output` 默认值为 `./logs`（相对路径），依赖当前工作目录，不同目录启动会导致日志分散。`web-server` 的 `--logs-dir` 同理。需要统一使用用户主目录下的固定位置，便于日志集中管理，同时保持可配置性。

## What Changes

- `proxy` 命令的 `--output` 默认值改为 `~/.deep-ai-analysis/raw-req-resp`
- `web-server` 命令的 `--logs-dir` **重命名为 `--req-resp-dir`**，默认值同步改为 `~/.deep-ai-analysis/raw-req-resp`，更明确表达其为原始 HTTP 请求/响应数据目录，避免与 Claude Log 页面混淆
- 在 `deep_ai_analysis/config.py` 中定义常量 `DEFAULT_RAW_LOG_DIR`，两处命令共享同一默认值

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `proxy-interceptor`: `--output` 默认值改为 `~/.deep-ai-analysis/raw-req-resp`
- `session-viewer`: `web-server --logs-dir` 默认值同步

## Impact

- `deep_ai_analysis/config.py`：新增 `DEFAULT_RAW_LOG_DIR` 常量
- `deep_ai_analysis/commands/proxy.py`：`--output` 默认值引用常量
- `deep_ai_analysis/commands/web_server.py`：`--logs-dir` 重命名为 `--req-resp-dir`，默认值引用常量
- `README.md`：更新两处默认路径说明
