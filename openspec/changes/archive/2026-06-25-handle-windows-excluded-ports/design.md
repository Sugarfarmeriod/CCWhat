## Context

ccwhat 的代理和 viewer 都绑定本机端口。当前 `_proxy_port_in_use()` 这类检查只判断 `127.0.0.1:<port>` 是否有 listener，可以发现普通端口占用，但无法发现 Windows TCP excluded port range。

在 Windows 上，excluded port 没有 listener 时 `connect_ex()` 会返回未占用，但后续 `bind()` 会抛 `PermissionError` / `WinError 10013`。这会让 `ccwhat -- <cli>`、`ccwhat proxy`、`ccwhat discover` 和 viewer 启动进入泛化失败提示。

## Goals / Non-Goals

**Goals:**

- 在启动子进程或 viewer 之前，判断目标端口是否可被当前进程绑定。
- 对不可绑定端口输出明确诊断，包含端口、原因和换端口建议。
- 保持已有端口被 listener 占用时的行为和 ccwhat proxy 复用逻辑。
- 用单元测试覆盖 Windows `WinError 10013` 等不可绑定错误路径。

**Non-Goals:**

- 不修改默认端口 `7788` / `7789`。
- 不做自动寻找空闲端口，避免改变用户配置、代理环境变量和日志行为。
- 不调用 `netsh` 解析 excluded range；该命令平台相关且输出本地化，直接 bind probe 更可靠也更小。

## Decisions

1. 使用 socket bind probe 判断可绑定性。

   在没有 listener 的情况下，短暂创建 `AF_INET/SOCK_STREAM` socket 并尝试 `bind(("127.0.0.1", port))`。成功即说明端口可绑定；失败则返回结构化诊断。这个方案比解析 `netsh` 简单，也能覆盖非 excluded range 的权限拒绝。

2. 复用“端口是否已有 listener”的现有检查。

   bind probe 只在 `_proxy_port_in_use(port)` 为 false 时执行。这样如果已有 ccwhat-managed proxy 正在监听，仍按 marker 复用；如果非 ccwhat 进程占用，仍保留现有“port already in use”提示。

3. 将诊断辅助函数放在 `ccwhat/commands/run.py`，并在 proxy/discover 复用或局部保持同等逻辑。

   本次目标是外科手术式修复，不引入新的公共模块或依赖。若后续端口管理逻辑继续增长，再抽到 runtime/ports 或 shared CLI util。

## Risks / Trade-offs

- [Risk] bind probe 与后续真实服务 bind 之间存在极短竞态。  
  Mitigation: 这是预诊断，不替代真实启动错误处理；真实启动失败仍会保留兜底提示。

- [Risk] 直接 `bind()` 可能受防火墙、安全软件或权限策略影响。  
  Mitigation: 这些情况同样属于“当前端口不可绑定”，提示换端口仍是有效操作建议。

- [Risk] Windows 以外平台也可能返回不可绑定错误。  
  Mitigation: 提示文案保持通用，只在检测到 `WinError 10013` 时额外提及 Windows excluded port range。
