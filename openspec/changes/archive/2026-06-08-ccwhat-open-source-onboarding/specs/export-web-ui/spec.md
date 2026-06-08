## MODIFIED Requirements

### Requirement: 导出成功后表单锁定并展示结果
导出成功后，弹窗 SHALL 将所有输入项变为不可编辑状态，并展示成功提示和导入命令。

#### Scenario: 导出成功后表单锁定
- **WHEN** 导出成功完成
- **THEN** session 选择器、文件名输入框、内容勾选框全部变为 disabled
- **AND** 状态行显示"✓ 导出成功，文件已下载至浏览器默认下载文件夹"
- **AND** 展示完整导入命令文本（含 `~/Downloads/<文件名>`）和"复制导入命令"按钮

#### Scenario: 复制导入命令
- **WHEN** 用户点击"复制导入命令"
- **THEN** `ccwhat import ~/Downloads/<文件名> --open` 被写入剪贴板
- **AND** 按钮文字短暂变为"已复制"

#### Scenario: 再次打开弹窗时重置为可编辑
- **WHEN** 用户关闭弹窗后再次打开
- **THEN** 所有输入项恢复为可编辑状态，内容勾选框重置为全选

## ADDED Requirements

### Requirement: Web export copy uses ccwhat package names
The Web export UI SHALL use `ccwhat` names in visible commands, downloaded package guidance, and generated filenames where applicable.

#### Scenario: Export modal command copy uses ccwhat
- **WHEN** the export modal displays command-line instructions
- **THEN** all commands use `ccwhat`
- **AND** no visible command uses `deep-ai-analysis`

#### Scenario: Export package root copy uses ccwhat-export
- **WHEN** the export modal describes the downloaded package structure
- **THEN** it refers to `ccwhat-export/`
