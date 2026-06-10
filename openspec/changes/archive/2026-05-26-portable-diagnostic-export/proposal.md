## Why

当前的 export 功能只是把日志文件打包成 tar.gz，接收方需要知道如何解压、数据放在哪里、用什么命令查看，门槛高且容易出错。我们需要把"可分享的诊断包"作为一等公民来设计：导出即可分享，分享即可一键查看。

## What Changes

- 压缩包内部改为固定结构，新增 `manifest.json` 描述包内容
- 新增 `import` 命令：解压 → 导入到本机数据目录 → 自动打开 Web 查看页面
- 压缩包内新增 `README.md`（接收方查看说明）和 `view.command`（macOS 双击脚本）
- 默认导出路径改为 `~/Downloads/deep-ai-analysis-exports/`
- Web UI 导出弹窗重新设计：支持勾选导出内容、显示导入命令、提供"在 Finder 中显示"按钮
- 文件名格式改为 `export-YYYYMMDD-HHmmss-<session短ID>.tar.gz`

## Capabilities

### New Capabilities

- `export-manifest`: 生成并写入 `manifest.json`，描述包版本、session ID、导出时间、包含内容
- `export-package-structure`: 固定压缩包内目录结构（`claude-logs/`、`req-resp/`、`metadata/`、`README.md`、`view.command`）
- `import-command`: `deep-ai-analysis import <file> [--open]` 命令，解压诊断包并导入本机，可选自动打开浏览器

### Modified Capabilities

- `export-command`: 导出路径默认改为 `~/Downloads/deep-ai-analysis-exports/`，文件名加 session 短 ID
- `export-web-ui`: 导出弹窗新增内容勾选、成功后显示导入命令和"在 Finder 中显示"按钮

## Impact

- `deep_ai_analysis/exporter.py`：重构打包逻辑，改用新目录结构，生成 manifest/README/view.command
- `deep_ai_analysis/commands/export.py`：更新默认路径和文件名格式
- `deep_ai_analysis/commands/import_.py`：新文件，实现 import 命令
- `deep_ai_analysis/main.py`：注册 import 命令
- `viewer/server.py`：`/api/export` 端点使用新打包逻辑
- `viewer/claude-log.html`：重新设计导出弹窗 UI
