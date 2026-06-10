## ADDED Requirements

### Requirement: Start proxy server
`proxy` 子命令 SHALL 在当前 Python 进程内通过 `mitmproxy.tools.dump.DumpMaster` 启动 HTTP/HTTPS 代理服务器，使用 `asyncio.run()` 驱动事件循环。

#### Scenario: Start with default port
- **WHEN** 用户执行 `deep-ai-analysis proxy`
- **THEN** 系统在默认端口 7788 启动代理，打印代理地址（如 `Proxy listening on http://127.0.0.1:7788`）和 CA 证书安装指引

#### Scenario: Start with custom port
- **WHEN** 用户执行 `deep-ai-analysis proxy --port 9090`
- **THEN** 系统在端口 9090 启动代理

#### Scenario: mitmproxy not installed
- **WHEN** `mitmproxy` 包未安装，用户执行 `deep-ai-analysis proxy`
- **THEN** 系统打印安装指引（`pip install mitmproxy`）并以非 0 退出码退出

#### Scenario: Port already in use
- **WHEN** 指定端口已被占用，用户执行 `deep-ai-analysis proxy --port 7788`
- **THEN** 系统打印端口冲突错误信息并以非 0 退出码退出

### Requirement: Domain filtering
域名过滤列表 SHALL 在代码中以常量数组配置，默认值为 `["api.example.com"]`，不作为 CLI 参数暴露。仅匹配域名的请求和响应被记录，其他域名流量被代理但不记录。

#### Scenario: Default domain filter applied
- **WHEN** 用户执行 `deep-ai-analysis proxy`，有请求经过代理
- **THEN** 仅 `api.example.com` 的请求/响应被写入日志，其他域名流量被代理但不记录

#### Scenario: Non-matching domain not recorded
- **WHEN** 经过代理的请求目标域名不在过滤列表中
- **THEN** 该请求被正常代理转发，但不生成任何日志记录

#### Scenario: Multiple configured domains
- **WHEN** 代码中 `RECORD_DOMAINS` 配置为 `["api.example.com", "other.example.com"]`
- **THEN** 两个域名的请求/响应均被记录

### Requirement: Record raw request and response
代理 addon SHALL 在 mitmproxy 的 `response` 钩子中将完整的请求和响应原始内容以 JSONL 格式追加到当天日志文件。

#### Scenario: Record standard HTTP response
- **WHEN** 一个匹配过滤域名的 HTTP 请求完成（非 SSE）
- **THEN** 一条 JSON 记录被追加到 `logs/YYYY-MM-DD.jsonl`，包含：请求时间戳（ISO8601）、URL、HTTP 方法、完整请求 headers（dict）、请求 body（字符串）、响应状态码、完整响应 headers（dict）、响应 body（字符串）、`is_sse: false`

#### Scenario: JSONL append mode
- **WHEN** 同一天内有多条请求被记录
- **THEN** 所有记录追加写入同一个 `logs/YYYY-MM-DD.jsonl` 文件，每条记录占一行，文件内容为合法的 JSONL 格式

#### Scenario: Output directory configuration
- **WHEN** 用户执行 `deep-ai-analysis proxy --output ./my-logs`
- **THEN** 日志文件写入 `./my-logs/YYYY-MM-DD.jsonl`；目录不存在时自动创建

#### Scenario: Log file auto-rotation
- **WHEN** 代理运行跨越午夜（日期变更）
- **THEN** 新的请求写入新日期对应的 `YYYY-MM-DD.jsonl` 文件

### Requirement: SSE stream recording
代理 addon SHALL 检测并完整记录 SSE（Server-Sent Events）流式响应，连接关闭后将完整记录作为一行追加到 JSONL 文件。

#### Scenario: Detect SSE response
- **WHEN** 响应头包含 `content-type: text/event-stream`
- **THEN** addon 识别该响应为 SSE 流，为该 flow 启用流式记录模式（`flow.response.stream = True`）

#### Scenario: Buffer SSE events in memory
- **WHEN** SSE 连接活跃且新的 chunk 到达
- **THEN** addon 解析 chunk 中完整的 SSE 事件（以 `\n\n` 为边界），将每个完整事件追加到该 flow 的内存缓冲 `sse_events` 列表

#### Scenario: Partial SSE chunk buffering
- **WHEN** 接收到的 chunk 末尾不以 `\n\n` 结尾（事件边界不完整）
- **THEN** addon 将不完整部分存入该 flow 的 per-flow 缓冲区，等待后续 chunk 合并后再解析

#### Scenario: SSE session complete — write to JSONL
- **WHEN** SSE 连接关闭（flow 完成）
- **THEN** 将完整记录作为一行 JSON 追加到当天 JSONL 文件：`is_sse: true`，`sse_events` 包含本次连接所有完整事件的原始文本列表，`response.body` 为所有事件拼接的完整字符串

### Requirement: CA certificate guidance
代理启动时 SHALL 向用户打印 mitmproxy CA 证书的路径和安装指引，以便用户信任 HTTPS 解密。

#### Scenario: Display certificate path on startup
- **WHEN** 用户执行 `deep-ai-analysis proxy` 且代理成功启动
- **THEN** 系统打印 CA 证书文件路径（`~/.mitmproxy/mitmproxy-ca-cert.pem`）和系统安装提示

### Requirement: Graceful shutdown
代理 SHALL 在收到 SIGINT（Ctrl+C）时完成当前活跃流的记录后再退出。

#### Scenario: SIGINT shutdown
- **WHEN** 用户按下 Ctrl+C
- **THEN** 系统打印关闭提示，mitmproxy master 调用 `master.shutdown()` 停止接受新连接，等待当前活跃 SSE flow 写入完毕（最多 5 秒），然后以退出码 0 退出
