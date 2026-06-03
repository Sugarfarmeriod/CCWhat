## Why

当前所有 session 的原始日志混写在同一个日期文件中（`YYYY-MM-DD.jsonl`），不同 Claude Code session 的流量无法区分，后续分析时需要依赖 `X-Claude-Code-Session-Id` header 手动过滤。将 sessionId 作为路径层级，每个 session 的日志独立存放，查找和管理更直观。

## What Changes

- 原始日志文件路径从 `<output_dir>/YYYY-MM-DD.jsonl` 改为 `<output_dir>/<sessionId>/YYYY-MM-DD.jsonl`
- sessionId 从每条请求的 header `X-Claude-Code-Session-Id` 动态提取；若该 header 不存在则使用 `unknown`
- 目录按需自动创建

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `proxy-interceptor`: 日志文件路径加入 sessionId 子目录层级

## Impact

- `deep_ai_analysis/addons/recorder.py`：`_jsonl_path()` 方法改为接受 session_id 参数，路径插入 sessionId 子目录；在 `response` 钩子中从 flow.request.headers 提取 session_id
