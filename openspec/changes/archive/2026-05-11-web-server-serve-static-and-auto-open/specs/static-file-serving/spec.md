## ADDED Requirements

### Requirement: web-server 提供 viewer HTML 文件的 HTTP 服务
`web-server` 命令启动的 HTTP 服务器 SHALL 响应对 viewer HTML 文件的 GET 请求，返回对应文件内容。

#### Scenario: 访问根路径返回 index.html
- **WHEN** 客户端 GET `/` 或 GET `/index.html`
- **THEN** 服务器返回 200，Content-Type 为 `text/html; charset=utf-8`，内容为 `viewer/index.html`

#### Scenario: 访问 claude-log.html
- **WHEN** 客户端 GET `/claude-log.html`
- **THEN** 服务器返回 200，Content-Type 为 `text/html; charset=utf-8`，内容为 `viewer/claude-log.html`

#### Scenario: 访问 req-resp.html
- **WHEN** 客户端 GET `/req-resp.html`
- **THEN** 服务器返回 200，Content-Type 为 `text/html; charset=utf-8`，内容为 `viewer/req-resp.html`

#### Scenario: 访问不存在的路径仍返回 404
- **WHEN** 客户端 GET `/unknown-path`
- **THEN** 服务器返回 404 JSON 错误响应

### Requirement: HTML 页面使用同域 API 地址
viewer HTML 页面中的 `apiBase()` 函数 SHALL 默认使用 `window.location.origin` 作为 API 基础地址，以支持通过 HTTP 服务访问时的同域请求。

#### Scenario: 通过 HTTP 服务访问页面时 API 地址正确
- **WHEN** 页面通过 `http://127.0.0.1:7789/claude-log.html` 访问
- **THEN** `apiBase()` 返回 `http://127.0.0.1:7789`，API 请求无需手动配置地址
