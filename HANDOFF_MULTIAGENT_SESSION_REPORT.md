# Multi-Agent Session Report 交接说明

## 背景

这个分支的核心目标是把 `session_report` / viewer 报告链路从 Claude-only 适配，迁移成真正可覆盖 Claude / Codex / OpenCode 的多 agent 模型。

本轮工作的重点不是单纯修一个页面报错，而是把“表面支持多 agent、底层仍然沿用 Claude 假设”的残留逐步拔掉。

---

## 这次已经完成的改动

### 1. 新增统一报告模型与 normalize 层

已引入统一报告模型：

- `ccwhat/session_report/model.py`
  - `ReportSession`
  - `ReportAgent`
  - `ReportEvent`
  - `ReportTurn`
  - `ReportProjectRef`

已新增 normalize 层：

- `ccwhat/session_report/normalize.py`

作用：
- Claude session 继续兼容 `main/subagents`
- Codex / OpenCode 统一走 `events/turns`
- `session_report/core.py` / pipeline 不再直接依赖 Claude 专有 session 结构

### 2. HTML 报告链路已切到统一模型

关键文件：

- `ccwhat/session_report/core.py`
- `ccwhat/session_report/pipeline.py`
- `viewer/server.py`
- `ccwhat/assets/session-report/*`

已完成：
- HTML 报告（元析 / generic）基于 normalize 后的数据生成
- viewer `/api/analyze` 的 HTML 报告分支会传递当前 session 的 `primary_agent_type`
- analyzer command 不再默认固定 Claude

### 3. analyzer 默认命令改成 agent-aware

关键文件：

- `ccwhat/analyzer.py`

已完成：
- Claude 默认 analyzer：`claude -p -`
- Codex 默认 analyzer：`codex exec -`
- 显式 `analyzer_cmd` 仍优先于 fallback
- `CCWHAT_ANALYZE_CMD` 仍优先于 agent fallback
- analyzer command 现在会尽量解析本机绝对二进制路径，避免 PATH 差异导致找不到命令

### 4. 这轮新补的更深层修复

这轮不是只修 HTML 分支，而是继续处理我第二次 review 出来的深层 multi-agent 残留：

#### 4.1 legacy analyze prompt 不再固定吃 `main/subagents`

`ccwhat/analyzer.py` 里的 `serialize_session_for_analysis()` 已改为：
- 先 `normalize_session_for_report(session)`
- 再序列化统一报告模型

这意味着 legacy `/api/analyze` 也不再是 Claude-only schema。

#### 4.2 legacy `/api/analyze` 分支已支持 agent-aware analyzer

`viewer/server.py` 的旧 markdown analyze 分支已改为：
- 先 normalize session
- 再把 `primary_agent_type` 传给 `run_mc_analysis()`

这修掉了“HTML 分支是 multi-agent，legacy 分支仍然默认 Claude 思维”的残留。

#### 4.3 `/api/session/<id>` 不再用 `ClaudeAdapter` 硬补 events / turns

之前 viewer 兼容层里有这类逻辑：
- 如果没有 `events`
- 就直接用 `ClaudeAdapter.raw_to_normalized_events()`
- 再用 `ClaudeAdapter()._build_turns(...)`

这本质上是 Claude fallback。

现在改成：
- 统一先 `normalize_session_for_report(data)`
- 然后从 normalized model 回填 `events` / `turns`

这一步很关键，因为它把 session API 的兼容层也从 Claude 专属逻辑里抽出来了。

#### 4.4 OpenCode 不再错误进入 stdin/stdout analyzer 协议

这是这轮最重要的现实修复之一。

已确认：
- `opencode run` **不兼容** 当前 `run_mc_analysis()` 采用的统一子进程协议
- 当前 analyzer runner 的协议前提是：
  - stdin 输入 prompt
  - 阻塞等待
  - stdout 返回完整文本
- 这个协议对 Claude / Codex 是成立的
- 对 OpenCode 当前 CLI 不是

所以现在改成：
- 默认只把 Claude / Codex 视作兼容当前 stdin runner 的 agent
- OpenCode 如果没有显式提供自定义 analyzer command，会直接 fast-fail：
  - code: `analyzer_not_supported`
- 不再进入 `opencode run` 然后卡 120 秒超时

这一步的意义是：
- 先把错误从“假通用 + 超时”纠正为“明确不支持当前 analyzer 协议”
- 避免再次误判为 Claude 登录问题或 OpenCode 命令卡死问题

---

## 这次遇到过的关键 bug

### Bug 1：generic 报告显示 Claude 登录错误

现象：
- 用户在非 Claude 场景下生成 generic 报告
- 页面显示：`Analysis failed: Not logged in · Please run /login`

根因：
- 当时 analyzer fallback 仍默认固定 `claude -p -`
- 所以即使 session 来自 Codex / OpenCode，报告分析也误走 Claude

