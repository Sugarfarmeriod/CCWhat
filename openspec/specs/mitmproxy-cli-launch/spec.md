## Purpose
Define how the proxy command launches mitmdump and reports proxy startup failures.
## Requirements
### Requirement: proxy 命令通过 mitmdump CLI 启动代理
`proxy` 子命令 SHALL 通过 `subprocess` 调用系统 `mitmdump` 命令启动代理，不使用 mitmproxy Python API。

#### Scenario: 正常启动
- **WHEN** 用户执行 `deep-ai-analysis proxy`
- **THEN** 系统调用 `mitmdump --listen-host 127.0.0.1 --listen-port 7788 -s <recorder.py路径>`，代理正常监听

#### Scenario: mitmdump 未安装时给出提示
- **WHEN** 系统中未安装 `mitmdump` 命令
- **THEN** 命令退出并提示用户执行 `brew install mitmproxy`

#### Scenario: 输出目录通过环境变量传递给 addon
- **WHEN** 用户指定 `--output /custom/path`
- **THEN** `DAA_OUTPUT_DIR` 环境变量设为该路径，`recorder.py` 从中读取输出目录

### Requirement: install.sh 通过 brew 安装 mitmproxy
`install.sh` SHALL 在安装 Python 包之前通过 `brew install mitmproxy` 安装 mitmproxy CLI。

#### Scenario: brew 可用时自动安装
- **WHEN** 系统中已安装 `brew`
- **THEN** 脚本执行 `brew install mitmproxy`，安装成功后继续安装 Python 包

#### Scenario: brew 不可用时给出提示
- **WHEN** 系统中未安装 `brew`
- **THEN** 脚本打印提示，跳过 mitmproxy 安装，继续安装 Python 包

### Requirement: Windows 启动 mitmdump
ccwhat SHALL 在 Windows 原生环境下通过 `mitmdump` CLI 启动本地代理。

#### Scenario: mitmdump 在 PATH 中
- **WHEN** Windows 用户运行 `ccwhat proxy` 或 `ccwhat -- codex`
- **THEN** 系统 SHALL 能从 PATH 找到并启动 `mitmdump`
- **AND** 启动命令 SHALL 使用 Windows 可接受的参数和路径

#### Scenario: mitmdump 未安装
- **WHEN** Windows 用户运行需要代理的命令但 `mitmdump` 不存在
- **THEN** 系统 SHALL 输出 Windows 可用的安装提示
- **AND** 提示不得只包含 Homebrew 命令

### Requirement: Windows 端口可绑定性
ccwhat SHALL 在启动 mitmdump 前验证目标端口可由当前进程绑定。

#### Scenario: Windows excluded port range
- **WHEN** 目标端口没有 listener 但 `bind()` 返回 `WinError 10013`
- **THEN** 系统 SHALL 拒绝启动代理
- **AND** 系统 SHALL 建议用户使用 `--port` 指定其他端口

#### Scenario: 普通 listener 占用
- **WHEN** 目标端口已有 listener
- **THEN** 系统 SHALL 保留现有 ccwhat-managed proxy 复用或非 ccwhat 占用报错语义
- **AND** 系统 SHALL 不把该场景误报为 Windows excluded port range

### Requirement: Windows CA 证书提示
ccwhat SHALL 为 Windows 用户提供 mitmproxy CA 信任提示。

#### Scenario: 代理启动输出证书路径
- **WHEN** Windows 用户启动代理
- **THEN** 系统 SHALL 输出 `mitmproxy-ca-cert.pem` 的路径
- **AND** 文档 SHALL 说明如何在 Windows 中信任该证书或临时只使用 `NODE_EXTRA_CA_CERTS`

