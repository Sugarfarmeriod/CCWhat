## ADDED Requirements

### Requirement: 压缩包使用固定目录结构
导出的 tar.gz 内部 SHALL 使用固定的目录结构，根目录名为 `deep-ai-analysis-export/`。

#### Scenario: 压缩包解压后目录结构符合规范
- **WHEN** 用户解压导出的 tar.gz
- **THEN** 根目录为 `deep-ai-analysis-export/`
- **AND** 包含 `manifest.json`、`README.md`、`claude-logs/`
- **AND** `claude-logs/main-session.jsonl` 存在（主日志）
- **AND** 如有 subagent 日志，则位于 `claude-logs/subagents/*.jsonl`
- **AND** 如有原始请求响应，则位于 `req-resp/*.jsonl`

#### Scenario: metadata 目录包含 session 和 project 信息
- **WHEN** 用户解压导出的 tar.gz
- **THEN** `metadata/session.json` 存在，包含 sessionId 和时间戳
- **AND** `metadata/project.json` 存在，包含 projectDir

### Requirement: 压缩包内包含 README.md
导出的 tar.gz SHALL 包含 `deep-ai-analysis-export/README.md`，说明如何查看该诊断包。

#### Scenario: README 包含导入命令说明
- **WHEN** 用户解压并打开 README.md
- **THEN** 文件包含 `deep-ai-analysis import` 命令的使用示例

### Requirement: macOS 下生成 view.command 双击脚本
导出时 SHALL 在压缩包内生成 `deep-ai-analysis-export/view.command`，内容为调用 `deep-ai-analysis import . --open` 的 shell 脚本。

#### Scenario: view.command 可执行
- **WHEN** 用户解压压缩包并双击 view.command（macOS）
- **THEN** 脚本执行 `deep-ai-analysis import . --open`
- **AND** 脚本首行为 `#!/bin/bash`，文件权限包含可执行位（755）
