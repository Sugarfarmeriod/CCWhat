## MODIFIED Requirements

### Requirement: Start proxy server
`proxy` 子命令 SHALL 启动绑定到 `127.0.0.1` 的 HTTP/HTTPS 代理服务器，代理实现可使用外部 `mitmdump` CLI 或 mitmproxy Python API，但用户入口 SHALL 为 `ccwhat proxy`。

#### Scenario: Start with default port
- **WHEN** 用户执行 `ccwhat proxy`
- **THEN** 系统在默认端口 7788 启动代理，打印代理地址（如 `Proxy listening on http://127.0.0.1:7788`）、记录范围和 CA 证书安装指引

#### Scenario: Start with custom port
- **WHEN** 用户执行 `ccwhat proxy --port 9090`
- **THEN** 系统在端口 9090 启动代理

#### Scenario: mitmproxy not installed
- **WHEN** 代理运行依赖不可用，用户执行 `ccwhat proxy`
- **THEN** 系统打印安装指引并以非 0 退出码退出

#### Scenario: Port already in use
- **WHEN** 指定端口已被占用且不是兼容的 ccwhat proxy，用户执行 `ccwhat proxy --port 7788`
- **THEN** 系统打印端口冲突错误信息并以非 0 退出码退出

### Requirement: Domain filtering
域名过滤列表 SHALL 来自 CLI 选项、持久化配置或 preset 展开结果。仅匹配 allowlist 且满足 path/content-type 规则的请求和响应被记录，其他流量被代理但不记录 payload。

#### Scenario: Configured domain filter applied
- **WHEN** 用户配置 `api.anthropic.com` 并执行 `ccwhat proxy`
- **THEN** 仅符合配置规则的 `api.anthropic.com` 请求/响应被写入日志，其他域名流量被代理但不记录 payload

#### Scenario: Non-matching domain not recorded
- **WHEN** 经过代理的请求目标域名不在过滤列表中
- **THEN** 该请求被正常代理转发，但不生成 payload 日志记录

#### Scenario: Multiple configured domains
- **WHEN** 配置包含 `["api.anthropic.com", "gateway.example.com"]`
- **THEN** 两个域名中符合 path/content-type 规则的请求/响应均可被记录

#### Scenario: Empty domain filter rejected
- **WHEN** 用户执行 `ccwhat proxy` 且没有任何配置、preset 或 CLI domain
- **THEN** 代理不进入 payload 记录模式
- **AND** 交互模式启动 onboarding，非交互模式输出安全错误

#### Scenario: CLI domain overrides config
- **WHEN** 用户执行 `ccwhat proxy --domain gateway.example.com`
- **THEN** 本次代理使用 `gateway.example.com` 作为记录域名
- **AND** 不使用与本次命令冲突的持久化 domain 配置

### Requirement: Record raw request and response
代理 addon SHALL 在 mitmproxy 的 `response` 钩子中将匹配记录规则的请求和响应原始内容以 JSONL 格式追加到对应 session 子目录下的当天日志文件。记录 headers 时，SHALL 过滤敏感 header；记录 body 时，SHALL 应用大小限制。

日志路径格式为 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl`。sessionId 优先从请求 header `X-Claude-Code-Session-Id` 提取；不存在时使用本次 `ccwhat run` 或 `ccwhat proxy` 进程生成的本地 session id。

#### Scenario: Default output directory
- **WHEN** 用户执行 `ccwhat proxy`（不带 `--output`）
- **THEN** 日志写入 `~/.ccwhat/raw-req-resp/<sessionId>/YYYY-MM-DD.jsonl`；目录不存在时自动创建

#### Scenario: Custom output directory
- **WHEN** 用户执行 `ccwhat proxy --output ~/my-logs`
- **THEN** 日志写入 `~/my-logs/<sessionId>/YYYY-MM-DD.jsonl`；目录不存在时自动创建

#### Scenario: Record standard HTTP response
- **WHEN** 一个匹配记录规则的 HTTP 请求完成（非 SSE）
- **THEN** 一条 JSON 记录被追加到 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl`，包含：请求时间戳（ISO8601）、URL、HTTP 方法、已脱敏请求 headers、请求 body、响应状态码、已脱敏响应 headers、响应 body、`is_sse: false`

