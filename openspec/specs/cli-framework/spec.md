### Requirement: Main CLI entry point
`deep-ai-analysis` 命令 SHALL 通过 Python 包的 `[project.scripts]` 入口点注册，安装后可在系统 PATH 中直接调用。CLI 使用 `click` 框架实现，入口函数为 `deep_ai_analysis.cli:cli`。

#### Scenario: Show help
- **WHEN** 用户执行 `deep-ai-analysis --help`
- **THEN** 系统打印用法说明、可用子命令列表和全局选项，退出码为 0

#### Scenario: Show version
- **WHEN** 用户执行 `deep-ai-analysis --version`
- **THEN** 系统打印当前版本号（与 `pyproject.toml` 中的 `version` 字段一致），退出码为 0

#### Scenario: Unknown subcommand
- **WHEN** 用户执行 `deep-ai-analysis unknowncmd`
- **THEN** 系统打印错误信息提示未知子命令，并展示帮助，退出码为非 0

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

### Requirement: Package installable via pip
Python 包 SHALL 通过 `pyproject.toml` 定义，支持 `pip install -e .` 开发安装和 `pip install .` 正式安装。

#### Scenario: Development install
- **WHEN** 用户在项目根目录执行 `pip install -e .`
- **THEN** `deep-ai-analysis` 命令在当前 Python 环境中可用，修改源码立即生效无需重新安装

#### Scenario: Dependency declaration
- **WHEN** 用户在空 Python 环境中执行 `pip install .`
- **THEN** `click` 和 `mitmproxy` 等依赖自动安装，`deep-ai-analysis` 命令可用
