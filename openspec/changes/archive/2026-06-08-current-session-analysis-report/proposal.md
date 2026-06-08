## Why

当前 Claude Log 页面只能查看原始交互记录，用户需要离开页面手动整理上下文并调用 Claude Code 才能获得会话级质量分析。现在需要在页面内提供一个临时分析入口，让用户一键生成当前 session 的结构化分析报告，而不把分析对话写回日志或持久化。

## What Changes

- 新增 `/api/analyze` 接口，接收当前 session ID，读取该 session 的主日志和 subagent 日志并构造分析输入。
- 后端使用包内 `deep_ai_analysis/assets/analyze_prompt.md` 模板，将 session 内容填入 `{{content}}` 后通过 `mc --code -p -` 的 stdin 临时调用 Claude Code。
- 前端 Claude Log 页面新增“分析当前 Session”按钮和报告展示面板，用户只能分析当前已加载 session。
- 分析请求执行期间展示 loading 状态，完成后渲染 Markdown 报告；失败时展示可理解的错误信息。
- 第一版不支持 selected turns、筛选结果、跨 session 分析、流式输出或报告持久化。

## Capabilities

### New Capabilities

- `current-session-analysis-report`: 定义当前 session 临时分析报告的 API、前端入口、prompt 模板使用、执行边界和错误处理。

### Modified Capabilities

None.

## Impact

- 影响代码：`viewer/server.py`、`viewer/claude-log.html`、`deep_ai_analysis/assets/analyze_prompt.md`、`pyproject.toml`
- 影响测试：新增 `/api/analyze` 后端测试和前端静态行为回归测试
- 运行依赖：接收方本机需要可执行 `mc` 命令；接口需要处理 `mc` 不存在、非零退出、超时和输出为空
- 安全与性能：分析内容来自本地 session 日志，后端需要限制请求范围为当前 session，避免任意命令执行或跨文件读取
