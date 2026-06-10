## MODIFIED Requirements

### Requirement: 导出时生成 manifest.json
每次导出 SHALL 在压缩包根目录的 `deep-ai-analysis-export/` 下生成 `manifest.json`，用于描述整个导出包中包含的 session 列表、导出时间及每个 session 的内容摘要。

#### Scenario: 正常导出时生成包级 manifest
- **WHEN** 用户执行导出（CLI 或 Web UI）
- **THEN** 压缩包内 `deep-ai-analysis-export/manifest.json` 存在
- **AND** 文件包含 `exportVersion`、`createdAt`、`sessionCount`、`sessions` 字段

#### Scenario: sessions 数组反映实际导出内容
- **WHEN** 导出包包含多个 session，且其中某个 session 未包含 req/resp 文件
- **THEN** `manifest.json` 的 `sessions` 数组包含每个 session 的 `sessionId` 和 `projectDir`
- **AND** 对应 session 的 `included.reqResp` 为 `false`
- **AND** 对应 session 的 `counts.reqRespFiles` 为 `0`

### Requirement: manifest 版本字段在多 session 包中为 "2.0"
当前导出 SHALL 在新的多 session 包格式中将 `exportVersion` 写为字符串 `"2.0"`。

#### Scenario: 导出包含多 session 包版本标识
- **WHEN** 生成新的导出包 manifest.json
- **THEN** `exportVersion` 字段值为 `"2.0"`
- **AND** `sessions` 字段为数组
