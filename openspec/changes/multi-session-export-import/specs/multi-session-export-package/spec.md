## ADDED Requirements

### Requirement: 导出包支持包含多个 session
`deep-ai-analysis export` 和 `/api/export` SHALL 生成可同时承载一个或多个 Claude session 的诊断包，包内各 session 的日志与元数据不得相互覆盖。

#### Scenario: CLI 导出多个 session 时生成单个多 session 包
- **WHEN** 用户执行 `deep-ai-analysis export <session-a> <session-b>`
- **THEN** 命令生成一个 tar.gz 文件
- **AND** 包内同时包含 `<session-a>` 和 `<session-b>` 的数据
- **AND** 两个 session 的主日志、subagent 日志和 req/resp 文件位于各自独立目录

#### Scenario: import 多 session 包时批量导入所有 session
- **WHEN** 用户执行 `deep-ai-analysis import <multi-session-package>`
- **THEN** 包内所有 session 都被导入到本地 imports 目录
- **AND** 终端输出导入成功的 session 数量和目标根目录
