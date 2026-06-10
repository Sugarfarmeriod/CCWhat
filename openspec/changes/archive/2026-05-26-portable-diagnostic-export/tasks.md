## 1. 重构 exporter.py：新包结构

- [x] 1.1 将压缩包根目录改为 `deep-ai-analysis-export/`，调整所有文件路径前缀
- [x] 1.2 实现 `_build_manifest()` 函数，生成 manifest.json（含 exportVersion、sessionId、projectDir、createdAt、included、counts）
- [x] 1.3 实现 `_build_readme()` 函数，生成 README.md，包含导入命令示例
- [x] 1.4 实现 `_build_view_command()` 函数，生成 view.command（chmod 755），内容为 `deep-ai-analysis import . --open`
- [x] 1.5 实现 `_build_metadata()` 函数，生成 metadata/session.json 和 metadata/project.json
- [x] 1.6 更新 `export_session()` 将上述文件写入 tar，调整 claude-logs/ 和 req-resp/ 目录名
- [x] 1.7 `build_tar_gz_bytes()` 支持 `content_options` 参数（dict，控制是否包含 subagent/reqResp），默认全 True
- [x] 1.8 验收：解压导出包，确认根目录为 `deep-ai-analysis-export/`，manifest.json 字段齐全，README.md 存在，view.command 权限为 755

## 2. 更新 commands/export.py

- [x] 2.1 默认导出路径改为 `~/Downloads/deep-ai-analysis-exports/`，不存在时自动创建
- [x] 2.2 `default_filename()` 改为接收 session_id 参数，生成 `export-YYYYMMDD-HHmmss-<前8位>.tar.gz`
- [x] 2.3 导出成功后打印导入命令：`deep-ai-analysis import <文件路径> --open`
- [x] 2.4 验收：执行 `deep-ai-analysis export <session-id>`，确认文件出现在 `~/Downloads/deep-ai-analysis-exports/`，文件名含短 ID，终端输出导入命令

## 3. 新增 commands/import_.py

- [x] 3.1 创建 `import_` click command，接收 `path` 参数（tar.gz 或已解压目录）和 `--open` flag
- [x] 3.2 实现解压 tar.gz 到临时目录，识别 `deep-ai-analysis-export/` 根目录
- [x] 3.3 读取并校验 manifest.json，缺失或格式错误时报错退出
- [x] 3.4 将数据复制到 `~/Downloads/deep-ai-analysis-imports/<projectDir>/`（可见目录，Finder 中可直接找到）
- [x] 3.5 目标目录已存在时输出提示并要求用户确认（`--force` 跳过确认）
- [x] 3.6 实现 `--open`：导入完成后调用 `webbrowser.open()` 打开 web-server 对应 session 页面，若 web-server 未运行则先启动
- [x] 3.7 验收：执行 `deep-ai-analysis import <导出包> --open`，确认数据写入 `~/.deep-ai-analysis/imports/<session-id>/`，浏览器自动打开
- [x] 3.8 验收（异常路径）：对非诊断包执行 import，确认报错信息清晰；对已存在的 session 再次 import，确认出现覆盖确认提示

## 4. 注册 import 命令

- [x] 4.1 在 `deep_ai_analysis/main.py` 中 import 并注册 `import_` 命令

## 5. 更新 viewer/server.py

- [x] 5.1 `/api/export` 端点从请求参数中读取 `include` 字段（逗号分隔，如 `claudeLogs,subagentLogs,reqResp`），构造 `content_options` 传给 `build_tar_gz_bytes()`

## 6. 重设计 viewer/claude-log.html 导出弹窗

- [x] 6.1 导出弹窗新增内容勾选区（三个 checkbox：主日志必选、Subagent 日志、原始请求响应），默认全选
- [x] 6.2 `doExport()` 将勾选状态拼入 `include` 参数传给 `/api/export`
- [x] 6.3 导出成功后展示：文件路径 + 完整导入命令文本
- [x] 6.4 添加"复制导入命令"按钮，点击写入剪贴板，短暂显示"已复制"
- [x] 6.5 移除 `showDirectoryPicker`，改用 `<a download>` 标准浏览器下载，按钮文字改为"导出并下载"
- [x] 6.6 弹窗内 session 选择器：打开时从 `/api/projects` 加载所有 sessions，默认选当前 session
- [x] 6.7 导出成功后锁定表单：session 选择器、文件名输入框、内容勾选框全部 disabled；再次打开时重置
- [ ] 6.8 验收：Web UI 选择不同 session 导出，确认文件名自动更新；取消勾选内容后导出，解压确认 manifest.included 正确；复制命令按钮正常工作

## 7. 集成验收

- [ ] 7.1 端到端（CLI）：export 一个 session → 把包复制到另一路径 → import --open → 确认浏览器打开且数据正确
- [ ] 7.2 端到端（Web UI）：Web 导出弹窗导出 → CLI import 导入 → 浏览器打开正确 session
- [ ] 7.3 异常路径：import 一个普通 tar.gz（非诊断包），确认错误提示明确
- [ ] 7.4 异常路径：Web UI 取消所有勾选时导出按钮应禁用或提示"至少选择一项"
