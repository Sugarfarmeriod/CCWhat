## MODIFIED Requirements

### Requirement: CLI web-server req-resp-dir option
`deep-ai-analysis web-server` 子命令 SHALL 支持 `--req-resp-dir` 选项（替代旧的 `--logs-dir`），指定原始 HTTP 请求/响应日志目录，默认为 `~/.deep-ai-analysis/raw-req-resp`（与 `proxy` 命令的默认输出目录一致）。

#### Scenario: Default req-resp dir
- **WHEN** 用户执行 `deep-ai-analysis web-server`（不指定 `--req-resp-dir`）
- **THEN** 服务使用 `~/.deep-ai-analysis/raw-req-resp` 查找原始请求/响应日志文件

#### Scenario: Custom req-resp dir
- **WHEN** 用户执行 `deep-ai-analysis web-server --req-resp-dir ~/my-req-resp`
- **THEN** 服务启动后使用指定目录查找原始请求/响应日志文件
