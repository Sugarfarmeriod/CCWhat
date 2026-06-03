## 1. 后端：新增接口和 logs-dir 参数

- [x] 1.1 在 `viewer/server.py` 中为 `run_server()` 和 `_make_handler()` 增加 `logs_dir: Path` 参数
- [x] 1.2 实现 `get_message_http(session_id, message_id, projects_dir, logs_dir)` 函数：在会话 JSONL 中找到 uuid 匹配的 user 条目，获取其 timestamp，扫描 `logs_dir/**/*_parsed.jsonl`，按 `claude_session_id` + 时间窗口 [-5s, +60s] 匹配，返回记录列表
- [x] 1.3 在 HTTP handler 中注册 `GET /api/message-http/<sessionId>/<messageId>` 路由，调用上述函数
- [x] 1.4 在 `server.py` 的 `__main__` 入口和 `run_server()` 中添加 `--logs-dir` 参数（默认 `./logs`）

## 2. CLI：更新 web-server 命令

- [x] 2.1 在 `deep_ai_analysis/commands/web_server.py` 中新增 `--logs-dir` 选项（默认 `./logs`），传递给 `run_server()`

## 3. 前端：用户气泡按钮和弹窗

- [x] 3.1 在 `viewer/index.html` 的 `renderTurn()` 中，为主会话（非 subagent）的 user 气泡添加「查看请求」按钮（气泡右上角，小字样式）
- [x] 3.2 为按钮绑定 click 事件：读取 turn 上存储的 `sessionId` 和 `messageId`（uuid），调用 `/api/message-http/<sessionId>/<messageId>`
- [x] 3.3 实现 `showHttpModal(records)` 函数：创建/显示模态弹窗，展示每条记录的 timestamp、model、最后用户消息摘要（50字）、response content.text（200字截断）、usage token 统计
- [x] 3.4 在 `buildTurns()` 中为 user turn 保存 `uuid` 和 `sessionId`，传递给渲染函数
- [x] 3.5 实现弹窗关闭逻辑（点击背景或关闭按钮）

## 4. 验证

- [x] 4.1 启动 `deep-ai-analysis web-server --logs-dir <parsed-logs-dir>`，加载会话，点击用户消息的「查看请求」，验证返回数据并正确展示弹窗
