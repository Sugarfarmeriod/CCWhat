## 1. Adapter 架构

- [x] 1.1 新增 `ccwhat/adapters/` 模块和 `__init__.py`
- [x] 1.2 在 `ccwhat/adapters/base.py` 定义统一 adapter 接口、未实现错误类型、normalized event/turn 和 usage 数据约定
- [x] 1.3 在 `ccwhat/adapters/claude.py` 实现 `ClaudeAdapter`，迁移项目扫描、UUID session 识别、JSONL 读取、时间戳读取和 subagents 读取逻辑
- [x] 1.4 为 ClaudeAdapter 增加 normalized events 输出，并保留 `main/subagents` 旧字段兼容
- [x] 1.5 为 ClaudeAdapter 增加 usage 映射，将 Claude 原始 usage 映射为 CCWhat 通用 usage 字段
- [x] 1.6 在 `ccwhat/adapters/registry.py` 实现 agent 名称规范化、target 命令推断、adapter 创建和未实现 agent 的清晰错误

## 2. Viewer 后端改造

- [x] 2.1 修改 `viewer/server.py`，让 projects/session 数据读取通过 adapter 完成
- [x] 2.2 保留 `get_projects(projects_dir)` 和 `get_session(session_id, projects_dir)` 旧函数包装，内部委托 ClaudeAdapter
- [x] 2.3 修改 `/api/projects` 返回，增加 `agent` 信息并保持 `projectDir`、`sessions` 兼容
- [x] 2.4 修改 `/api/session/<sessionId>` 返回，增加 `agent` 和 `events` 信息并保持 `sessionId`、`projectDir`、`main`、`subagents` 兼容
- [x] 2.5 确认 `/api/analyze`、`/api/message-http`、`/api/message-source`、`/api/export` 在 Claude adapter 下仍按原行为工作
- [x] 2.6 为 adapter 未实现或未知 agent 的 API 响应提供明确错误
- [x] 2.7 保持 `req-resp.html` 独立，不把网络抓包页面融合进 Agent Log 页面

## 3. CLI 参数和启动模式

- [x] 3.1 修改 `ccwhat web`，新增 `--agent` 参数
- [x] 3.2 修改 `ccwhat web --projects-dir` 默认解析方式，使显式路径优先于 agent 默认路径
- [x] 3.3 修改 `viewer.server.create_server()` 和 `run_server()`，支持传入 agent 或 adapter，并保持旧调用兼容
- [x] 3.4 修改 `ccwhat -- <target>` 启动流程，根据 target 推断 agent 类型
- [x] 3.5 修改 managed viewer 启动逻辑，将推断出的 agent 传给 viewer 后端
- [x] 3.6 对 Codex/OpenCode 未实现 adapter 的 run 模式输出 warning 或 fallback 提示，确保目标命令不因 viewer 未实现而崩溃

## 4. 前端最小改动

- [x] 4.1 在 `viewer/claude-log.html` 中显示当前 agent 类型
- [x] 4.2 在 `viewer/claude-log.html` 中处理 adapter 未支持或未实现的 API 错误展示
- [x] 4.3 在 Claude 数据下继续展示本地日志可得的 token/cache 计数，不默认展示 cache 命中率
- [x] 4.4 确认 session 列表、搜索、导出、分析按钮在 Claude 数据下不回退

## 5. 测试

- [x] 5.1 新增 ClaudeAdapter 测试，覆盖列出项目和 UUID session
- [x] 5.2 新增 ClaudeAdapter 测试，覆盖读取 main entries、subagents 和 JSONL 解析失败降级
- [x] 5.3 新增 ClaudeAdapter 测试，覆盖 normalized events 和 usage 字段映射
- [x] 5.4 新增 usage 测试，确认缺失字段为空且不会默认计算 cache 命中率
- [x] 5.5 新增 registry 测试，覆盖 `claude`、`claude-code`、`codex`、`opencode`、`open-code`、`open_code` 和未知 agent
- [x] 5.6 更新 web 命令测试，覆盖 `ccwhat web --agent claude` 可启动
- [x] 5.7 更新 web 命令测试，覆盖显式 `--projects-dir` 优先于 agent 默认路径
- [x] 5.8 更新 run 模式测试，覆盖 target agent 推断和 Codex/OpenCode 未实现 adapter 的 warning 或 fallback
- [x] 5.9 运行现有 export/import 测试，确认包结构和导入查看流程不被破坏
- [x] 5.10 运行全量测试并修复回归

## 6. 手动验证

- [x] 6.1 手动运行 `ccwhat web --agent claude`，确认 viewer 使用 Claude 默认目录
- [x] 6.2 手动运行 `ccwhat web --projects-dir ~/.claude/projects`，确认显式目录仍可用
- [x] 6.3 手动运行 `ccwhat -- claude`，确认 viewer 和目标命令正常启动
- [x] 6.4 手动运行 `ccwhat -- codex`，确认未实现 adapter 的提示清晰且目标命令不因 viewer 崩溃
- [x] 6.5 手动运行 `ccwhat -- opencode`，确认未实现 adapter 的提示清晰且目标命令不因 viewer 崩溃