#### Scenario: Log path includes Claude session ID
- **WHEN** 代理收到携带 `X-Claude-Code-Session-Id` header 的请求
- **THEN** 日志写入 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl`

#### Scenario: Log path fallback uses local session ID
- **WHEN** 请求不携带 `X-Claude-Code-Session-Id` header
- **THEN** 日志写入 `<output_dir>/<localSessionId>/YYYY-MM-DD.jsonl`
- **AND** 不再把所有未知 session 混写到固定 `unknown` 目录

#### Scenario: Sensitive headers excluded from log
- **WHEN** 请求或响应携带敏感 header（如 `Authorization`、`Cookie`、`Set-Cookie`、`X-Api-Key`、`Proxy-Authorization` 或 header 名包含 `token`、`secret`、`key`）
- **THEN** 写入 JSONL 的记录中对应 header 值被移除或替换为 redacted 标记

#### Scenario: JSONL append mode
- **WHEN** 同一 session 同一天内有多条请求被记录
- **THEN** 所有记录追加写入同一个 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl` 文件，每条记录占一行，文件内容为合法的 JSONL 格式

#### Scenario: Output directory auto-creation
- **WHEN** `<output_dir>/<sessionId>/` 目录不存在
- **THEN** 自动创建该目录

#### Scenario: Log file auto-rotation
- **WHEN** 代理运行跨越午夜（日期变更）
- **THEN** 新的请求写入新日期对应的 `YYYY-MM-DD.jsonl` 文件

#### Scenario: Body size limit applied
- **WHEN** 请求或响应 body 超过配置的最大持久化大小
- **THEN** 写入 JSONL 的 body 被截断
- **AND** 记录包含截断标记和可获得的原始大小信息

### Requirement: SSE stream recording
代理 addon SHALL 检测并记录匹配规则的 SSE（Server-Sent Events）流式响应，连接关闭后将完整记录作为一行追加到 JSONL 文件。记录 headers 和 body 时，SHALL 应用脱敏和大小限制。

#### Scenario: Detect SSE response
- **WHEN** 响应头包含 `content-type: text/event-stream`
- **THEN** addon 识别该响应为 SSE 流，为该 flow 启用流式记录模式

#### Scenario: Buffer SSE events in memory
- **WHEN** SSE 连接活跃且新的 chunk 到达
- **THEN** addon 解析 chunk 中完整的 SSE 事件（以 `\n\n` 为边界），将每个完整事件追加到该 flow 的内存缓冲 `sse_events` 列表

#### Scenario: Partial SSE chunk buffering
- **WHEN** 接收到的 chunk 末尾不以 `\n\n` 结尾（事件边界不完整）
- **THEN** addon 将不完整部分存入该 flow 的 per-flow 缓冲区，等待后续 chunk 合并后再解析

#### Scenario: SSE session complete — write to JSONL
- **WHEN** SSE 连接关闭（flow 完成）
- **THEN** 将完整记录作为一行 JSON 追加到当天 JSONL 文件：`is_sse: true`，`sse_events` 包含本次连接所有完整事件的原始文本列表，`response.body` 为所有事件拼接后的内容，headers 已脱敏，超限内容已截断

#### Scenario: SSE sensitive headers redacted
- **WHEN** SSE 请求或响应携带敏感 header
- **THEN** 写入 JSONL 的 SSE 记录中对应 header 值被移除或替换为 redacted 标记

### Requirement: CA certificate guidance
代理启动和 run 启动时 SHALL 向用户打印 mitmproxy CA 证书的路径和安装指引，以便用户信任 HTTPS 解密。

#### Scenario: Display certificate path on startup
- **WHEN** 用户执行 `ccwhat proxy` 且代理成功启动
- **THEN** 系统打印 CA 证书文件路径（`~/.mitmproxy/mitmproxy-ca-cert.pem`）和系统安装提示

#### Scenario: Display certificate path from launch
- **WHEN** 用户执行 `ccwhat -- <command...>` 且需要用户信任 CA
- **THEN** 系统打印 CA 证书文件路径和适用于当前平台的安装提示

### Requirement: Graceful shutdown
代理 SHALL 在收到 SIGINT（Ctrl+C）时完成当前活跃流的记录后再退出。

#### Scenario: SIGINT shutdown
- **WHEN** 用户按下 Ctrl+C
- **THEN** 系统打印关闭提示，代理停止接受新连接，等待当前活跃 SSE flow 写入完毕（最多 5 秒），然后以退出码 0 退出
