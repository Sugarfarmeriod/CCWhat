## Context

CCWhat 当前已经具备多 Agent Log Adapter：Claude Code、Codex、OpenCode 的本地 session 可以通过不同 adapter 读取并归一化为 `events/turns/usage`。但报告生成链路仍沿用早期 `ccwhat.analyzer.run_mc_analysis()` 的单一 stdin/stdout 子进程协议。

当前最大问题是 `ccwhat -- <target>` 的 `target_args` 被传入 Viewer Server 的 `analyzer_cmd`，导致“启动 observed agent 的命令”和“生成报告的 analyzer 命令”混用。例如 `ccwhat -- opencode` 可能让报告生成执行裸 `opencode`，从而进入 TUI 并超时。正确的 OpenCode 非交互协议应是 `opencode run --format json`。

本 change 只定义并实现最小 Analyzer Adapter 协议，不做复杂重试，也不引入外部 API provider。

## Goals / Non-Goals

**Goals:**

- 分离 observed agent 与 analyzer command。
- 为 Claude、OpenCode、Codex 定义清晰的 analyzer 协议。
- 支持 prompt 通过 stdin 传入。
- 支持三类输出解析：
  - `stdout`
  - `jsonl_text`
  - `last_message_file`
- OpenCode 使用 `opencode run --format json` 作为默认 analyzer。
- Codex 纳入本次改造，但标记为 experimental。
- timeout 可配置。
- 让报告 pipeline 能明确知道 analyzer 的状态、错误 code 和输出来源。

**Non-Goals:**

- 不实现复杂重试、自动降级、并发多 analyzer 竞速。
- 不引入 OpenAI API、Anthropic API 或其他外部 API analyzer。
- 不要求 Codex experimental analyzer 在所有机器上稳定通过真实端到端。
- 不改变 Log Adapter 的读取格式。
- 不把 Raw Req/Resp 页面和 Agent Log 页面合并。

## Decisions

### Decision 1: Observed Agent 与 Analyzer Agent 分离

Observed Agent 是用户通过 `ccwhat -- <target>` 启动和观测的 agent。Analyzer Agent 是生成报告的 agent。两者可以相同，但不得共享同一个命令参数变量。

关键原则：

- `target_args` 只能用于启动 observed agent。
- `agent_name` 用于选择 Log Adapter。
- `analyzer_agent` 用于选择 Analyzer Adapter。
- `analyzer_cmd` 只能来自显式配置或环境变量，不能来自 `target_args`。

### Decision 2: Analyzer 协议使用 Adapter/Registry

新增 analyzer 协议模型，建议字段：

- `name`
- `default_command`
- `output_mode`
- `experimental`
- `timeout_seconds`
- `parse_output(stdout, stderr, extra_files)`

可放在 `ccwhat/analyzers/`，也可以先在 `ccwhat/analyzer.py` 中小步实现。为了长期扩展，推荐新建模块：

- `ccwhat/analyzers/base.py`
- `ccwhat/analyzers/claude.py`
- `ccwhat/analyzers/opencode.py`
- `ccwhat/analyzers/codex.py`
- `ccwhat/analyzers/registry.py`

### Decision 3: 默认 analyzer 协议

Claude：

```bash
claude -p -
```

- output mode: `stdout`
- stable

OpenCode：

```bash
opencode run --format json
```

- prompt: stdin
- output mode: `jsonl_text`
- stable
- parser 从 stdout 的 JSONL 中提取 `type == "text"` 或 `part.type == "text"` 的文本，并拼接为最终报告
- parser 可保留 `step_finish.tokens` 作为 analyzer usage metadata

Codex：

```bash
codex exec --json --ephemeral --ignore-user-config -
```

- prompt: stdin
- output mode: `jsonl_text`
- experimental
- parser 从 JSONL event 中提取最终 agent message / assistant text

Codex 备用候选：

```bash
codex exec --output-last-message <tmpfile> --ephemeral --ignore-user-config -
```

- output mode: `last_message_file`
- experimental
- 使用临时文件读取最终消息

### Decision 4: 配置优先级

建议优先级：

1. 显式传入的 `analyzer_cmd`
2. 环境变量 `CCWHAT_ANALYZE_CMD`
3. 显式传入的 `analyzer_agent`
4. 环境变量 `CCWHAT_ANALYZE_AGENT`
5. observed agent 对应的 analyzer adapter

注意：第 5 步可以默认“observed agent == analyzer agent”，但只能通过 analyzer registry 选择默认 analyzer 命令，不得使用 observed agent 的 `target_args`。

timeout 优先级：

1. 显式参数 `analyzer_timeout`
2. 环境变量 `CCWHAT_ANALYZE_TIMEOUT`
3. analyzer adapter 默认 timeout
4. 全局默认 timeout

### Decision 5: 报告 API 仍可同步，但协议必须清晰

本 change 不强制把 `/api/analyze` 改成异步 job/poll 模式。同步接口可以继续存在，但必须：

- 使用正确 analyzer command。
- 对 timeout 返回明确 code。
- 对 unsupported/experimental 失败返回清晰错误。
- 在响应中包含 analyzer metadata，例如 `analyzerAgent`、`analyzerOutputMode`、`experimental`、`llmStatus`。

## Risks / Trade-offs

- [Risk] Codex experimental analyzer 在部分机器仍可能超时。  
  Mitigation: 标记 experimental，保留 timeout 配置，响应中返回清晰 code，不把它伪装成 stable。

- [Risk] OpenCode JSONL 输出格式可能随版本变化。  
  Mitigation: parser 兼容 `type == "text"` 和 `part.type == "text"`，保留 raw preview 方便诊断。

- [Risk] 继续同步 `/api/analyze` 可能让长报告等待较久。  
  Mitigation: 本次先保证命令协议正确；异步 job/poll 另开 change。

- [Risk] 用户只安装某一个 agent。  
  Mitigation: 默认 analyzer 可以跟 observed agent 一致，但必须使用 analyzer registry 中的非交互协议；不可直接使用启动命令。

## Migration Plan

1. 新增 analyzer 协议模型和 registry。
2. 修正 `ccwhat/commands/run.py`，停止把 `target_args` 传给 `_start_managed_web` 的 `analyzer_cmd`。
3. 为 Viewer Server 增加 `analyzer_agent` 和 `analyzer_timeout` 传递能力。
4. 将 `run_mc_analysis()` 改造成按 analyzer spec 选择命令和解析输出。
5. 为 OpenCode JSONL 和 Codex experimental JSONL/last-message 增加解析测试。
6. 补充 `ccwhat -- opencode/codex` 不再把 target args 当 analyzer cmd 的回归测试。

## Open Questions

- Codex 的默认 experimental 模式优先使用 `--json`，还是优先使用 `--output-last-message`？
- 是否需要在 UI 中显示 Codex analyzer experimental 标记？
- 是否要在下一阶段把 `/api/analyze` 改成异步 job/poll？
