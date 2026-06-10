## 1. Python 后端服务逻辑

- [x] 1.1 创建 `viewer/server.py`：封装 HTTP 服务逻辑为可复用函数 `run_server(port, projects_dir)`，支持直接 `python3 viewer/server.py --port ... --projects-dir ...` 运行
- [x] 1.2 实现 `GET /api/projects`：扫描 projects-dir，返回项目列表和各项目下的 sessionId 列表
- [x] 1.3 实现 `GET /api/session/<sessionId>`：查找主会话 JSONL 和 subagent 目录，返回结构化数据
- [x] 1.4 所有响应设置 `Access-Control-Allow-Origin: *` 和 `Content-Type: application/json`

## 2. CLI web-server 子命令

- [x] 2.1 创建 `deep_ai_analysis/commands/web_server.py`：click 命令 `web-server`，选项 `--port`（默认 7789）和 `--projects-dir`（默认 `~/.claude/projects`），调用 `viewer/server.py` 中的 `run_server()`
- [x] 2.2 在 `deep_ai_analysis/cli.py` 中 import 并注册 `web_server` 命令

## 3. 前端 HTML

- [x] 3.1 创建 `viewer/index.html`：页面结构包含 session selector（项目+会话下拉）、标签栏（主会话+subagents）、内容区、统计栏
- [x] 3.2 实现 `loadProjects()`：调用 `/api/projects`，填充选择器
- [x] 3.3 实现 `loadSession(sessionId)`：调用 `/api/session/<id>`，构建并渲染所有标签

## 4. 渲染逻辑

- [x] 4.1 实现 `buildTurns(entries, isSubagent)`：主会话过滤 `isSidechain: true`，配对 tool_use/tool_result
- [x] 4.2 实现 `renderTurns(turns, container)`：user 气泡（右侧）+ assistant 气泡（左侧，含工具卡片）
- [x] 4.3 实现工具卡片：工具名、输入摘要（截断/展开）、结果（折叠/展开，error 红色）
- [x] 4.4 实现 `calcStats(entries)` 并渲染统计栏

## 5. 验证

- [x] 5.1 执行 `deep-ai-analysis web-server`，在浏览器打开 `viewer/index.html`，加载 `9fcdf91f-3cd3-41c2-9b4a-bdccc17b7025` 会话，验证主会话渲染正常
- [x] 5.2 验证 subagent 标签页显示正确，工具调用配对正常
