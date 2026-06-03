## MODIFIED Requirements

### Requirement: Subcommand routing
CLI 框架 SHALL 使用 `click.group()` 实现插件式子命令注册，每个子命令在独立模块中定义并通过 `cli.add_command()` 注册。已注册的子命令包括 `proxy`、`start-mc`、`clear-req-resp` 和 `web-server`。

#### Scenario: Subcommand help
- **WHEN** 用户执行 `deep-ai-analysis proxy --help`
- **THEN** 系统打印 proxy 子命令的用法说明、所有选项及默认值，退出码为 0

#### Scenario: No subcommand provided
- **WHEN** 用户执行 `deep-ai-analysis`（不带任何子命令）
- **THEN** 系统打印全局帮助信息，退出码为 0

#### Scenario: start-mc subcommand available
- **WHEN** 用户执行 `deep-ai-analysis --help`
- **THEN** 帮助信息中包含 `start-mc` 子命令及其简要描述

#### Scenario: clear-req-resp subcommand available
- **WHEN** 用户执行 `deep-ai-analysis --help`
- **THEN** 帮助信息中包含 `clear-req-resp` 子命令及其简要描述

#### Scenario: web-server subcommand available
- **WHEN** 用户执行 `deep-ai-analysis --help`
- **THEN** 帮助信息中包含 `web-server` 子命令及其简要描述
