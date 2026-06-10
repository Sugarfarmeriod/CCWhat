# export-command Specification

## Purpose
TBD - created by archiving change portable-diagnostic-export. Update Purpose after archive.
## Requirements
### Requirement: 默认导出路径为 ~/Downloads/deep-ai-analysis-exports/
CLI export 命令 SHALL 在未指定 `--output` 时，将文件保存到 `~/Downloads/deep-ai-analysis-exports/` 目录下，不再使用当前工作目录。

#### Scenario: 未指定 --output 时使用默认路径
- **WHEN** 用户执行 `deep-ai-analysis export <session-id>`（不带 -o）
- **THEN** 文件保存到 `~/Downloads/deep-ai-analysis-exports/export-YYYYMMDD-HHmmss-<短ID>.tar.gz`
- **AND** 若目录不存在则自动创建

#### Scenario: 指定 --output 时优先使用指定路径
- **WHEN** 用户执行 `deep-ai-analysis export <session-id> -o ./my-export.tar.gz`
- **THEN** 文件保存到指定路径，不使用默认路径

### Requirement: 导出文件名包含 session 短 ID
默认文件名格式 SHALL 为 `export-YYYYMMDD-HHmmss-<session-id前8位>.tar.gz`。

#### Scenario: 默认文件名包含时间戳和短 ID
- **WHEN** 导出 session `c821b9c9-48e7-4383-94e0-09a29fb75d38`
- **THEN** 默认文件名为类似 `export-20260526-120017-c821b9c9.tar.gz` 的格式

### Requirement: 导出完成后显示导入命令
CLI export 成功后 SHALL 输出接收方可直接使用的导入命令。

#### Scenario: 导出成功后输出导入提示
- **WHEN** 导出成功完成
- **THEN** 终端输出文件路径
- **AND** 输出 `deep-ai-analysis import <文件路径> --open` 的完整命令供复制

