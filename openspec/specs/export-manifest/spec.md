# export-manifest Specification

## Purpose
TBD - created by archiving change portable-diagnostic-export. Update Purpose after archive.
## Requirements
### Requirement: 导出时生成 manifest.json
每次导出 SHALL 在压缩包根目录的 `deep-ai-analysis-export/` 下生成 `manifest.json`，包含版本、session 信息、导出时间及内容摘要。

#### Scenario: 正常导出时生成 manifest
- **WHEN** 用户执行导出（CLI 或 Web UI）
- **THEN** 压缩包内 `deep-ai-analysis-export/manifest.json` 存在
- **AND** 文件包含 `exportVersion`、`sessionId`、`createdAt`、`included`、`counts` 字段

#### Scenario: included 字段反映实际导出内容
- **WHEN** 某类内容（如 reqResp）不存在或被用户取消勾选
- **THEN** `manifest.json` 中对应 `included` 字段为 `false`
- **AND** `counts` 中对应数量为 `0`

### Requirement: manifest 版本字段固定为 "1.0"
当前导出 SHALL 将 `exportVersion` 写为字符串 `"1.0"`。

#### Scenario: 导出包含版本标识
- **WHEN** 生成 manifest.json
- **THEN** `exportVersion` 字段值为 `"1.0"`

