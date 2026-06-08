## 1. 调用链分离

- [x] 1.1 阅读 `ccwhat/commands/run.py` 中 `target_args`、`agent_name`、`_start_managed_web` 的调用链
- [x] 1.2 修改 `_start_managed_web` 参数语义，使 `analyzer_cmd` 默认为 `None`，且不接收 observed agent 的 `target_args`
- [x] 1.3 修改 `ccwhat -- <target>` 启动路径，确保 `target_args` 只用于启动 observed agent
- [x] 1.4 增加回归测试，验证 `ccwhat -- opencode` 不会把 `("opencode",)` 传给 Viewer Server 的 analyzer command

## 2. Analyzer Adapter 协议

- [x] 2.1 新增 analyzer 协议模型，包含 name、default command、output mode、experimental、timeout 和 output parser
- [x] 2.2 新增 analyzer registry，支持 `claude`、`claude-code`、`codex`、`opencode`、`open-code`、`open_code`
- [x] 2.3 保持 Claude analyzer 默认命令 `claude -p -` 和 stdout 输出解析
- [x] 2.4 增加 OpenCode analyzer 默认命令 `opencode run --format json`
- [x] 2.5 增加 Codex experimental analyzer 默认候选 `codex exec --json --ephemeral --ignore-user-config -`
- [x] 2.6 增加 Codex last-message 备用协议 `codex exec --output-last-message <tmpfile> --ephemeral --ignore-user-config -`

## 3. 输出解析和错误处理

- [x] 3.1 实现 stdout 输出模式解析，空输出返回 `empty_report`
- [x] 3.2 实现 OpenCode JSONL text 提取，兼容 `type == "text"` 和 `part.type == "text"`
- [x] 3.3 实现 Codex JSONL 最终文本提取，适配 Codex exec JSON event 输出
- [x] 3.4 实现 last-message-file 输出模式，确保临时文件被清理
- [x] 3.5 实现 JSONL 解析失败错误 `analyzer_output_parse_error`
- [x] 3.6 保持命令不存在、非 0 exit、timeout 的错误 code 清晰

## 4. 配置和 API 接入

- [x] 4.1 在 analyzer 选择逻辑中支持 `CCWHAT_ANALYZE_CMD`
- [x] 4.2 在 analyzer 选择逻辑中支持 `CCWHAT_ANALYZE_AGENT`
- [x] 4.3 在 analyzer 运行逻辑中支持 `CCWHAT_ANALYZE_TIMEOUT`
- [x] 4.4 在 `viewer/server.py` 中传递独立的 `analyzer_agent`、`analyzer_cmd` 和 `analyzer_timeout`
- [x] 4.5 修改 HTML report pipeline，使 `analyzer_agent` 表示报告生成 agent，而不是 session 来源 agent
- [x] 4.6 `/api/analyze` 成功和失败响应中包含 analyzer metadata

## 5. 测试

- [x] 5.1 测试 Claude analyzer stdout 协议保持兼容（现有 test_current_session_analysis tests 验证）
- [x] 5.2 测试 OpenCode analyzer JSONL 文本提取和 usage metadata 保留
- [x] 5.3 测试 Codex analyzer JSONL 文本提取
- [x] 5.4 测试 Codex last-message-file 备用协议
- [x] 5.5 测试 `target_args` 不会进入 analyzer command
- [x] 5.6 测试 analyzer command 显式配置优先于 analyzer agent
- [x] 5.7 测试 `CCWHAT_ANALYZE_AGENT` 和 `CCWHAT_ANALYZE_TIMEOUT`
- [x] 5.8 运行完整测试，确认 export/import、Log Adapter、current session analysis 不回退（255 passed）

## 6. 手动验证

- [ ] 6.1 验证 `ccwhat -- claude` 后生成 yuanxi/generic 报告
- [ ] 6.2 验证 `ccwhat -- opencode` 后默认使用 `opencode run --format json` 生成报告
- [ ] 6.3 验证 `ccwhat -- codex` 后 Codex analyzer 以 experimental 状态运行或清晰失败
- [ ] 6.4 验证 `CCWHAT_ANALYZE_AGENT=opencode ccwhat web --agent opencode`
- [ ] 6.5 验证 `CCWHAT_ANALYZE_CMD='opencode run --format json'` 覆盖默认 analyzer

## 7. Review 修复

- [x] 7.1 修复 OpenCode DB session.agent 泄漏为 analyzer agent
- [x] 7.2 修复 normalize_session_for_report 防御（unknown agent → claude fallback）
- [x] 7.3 修复 Viewer Server 默认 analyzer agent 优先级（adapter.name 优于 session.agent）
- [x] 7.4 修复 _resolve_analyzer_timeout 未使用 spec.timeout_seconds
- [x] 7.5 实现 Codex last-message-file fallback（get_candidates 机制）
- [x] 7.6 增加 OpenCode agent=build、Viewer priority、Codex timeout/fallback 测试
- [ ] 7.7 重新手动验证 opencode/codex generic/yuanxi 报告

## 8. OpenCode 真实 JSONL 回归修复

- [x] 8.1 修复 OpenCode analyzer parser，兼容真实 `opencode run --format json` 输出中的 `part.text`
- [x] 8.2 更新 OpenCode parser 测试，使用真实 `type=text` + `part.type=text` + `part.text` 结构
- [x] 8.3 增加 OpenCode generic/yuanxi 报告链路回归测试，确认 parser 不再产出空报告
- [x] 8.4 运行针对性测试、完整测试和 OpenCode analyzer 烟测，确认现有功能不回退

## 9. OpenCode 报告渲染和时间轴修复

- [x] 9.1 修复 OpenCode 本地 DB 数字时间戳归一化，统一转为 ISO timestamp
- [x] 9.2 修复 OpenCode 工具事件使用 part/state start/end 时间，确保元析 phases 和图表有耗时数据
- [x] 9.3 修复通用报告 Mermaid fallback，渲染失败时保留原始 Mermaid 源码并给出准确错误文案
- [x] 9.4 收紧通用报告 prompt 的 Mermaid 输出约束，降低 OpenCode 生成非法 Mermaid 的概率
- [x] 9.5 增加 OpenCode 时间轴和 Mermaid fallback 回归测试
