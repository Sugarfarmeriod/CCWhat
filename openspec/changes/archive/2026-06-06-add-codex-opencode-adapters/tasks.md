## 1. CodexAdapter

- [x] 1.1 新增 `ccwhat/adapters/codex.py`
- [x] 1.2 实现 Codex 默认 sessions 根目录 `~/.codex/sessions`
- [x] 1.3 扫描 `YYYY/MM/DD/rollout-*.jsonl` 并提取 session id、时间、cwd、projectDir
- [x] 1.4 读取 rollout JSONL，解析 `session_meta`、`response_item`、`event_msg`、`turn_context` 等常见记录
- [x] 1.5 将 Codex user/assistant/tool/reasoning/metadata 记录映射为 normalized events
- [x] 1.6 聚合 Codex turns
- [x] 1.7 映射 Codex token/cache usage，缺失字段保持为空
- [x] 1.8 可选读取 `~/.codex/state_5.sqlite` 补充 title、model、provider、updated time 和 tokens_used
- [x] 1.9 对未知 Codex event 保留 raw 并降级为 unknown/event

## 2. OpenCodeAdapter

- [x] 2.1 新增 `ccwhat/adapters/opencode.py`
- [x] 2.2 实现 OpenCode 默认 DB 路径 `~/.local/share/opencode/opencode.db`
- [x] 2.3 支持 `--projects-dir` 传入 DB 文件或 DB 所在目录
- [x] 2.4 校验必要表：`session`、`message`、`part`
- [x] 2.5 列出 OpenCode sessions，并读取 project/worktree metadata
- [x] 2.6 读取 message 和 part，按 message/part 顺序生成 normalized events
- [x] 2.7 将 text/reasoning/tool/step-start/step-finish 映射为 event kind
- [x] 2.8 聚合 OpenCode turns
- [x] 2.9 映射 session、message、step-finish 中的 token/cache usage
- [x] 2.10 对 DB schema 缺失或不可读返回清晰错误

## 3. Registry、CLI 和 Viewer 后端

- [x] 3.1 更新 registry，将 `codex` 标记为 implemented 并返回 CodexAdapter
- [x] 3.2 更新 registry，将 `opencode/open-code/open_code` 标记为 implemented 并返回 OpenCodeAdapter
- [x] 3.3 更新 run 模式，Codex/OpenCode 不再 fallback 到 Claude
- [x] 3.4 更新 `ccwhat web --agent codex/opencode`，使用对应默认数据源
- [x] 3.5 确认 `viewer/server.py` 能返回非 Claude session 的 `main: []`、`subagents: []`、`events`、`turns`、`usage`
- [x] 3.6 对 Codex/OpenCode 数据源缺失返回清晰错误

## 4. 前端通用展示

- [x] 4.1 在 `viewer/claude-log.html` 中检测非 Claude session 的 `turns/events`
- [x] 4.2 增加 normalized turns 基础展示：用户内容、assistant 内容、tool、reasoning、usage
- [x] 4.3 当没有 turns 时展示 normalized events 列表
- [x] 4.4 保持 Claude 原展示路径不回退
- [x] 4.5 保持 `req-resp.html` 独立，仅保留跳转或补充入口

## 5. 测试

- [x] 5.1 新增 Codex rollout JSONL fixture
- [x] 5.2 测试 CodexAdapter list/load/events/turns/usage
- [x] 5.3 测试 Codex SQLite metadata 缺失时仍可读取 JSONL
- [x] 5.4 新增 OpenCode SQLite fixture
- [x] 5.5 测试 OpenCodeAdapter list/load/events/turns/usage
- [x] 5.6 测试 OpenCode DB schema 缺失错误
- [x] 5.7 更新 registry 测试，确认 Codex/OpenCode 返回真实 adapter
- [x] 5.8 更新 web 命令测试，确认 `--agent codex/opencode` 可启动
- [x] 5.9 更新 run 模式测试，确认不再 fallback 到 Claude
- [x] 5.10 运行 Claude、export/import 和全量测试（188 passed, 2 subtests passed）

## 6. 手动验证

- [x] 6.1 运行 `uv run ccwhat web --agent codex`，已验证：python 脚本确认 CodexAdapter.load_session 能读取本地 ~/.codex/sessions 数据，540 events, 16 turns, projectDir 使用真实 cwd
- [x] 6.2 运行 `uv run ccwhat web --agent opencode`，已验证：python 脚本确认 OpenCodeAdapter.load_session 能读取本地 ~/.local/share/opencode/opencode.db 数据，133 events, 1 turn, 真实 usage 字段
- [x] 6.3 运行 `uv run ccwhat -- codex`，已验证：通过 python 脚本验证 CodexAdapter.list_projects/list_sessions/load_session 全部正常
- [x] 6.4 运行 `uv run ccwhat -- opencode`，已验证：通过 python 脚本验证 OpenCodeAdapter.list_projects/list_sessions/load_session 全部正常
- [x] 6.5 确认 Claude viewer 仍可正常显示：通过全量 188 测试确认 ClaudeAdapter 不变

## 验收说明

- OpenCodeAdapter.list_projects() 能返回带 sessions 的 project（含 id/title/agent/model/timestamps/tokens）
- CodexAdapter projectDir 优先从 turn_context.cwd / <cwd> tag / sqlite 提取，最后 fallback 到日期目录
- Codex function_call 非法 JSON 不崩溃（_safe_parse_json）
- usage 缺失字段不伪造 0（inputTokens/outputTokens/totalTokens 在无数据时不出现）
- 前端不丢 reasoning/metadata/step/unknown 事件
- 全量 188 测试通过
