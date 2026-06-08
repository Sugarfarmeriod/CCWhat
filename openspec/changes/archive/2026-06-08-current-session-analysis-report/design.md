## Context

当前 `viewer/server.py` 提供只读的 session、raw req/resp、export 等 HTTP API，`viewer/claude-log.html` 在浏览器中加载 session JSONL 并按 turn 展示。用户希望在当前页面内临时生成当前 session 的 Agent 交互分析报告，prompt 模板已经移动到 `deep_ai_analysis/assets/analyze_prompt.md` 并纳入 Python package data。

这个功能会引入一次性外部进程调用：后端需要启动 `mc --code -p -`，通过 stdin 注入完整分析 prompt，并从 stdout 读取 Markdown 报告。分析结果不写入 Claude session、不落盘、不导出，但前端需要在当前页面生命周期内按 session 缓存，避免用户点击日志详情后报告丢失。

## Goals / Non-Goals

**Goals:**
- 在 Claude Log 页面为当前已加载 session 提供一键分析入口
- 通过 `/api/analyze` 后端接口临时调用 `mc --code -p -`
- 使用包内 `analyze_prompt.md` 模板和当前 session 内容生成报告
- 在前端展示 loading、成功报告和错误状态
- 在前端按 `sessionId` 内存缓存报告，支持反复查看和重新分析
- 对 `mc` 不存在、超时、非零退出和空输出提供明确错误
- 用自动化测试覆盖 prompt 拼接、API 行为和前端入口存在性

**Non-Goals:**
- 不支持 selected turns、当前筛选结果、跨 session 或多 session 分析
- 不做流式输出
- 不持久化报告，不写回 session 日志；刷新页面后报告可以丢弃
- 不新增 OpenAI/Anthropic SDK 依赖，仍使用本机 `mc` CLI
- 不在浏览器中直接执行命令或打开真实 Terminal

## Decisions

### Decision 1：API 使用 POST `/api/analyze`

分析请求包含 session ID，并可能触发较长耗时的外部进程，因此使用 POST 而不是 GET。第一版请求体保持极简：

```json
{"sessionId": "<current-session-id>"}
```

后端通过已有 `get_session(session_id, projects_dir)` 读取数据，避免前端上传完整 session 内容，也避免前端构造的数据与磁盘真实 session 不一致。

### Decision 2：后端负责序列化当前 session 内容

后端将当前 session 序列化为稳定文本块，包含：
- `sessionId`
- `projectDir`
- main entries
- subagent entries 及其 metadata

第一版不重建前端 turns 结构，因为需求范围是“当前 session”，prompt 本身要求分析 captured interaction data。直接提供按文件顺序排序的 JSON 数据更完整，也减少前后端 turn 算法不一致的风险。

### Decision 3：通过 `subprocess.run` 调用 `mc --code -p -`

使用 `subprocess.run(["mc", "--code", "-p", "-"], input=prompt, capture_output=True, text=True, timeout=...)`。相比手写 `Popen` 循环，第一版没有流式输出需求，`run` 更简单且便于测试 mock。

默认 timeout 设为 120 秒。若后续需要取消或流式输出，再改为 Popen 管理进程生命周期。

### Decision 4：prompt 模板作为 package resource 读取

使用 `importlib.resources.files("deep_ai_analysis").joinpath("assets/analyze_prompt.md")` 读取模板，避免依赖当前工作目录。模板必须包含 `{{content}}`，后端以 session 内容替换该占位符；若缺失则把 session 内容追加在模板末尾作为 fallback。

### Decision 5：前端按 sessionId 做内存缓存

前端维护一个只存在于当前页面生命周期的对象：

```js
const analysisReports = {
  [sessionId]: {
    report,
    elapsedMs,
    truncated,
    createdAt
  }
}
```

这不是持久化：刷新页面会丢失缓存，后端也不保存报告。它只解决页面内交互问题：用户分析完成后点击左侧任意日志条目，detail panel 可以切换到日志详情；再点击“查看分析报告”即可从内存缓存恢复报告。

### Decision 6：单按钮入口 + 报告内重新分析

Claude Log 页面新增一个主按钮，状态由当前 session 是否已有缓存报告决定：

- 没有报告：显示“分析当前 Session”
- 已有报告：显示“查看分析报告”
- 分析中：显示“分析中...”并禁用

报告视图顶部提供“重新分析”按钮。重新分析成功时覆盖当前 session 的缓存报告；重新分析失败时保留旧报告，并在页面内展示错误原因。

## Risks / Trade-offs

- `mc` 未安装或 PATH 不可见 → 返回明确错误，前端展示失败原因
- session 过大导致上下文过长或耗时过久 → 第一版不做复杂分片，但应限制输入字符数并在内容被截断时标记
- `mc` 输出非 Markdown 或包含异常文本 → 前端按 Markdown/纯文本渲染，不假设结构化 JSON
- HTTP server 单线程处理长请求会阻塞其他请求 → 当前 viewer 使用本地单用户场景，第一版可接受；若体验受影响，后续改为后台 job + polling
- 分析内容可能包含敏感日志 → 功能只在本机执行，报告只保存在页面内存中，不写入 localStorage、文件或导出包
- 重新分析失败可能覆盖已有可用报告 → 失败时保留旧缓存，仅展示错误状态

## Migration Plan

1. 新增 prompt resource 读取和 session 内容序列化 helper。
2. 新增 `/api/analyze` POST 处理，调用 `mc --code -p -` 并返回 JSON。
3. Claude Log 页面新增分析按钮、loading 状态、报告展示、前端内存缓存和重新分析入口。
4. 新增 API 和前端静态回归测试。
5. 跑 unittest、py_compile、OpenSpec strict validate。

## Open Questions

- 是否需要后续将单线程 HTTP server 改为 threaded server，以避免分析期间阻塞页面其他请求。
- 后续是否需要把报告导出为 Markdown 文件或附加到诊断包中；第一版明确不做。
