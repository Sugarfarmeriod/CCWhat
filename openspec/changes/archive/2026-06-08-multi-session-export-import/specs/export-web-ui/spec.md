## MODIFIED Requirements

### Requirement: 导出弹窗支持多 Session 选择
Web UI 导出弹窗 SHALL 提供 session 多选控件，打开时从 `/api/projects` 加载所有可用 session，默认只选中当前正在查看的 session。

#### Scenario: 打开弹窗时预填当前 session
- **WHEN** 用户点击导出按钮
- **THEN** 弹窗内 session 多选控件自动选中主页面当前查看的 session
- **AND** 其他 session 默认不选中

#### Scenario: 可在弹窗内选择多个 session
- **WHEN** 用户在弹窗内选择多个 session
- **THEN** 文件名输入框自动更新为多 session 默认文件名
- **AND** 点击"导出并下载"时请求 `/api/export` 的 `sessions` 参数包含所有选中 session ID

#### Scenario: 只选择一个 session 时使用短 ID 文件名
- **WHEN** 用户只选择一个 session
- **THEN** 文件名输入框自动更新为该 session 对应的短 ID 默认文件名

### Requirement: 导出弹窗支持内容勾选
Web UI 导出弹窗 SHALL 展示可导出的内容类别，用户可勾选/取消，Claude Code 主日志为必选项。

#### Scenario: 默认全选所有导出内容
- **WHEN** 用户打开导出弹窗
- **THEN** 所有内容类别默认勾选；主日志显示"（必选）"且不可取消

#### Scenario: 取消勾选某类内容后导出
- **WHEN** 用户取消勾选"原始请求响应"后点击"导出并下载"
- **THEN** 生成的压缩包不包含所选 session 的 `req-resp/` 目录
- **AND** manifest.json 中每个所选 session 的 `included.reqResp` 为 `false`

### Requirement: 导出通过浏览器标准下载触发，不使用文件夹选择器
Web UI 导出 SHALL 通过 `<a download>` 触发浏览器标准下载，不使用 File System Access API（`showDirectoryPicker`）。

#### Scenario: 点击"导出并下载"触发浏览器下载
- **WHEN** 用户点击"导出并下载"按钮
- **THEN** 后端生成 tar.gz，浏览器弹出下载保存到默认下载文件夹
- **AND** 不弹出文件夹选择对话框

### Requirement: 导出成功后表单锁定并展示结果
导出成功后，弹窗 SHALL 将所有输入项变为不可编辑状态，并展示成功提示和导入命令。

#### Scenario: 导出成功后表单锁定
- **WHEN** 导出成功完成
- **THEN** session 多选控件、文件名输入框、内容勾选框全部变为 disabled
- **AND** 状态行显示"✓ 导出成功，文件已下载至浏览器默认下载文件夹"
- **AND** 展示完整导入命令文本（含 `~/Downloads/<文件名>`）和"复制导入命令"按钮

#### Scenario: 复制导入命令
- **WHEN** 用户点击"复制导入命令"
- **THEN** `deep-ai-analysis import ~/Downloads/<文件名> --open` 被写入剪贴板
- **AND** 按钮文字短暂变为"已复制"

#### Scenario: 再次打开弹窗时重置为可编辑
- **WHEN** 用户关闭弹窗后再次打开
- **THEN** 所有输入项恢复为可编辑状态，内容勾选框重置为全选
- **AND** session 多选控件重新默认只选中当前正在查看的 session