状态：
- 已修掉

### Bug 2：OpenCode 报告分析 120 秒超时

现象：
- 报告生成返回：`Analysis timed out after 120 seconds.`

根因：
- multi-agent 命令分流已经改成走 OpenCode
- 但底层 analyzer runner 仍假设所有 agent 都支持 stdin/stdout 单次分析协议
- `opencode run` 不满足这套协议，所以会卡住直到超时

状态：
- 已改为 fast-fail（`analyzer_not_supported`）
- 还没有实现 OpenCode 专属 analyzer runner

### Bug 3：`viewer/server.py` 出现 `UnboundLocalError`

现象：
- 改造后局部作用域里出现 `normalize_session_for_report` 未绑定

根因：
- 函数内部 import 与外层同名符号混用，触发 Python 局部变量解析问题

状态：
- 已修掉

### Bug 4：`ccwhat/analyzer.py` 与 `session_report.pipeline` 循环依赖

现象：
- 跑完整测试时，`ImportError: partially initialized module 'ccwhat.analyzer'`

根因：
- `analyzer.py` 顶层 import `session_report.normalize`
- `session_report.pipeline` 又 import `analyzer`
- 形成循环依赖

状态：
- 已通过函数内延迟 import 打断

### Bug 5：测试对命令路径断言过死

现象：
- 本地命令解析后会变成绝对路径，例如：
  - `/opt/homebrew/bin/claude`
  - `/Applications/Codex.app/.../codex`
- 旧测试断言写死成 `claude` / `codex`

状态：
- 已改为断言“参数尾部 + 二进制名”，不再依赖是否是裸命令

---

## 目前代码状态

本轮结束后，已经确认通过：

- `python3 -m unittest tests.test_current_session_analysis`
- 结果：`63/63 OK`

所以当前这批已提交代码，在测试覆盖范围内是稳定的。

---

## 还没有完成、下一位 agent 需要继续做的事

### P0：给 OpenCode 实现真正可用的 analyzer runner

当前 OpenCode 的策略只是：
- 不再误走错误协议
- 改成明确 fast-fail

这只是止血，不是最终完成态。

下一步需要做的是：
- 调研 OpenCode CLI / server 的真实非交互分析入口
- 单独实现一条 OpenCode analyzer runner
- 不要强行复用 `subprocess.run(..., input=prompt)` 这条 Claude/Codex 协议

换句话说：
- 现在已经完成“不要伪适配”
- 还没完成“真正适配 OpenCode 报告分析”

### P1：继续清理全局 Claude-first 默认值

这轮我已经修掉了最危险的几个运行时残留，但仓库里仍可能存在这些次级问题：
- `ccwhat web --agent` 默认值还是 `claude`
- 某些错误文案仍写着 “Only Claude Code is supported”
- viewer 前端某些 badge / fallback 文案可能仍默认显示 claude

这些不一定会立即导致功能 bug，但会继续放大系统的 Claude-first 倾向。

### P2：确认 `/api/session` 输出 shape 是否要正式文档化

这轮我把 `/api/session/<id>` 的 `events` / `turns` 输出统一成 normalized 风格：
- `agentId`
- `startedAt`
- `endedAt`
- `events: [{id: ...}]`

这对统一性是好事，但下一位 agent 最好再确认：
- 前端是否已经完全基于这套 shape
- 是否要补到 spec / 文档里，避免后续又被某个 adapter 的原始格式带歪

### P3：真实环境回归验证

目前通过的是单测和我们本机的命令探测。

下一位 agent 最好补做：
- Claude session → generic / 元析报告
- Codex session → generic / 元析报告
- OpenCode session → fast-fail 是否前端提示清晰
- 若后续接入 OpenCode 专属 analyzer runner，再补真实端到端验证

---

## 推荐下一步落点

如果时间有限，建议下一位 agent 直接按这个顺序继续：

1. 先做 OpenCode 专属 analyzer runner 方案设计
2. 明确它是否应走：
   - CLI 参数模式
   - headless server / attach 模式
   - 还是别的 provider API 方式
3. 只在确认真实协议后再接入 `run_mc_analysis()` 的分流体系
4. 最后再处理那些次级 Claude-first 默认值与文案

---

## 最关键的一句话总结

**当前已经解决的问题是：系统不再把多 agent 场景伪装成 Claude-compatible。**

也就是说：
- session schema 已统一
- HTML 报告链路已统一
- legacy analyze 输入模型已统一
- viewer session API 兼容层已不再依赖 ClaudeAdapter
- OpenCode 已不再被错误塞进 Claude/Codex 的 analyzer 协议

**当前仍未解决的问题是：OpenCode 的“真正可用分析执行器”还没有实现。**

这是下一位 agent 最应该继续接的点。
