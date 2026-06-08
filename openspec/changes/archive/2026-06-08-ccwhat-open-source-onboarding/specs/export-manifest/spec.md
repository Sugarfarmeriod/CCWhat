## MODIFIED Requirements

### Requirement: 导出时生成 manifest.json
每次导出 SHALL 在压缩包根目录的 `ccwhat-export/` 下生成 `manifest.json`，包含版本、tool 标识、session 信息、导出时间及内容摘要。

#### Scenario: 正常导出时生成 manifest
- **WHEN** 用户执行导出（CLI 或 Web UI）
- **THEN** 压缩包内 `ccwhat-export/manifest.json` 存在
- **AND** 文件包含 `exportVersion`、`toolName`、`toolVersion`、`createdAt`、`sessionCount`、`sessions` 字段

#### Scenario: included 字段反映实际导出内容
- **WHEN** 某类内容（如 reqResp）不存在或被用户取消勾选
- **THEN** `manifest.json` 中对应 `included` 字段为 `false`
- **AND** `counts` 中对应数量为 `0`

#### Scenario: tool name identifies ccwhat
- **WHEN** 生成 manifest.json
- **THEN** `toolName` 字段值为 `ccwhat`

### Requirement: manifest 版本字段固定为 "1.0"
当前导出 SHALL 将 `exportVersion` 写为当前 ccwhat 诊断包格式版本字符串，并在本次改造后使用 `"2.0"`。

#### Scenario: 导出包含版本标识
- **WHEN** 生成 manifest.json
- **THEN** `exportVersion` 字段值为 `"2.0"`

## ADDED Requirements

### Requirement: Legacy manifest compatibility is recognized
The import command SHALL recognize legacy manifests that do not include `toolName` or that live under `deep-ai-analysis-export/`.

#### Scenario: Legacy manifest imports successfully
- **WHEN** 用户导入旧诊断包且 manifest 缺少 `toolName`
- **THEN** `ccwhat import` 仍可解析 manifest
- **AND** 终端提示该包来自 legacy 格式
