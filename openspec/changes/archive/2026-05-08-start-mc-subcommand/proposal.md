## Why

使用 `deep-ai-analysis proxy` 拦截流量后，还需手动配置 `HTTPS_PROXY` 和 `NODE_EXTRA_CA_CERTS` 才能让 `mc`（Meituan Claude CLI）的流量经过代理。`start-mc` 子命令将这两步合并为一条命令，自动注入所需环境变量后启动 `mc --code`。

## What Changes

- 新增 `start-mc` 子命令，执行以下操作：
  - 设置 `HTTPS_PROXY=http://127.0.0.1:<port>`（端口与 proxy 子命令默认值一致，默认 7788，可覆盖）
  - 设置 `NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem`（绝对路径）
  - 在注入环境变量的子进程中执行 `mc --code`，继承当前终端的 stdin/stdout/stderr
- 在 `cli.py` 中注册 `start-mc` 子命令

## Capabilities

### New Capabilities

- `start-mc`: `start-mc` 子命令——注入代理环境变量并启动 `mc --code`

### Modified Capabilities

- `cli-framework`: 新增 `start-mc` 子命令注册到主命令组

## Impact

- **新增文件**: `deep_ai_analysis/commands/start_mc.py`
- **修改文件**: `deep_ai_analysis/cli.py`（注册新子命令）
- **外部依赖**: 系统中需已安装 `mc` 命令；`~/.mitmproxy/mitmproxy-ca-cert.pem` 需存在（运行 `proxy` 子命令后自动生成）
- **无破坏性变更**
