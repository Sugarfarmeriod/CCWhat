## Why

开发者在分析 AI 服务（如 Claude、OpenAI 等）的网络请求时，缺乏一个专用的命令行工具来拦截、记录和查看 HTTP/HTTPS 流量，尤其是支持 SSE（Server-Sent Events）协议的流式响应。现有的通用抓包工具配置繁琐，且不针对 AI 接口场景做优化。

## What Changes

- 新建 `deep-ai-analysis` CLI 主命令（Python 实现），支持子命令扩展架构
- 新增 `proxy` 子命令：基于 mitmproxy 创建 HTTP/HTTPS 代理
  - 支持按域名过滤，仅记录指定域名的流量
  - 支持 SSE（Server-Sent Events）流式响应的完整记录
  - 将原始请求和响应内容持久化到本地文件
  - 支持配置代理监听端口

## Capabilities

### New Capabilities

- `cli-framework`: 主命令 `deep-ai-analysis` 的脚手架与子命令路由，使用 Python + Click 提供统一的 CLI 入口
- `proxy-interceptor`: `proxy` 子命令核心能力——内嵌 mitmproxy addon、按域名过滤流量、记录原始请求/响应（含 SSE 流）到文件

### Modified Capabilities

## Impact

- **语言**: 纯 Python 实现，使用 `click` 作为 CLI 框架，`mitmproxy` 作为代理引擎
- **新增文件**: `deep_ai_analysis/cli.py`（入口）、`deep_ai_analysis/commands/proxy.py`、`deep_ai_analysis/addons/recorder.py`
- **打包配置**: `pyproject.toml`，通过 `pip install -e .` 安装，注册 `deep-ai-analysis` 命令
- **输出产物**: 代理日志文件（`logs/YYYY-MM-DD/`），包含请求/响应的原始内容
- **无破坏性变更**
