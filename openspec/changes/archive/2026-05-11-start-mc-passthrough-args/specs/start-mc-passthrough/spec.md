## ADDED Requirements

### Requirement: start-mc 透传额外参数给 mc
`start-mc` 子命令 SHALL 接受任意额外参数，并将其原样拼接到 `mc --code` 命令之后执行。

#### Scenario: 无额外参数时行为不变
- **WHEN** 用户执行 `deep-ai-analysis start-mc`
- **THEN** 系统运行 `mc --code`，行为与修改前完全相同

#### Scenario: 透传单个额外参数
- **WHEN** 用户执行 `deep-ai-analysis start-mc --opt1`
- **THEN** 系统运行 `mc --code --opt1`

#### Scenario: 透传多个额外参数
- **WHEN** 用户执行 `deep-ai-analysis start-mc --resume /some/path --flag`
- **THEN** 系统运行 `mc --code --resume /some/path --flag`，参数顺序与输入一致

#### Scenario: --port 选项与透传参数共存
- **WHEN** 用户执行 `deep-ai-analysis start-mc --port 8888 --opt1`
- **THEN** 系统以端口 8888 配置代理，并运行 `mc --code --opt1`
