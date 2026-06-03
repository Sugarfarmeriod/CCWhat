## Why

当前 export CLI 和 `/api/export` 接口接受多个 session ID，但导出包结构、manifest 和 import 流程只对单 session 自洽，导致多 session 导出后的产物无法稳定导入和查看。现在需要把“名义支持”补齐为真正可交付的多 session 诊断包格式，同时保留对旧单 session 包的导入兼容。

## What Changes

- 将导出包升级为可容纳多个 session 的统一结构，避免多 session 导出时文件路径和 manifest 相互覆盖。
- 将 manifest 从单 session 元数据升级为包级清单，描述包内包含的多个 session 及其各自的 projectDir、内容选项和文件计数。
- 更新 CLI export、viewer `/api/export` 和 Web UI，使其生成与多 session 包格式一致的默认文件名、导入命令和交互文案。
- 更新 import 命令，使其可导入多 session 包，并继续兼容旧单 session 包。
- 增加多 session export/import 的自动化测试，覆盖 tar.gz 与目录导入、旧格式兼容和结构校验。

## Capabilities

### New Capabilities
- `multi-session-export-package`: 定义一个可同时承载多个 Claude session 的可移植诊断包格式及其导入行为。

### Modified Capabilities
- `export-command`: `export` 命令的默认文件名、成功提示和多 session 参数行为发生变化。
- `export-manifest`: manifest 从单 session 文档升级为包级多 session 清单。
- `export-package-structure`: 导出包目录结构从单 session 布局升级为多 session 布局。
- `import-command`: `import` 命令从导入单 session 包升级为可批量导入包内多个 session，并兼容旧格式。
- `export-web-ui`: 导出弹窗与下载后的导入提示需要与多 session 导出行为保持一致。

## Impact

- 影响代码：`deep_ai_analysis/exporter.py`、`deep_ai_analysis/commands/export.py`、`deep_ai_analysis/commands/import_.py`、`viewer/server.py`、`viewer/claude-log.html`
- 影响测试：新增 export/import 回归测试
- 影响包格式：新增 manifest v2 和多 session 目录布局
- 兼容性：需要继续支持旧单 session 包导入，避免已发出的诊断包失效
