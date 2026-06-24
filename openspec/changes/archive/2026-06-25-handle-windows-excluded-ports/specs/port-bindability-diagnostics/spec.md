## ADDED Requirements

### Requirement: 启动前诊断不可绑定端口
ccwhat 在启动本机代理或 viewer 前，SHALL 在端口没有 listener 时验证该端口是否可被当前进程绑定。

#### Scenario: 端口没有 listener 且可绑定
- **WHEN** 用户启动需要监听本机端口的 ccwhat 命令，且目标端口没有 listener 并可成功 `bind()`
- **THEN** 系统 SHALL 继续原有启动流程

#### Scenario: 端口没有 listener 但不可绑定
- **WHEN** 用户启动需要监听本机端口的 ccwhat 命令，且目标端口没有 listener 但 `bind()` 抛出 `OSError`
- **THEN** 系统 SHALL 以非 0 状态退出或拒绝启动该服务
- **AND** 错误信息 SHALL 说明该端口不可绑定，而不是仅提示端口被占用或 mitmproxy 未安装

### Requirement: Windows excluded port range 提示
当不可绑定错误表现为 Windows `WinError 10013` 时，ccwhat SHALL 在错误提示中说明该端口可能处于 Windows TCP excluded port range，并给出检查和换端口建议。

#### Scenario: Windows WinError 10013
- **WHEN** bind probe 或服务启动失败得到 `WinError 10013`
- **THEN** 错误信息 SHALL 包含 `WinError 10013`
- **AND** 错误信息 SHALL 提示用户可运行 `netsh interface ipv4 show excludedportrange protocol=tcp` 检查 excluded port range
- **AND** 错误信息 SHALL 提示使用 `--port` 或 `--web-port` 指定其他端口

### Requirement: 保留已有端口占用语义
ccwhat SHALL 保留现有 listener 检测语义；如果端口已有 listener，系统 SHALL 继续执行现有 ccwhat-managed proxy 复用或非 ccwhat 进程占用报错逻辑。

#### Scenario: 已有 ccwhat-managed proxy
- **WHEN** `ccwhat -- <cli>` 启动时发现目标代理端口已有 listener 且 marker 指向存活的 ccwhat-managed proxy
- **THEN** 系统 SHALL 复用该代理，不执行 bind probe

#### Scenario: 已有非 ccwhat listener
- **WHEN** `ccwhat -- <cli>` 启动时发现目标代理端口已有 listener 但不是兼容的 ccwhat-managed proxy
- **THEN** 系统 SHALL 保留现有端口占用错误提示，不执行 bind probe
