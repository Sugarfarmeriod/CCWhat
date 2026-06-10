## MODIFIED Requirements

### Requirement: Output directory configuration
代理 addon SHALL 将日志文件写入 `--output` 指定的目录，默认为 `~/.deep-ai-analysis/raw-req-resp`，目录不存在时自动创建。

#### Scenario: Default output directory
- **WHEN** 用户执行 `deep-ai-analysis proxy`（不指定 `--output`）
- **THEN** 日志文件写入 `~/.deep-ai-analysis/raw-req-resp/YYYY-MM-DD.jsonl`；目录不存在时自动创建

#### Scenario: Custom output directory
- **WHEN** 用户执行 `deep-ai-analysis proxy --output ~/my-logs`
- **THEN** 日志文件写入 `~/my-logs/YYYY-MM-DD.jsonl`；目录不存在时自动创建
