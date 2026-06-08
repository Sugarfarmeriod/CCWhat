## MODIFIED Requirements

### Requirement: Main CLI entry point
`ccwhat` 命令 SHALL 通过 Python 包的 `[project.scripts]` 入口点注册，安装后可在系统 PATH 中直接调用。CLI 使用 `click` 框架实现，入口函数为 `ccwhat.cli:cli`。

#### Scenario: Show help
- **WHEN** 用户执行 `ccwhat --help`
- **THEN** 系统打印用法说明、可用子命令列表和全局选项，退出码为 0

#### Scenario: Show version
- **WHEN** 用户执行 `ccwhat --version`
- **THEN** 系统打印当前版本号（与 `pyproject.toml` 中的 `version` 字段一致），退出码为 0

#### Scenario: Launch arbitrary CLI through top-level passthrough
- **WHEN** 用户执行 `ccwhat -- mc --code`
- **THEN** 系统 SHALL 按等价于隐藏兼容命令 `ccwhat run -- mc --code` 的行为启动目标 CLI
- **AND** SHALL 保留 `--` 后的参数顺序和值
- **AND** 启动或复用 proxy 与 viewer
- **AND** 打开浏览器查看器

#### Scenario: Launch Claude through top-level passthrough
- **WHEN** 用户执行 `ccwhat -- claude`
- **THEN** 系统 SHALL 启动 Claude Code
- **AND** 不需要用户输入 `run` 子命令

#### Scenario: Unknown subcommand
- **WHEN** 用户执行 `ccwhat unknowncmd`
- **THEN** 系统打印错误信息提示未知子命令，并展示帮助，退出码为非 0

### Requirement: Subcommand routing
CLI 框架 SHALL 使用 `click.group()` 实现插件式子命令注册，每个子命令在独立模块中定义并通过 `cli.add_command()` 注册。已注册的公共子命令包括 `setup`、`discover`、`proxy`、`clear-req-resp`、`export`、`import` 和 `web`。`run` MAY remain as a hidden compatibility command.

#### Scenario: Subcommand help
- **WHEN** 用户执行 `ccwhat proxy --help`
- **THEN** 系统打印 proxy 子命令的用法说明、所有选项及默认值，退出码为 0

#### Scenario: No subcommand provided
- **WHEN** 用户执行 `ccwhat`（不带任何子命令）
- **THEN** 系统打印全局帮助信息，退出码为 0

#### Scenario: run subcommand hidden from public help
- **WHEN** 用户执行 `ccwhat --help`
- **THEN** 帮助信息中不包含 `run` 作为推荐子命令
- **AND** 通用启动方式 SHALL 显示为 `ccwhat -- <cli> [args...]`

#### Scenario: setup subcommand available
- **WHEN** 用户执行 `ccwhat --help`
- **THEN** 帮助信息中包含 `setup` 子命令及其简要描述

#### Scenario: discover subcommand available
- **WHEN** 用户执行 `ccwhat --help`
- **THEN** 帮助信息中包含 `discover` 子命令及其简要描述

#### Scenario: start-mc hidden from public help
- **WHEN** 用户执行 `ccwhat --help`
- **THEN** 帮助信息中不包含 `start-mc` 作为推荐子命令
- **AND** 如保留兼容别名，该别名 SHALL 显示废弃提示并指向 `ccwhat -- claude`

#### Scenario: clear-req-resp subcommand available
- **WHEN** 用户执行 `ccwhat --help`
- **THEN** 帮助信息中包含 `clear-req-resp` 子命令及其简要描述

#### Scenario: web subcommand available
- **WHEN** 用户执行 `ccwhat --help`
- **THEN** 帮助信息中包含 `web` 子命令及其简要描述

### Requirement: Package installable via pip
Python 包 SHALL 通过 `pyproject.toml` 定义，支持 `pip install -e .` 开发安装和 `pip install .` 正式安装。

#### Scenario: Development install
- **WHEN** 用户在项目根目录执行 `pip install -e .`
- **THEN** `ccwhat` 命令在当前 Python 环境中可用，修改源码立即生效无需重新安装

#### Scenario: Dependency declaration
- **WHEN** 用户在空 Python 环境中执行 `pip install .`
- **THEN** `click` 和运行所需依赖自动安装，`ccwhat` 命令可用
