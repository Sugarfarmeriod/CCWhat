### Requirement: Launch mc with proxy environment
`start-mc` 子命令 SHALL 在注入 `HTTPS_PROXY` 和 `NODE_EXTRA_CA_CERTS` 环境变量后，以子进程方式执行 `mc --code`，继承当前终端的 stdin/stdout/stderr。

#### Scenario: Default launch
- **WHEN** 用户执行 `deep-ai-analysis start-mc`
- **THEN** 系统以 `HTTPS_PROXY=http://127.0.0.1:7788` 和 `NODE_EXTRA_CA_CERTS=<home>/.mitmproxy/mitmproxy-ca-cert.pem` 启动 `mc --code`，mc 的输入输出直接与当前终端交互

#### Scenario: Custom port
- **WHEN** 用户执行 `deep-ai-analysis start-mc --port 9000`
- **THEN** 系统以 `HTTPS_PROXY=http://127.0.0.1:9000` 启动 `mc --code`

#### Scenario: mc exits with non-zero code
- **WHEN** `mc --code` 以非 0 退出码退出
- **THEN** `deep-ai-analysis start-mc` 以相同的退出码退出

### Requirement: mc not found error
`start-mc` 子命令 SHALL 在 `mc` 命令不在 PATH 时打印友好错误信息并以非 0 退出。

#### Scenario: mc not installed
- **WHEN** 用户执行 `deep-ai-analysis start-mc` 且系统中不存在 `mc` 命令
- **THEN** 系统打印错误信息（"mc command not found. Please install mc first."）并以退出码 1 退出

### Requirement: CA certificate warning
`start-mc` 子命令 SHALL 在 CA 证书文件不存在时打印警告，但仍继续启动 `mc --code`。

#### Scenario: CA cert missing
- **WHEN** 用户执行 `deep-ai-analysis start-mc` 且 `~/.mitmproxy/mitmproxy-ca-cert.pem` 不存在
- **THEN** 系统向 stderr 打印警告（提示先运行 `deep-ai-analysis proxy` 生成证书），然后继续以注入的环境变量启动 `mc --code`
