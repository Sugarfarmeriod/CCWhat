## Context

`deep-ai-analysis` 是一个面向 AI 接口调试与分析的命令行工具集。使用 Python 实现，mitmproxy 本身也是 Python 生态，因此可以将 CLI 主框架与 mitmproxy addon 统一在同一 Python 包中，无需跨语言进程通信。

**技术栈**:
- Python 3.10+
- `click`：CLI 框架（子命令、选项解析、帮助文本）
- `mitmproxy`：HTTP/HTTPS 代理引擎（含 SSE 流拦截支持）
- `pyproject.toml`：打包与入口点注册

## Goals / Non-Goals

**Goals:**
- 提供 `deep-ai-analysis` 作为顶层命令，支持 `--help`、`--version`
- 提供 `deep-ai-analysis proxy` 子命令，在当前进程内启动 mitmproxy（via `mitmproxy.options` + `mitmproxy.tools.dump.DumpMaster`）
- 域名过滤列表在代码中配置（默认 `["api.example.com"]`，支持数组），不作为 CLI 参数
- 支持 SSE 流式响应的完整记录（逐 chunk 追加）
- 将原始请求头、请求体、响应头、响应体（含 SSE 事件流）以 JSONL 格式追加记录到文件

**Non-Goals:**
- 不提供请求内容的可视化 UI（属于后续 viewer 子命令范畴）
- 不修改或重放请求（纯被动记录）
- 不支持 WebSocket 协议

## Decisions

### 决策 1：CLI 框架选用 `click`

**选择**: `click` 库构建 CLI 主框架与子命令

**理由**:
- Python 生态最主流的 CLI 框架，与 mitmproxy 同属 Python，无跨语言边界
- `@click.group()` + `@cli.command()` 天然支持插件式子命令
- 比 `argparse` 代码更简洁，比 `typer` 依赖更轻

**备选方案**: `argparse`（标准库）→ 放弃，子命令组织比较冗长；`typer` → 引入 `pydantic` 依赖链，偏重

---

### 决策 2：在同一进程内嵌 mitmproxy（asyncio）

**选择**: 通过 `mitmproxy.tools.dump.DumpMaster` 在当前 Python 进程的 asyncio 事件循环中运行代理，而非 subprocess 启动 `mitmdump`

**理由**:
- CLI 与 addon 共享同一 Python 进程，参数传递直接（无需环境变量序列化）
- 可以在 addon 内直接引用 click 解析后的参数对象
- 错误处理、日志输出统一

**代码骨架**:
```python
import asyncio
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options

async def start_proxy(host, port, addon):
    opts = Options(listen_host=host, listen_port=port)
    master = DumpMaster(opts)
    master.addons.add(addon)
    await master.run()
```

**备选方案**: subprocess 调用 `mitmdump` → 放弃，参数传递需要序列化，跨进程调试困难

---

### 决策 3：SSE 记录策略——流式钩子 + 逐事件追加

**选择**: 在 addon 的 `response` 钩子中检测 SSE，设置 `flow.response.stream = True`，使用 `response_chunk` 流式处理器（或 mitmproxy streaming callback）逐 chunk 解析 SSE 事件并追加写入

**SSE chunk 解析逻辑**:
- 按 `\n\n` 分割事件边界
- 维护每个 flow 的缓冲区 `Dict[flow_id, str]`
- chunk 中包含完整事件时立即写入，不完整时追加到缓冲区等待下一 chunk

---

### 决策 4：日志文件格式 — JSONL，每天一个文件

**选择**: 使用 JSONL（JSON Lines）格式，每天生成一个文件，每条请求追加一行 JSON。

```
logs/
  YYYY-MM-DD.jsonl
```

每行一条完整记录：
```jsonl
{"timestamp":"2026-05-08T10:30:00.123Z","domain":"api.example.com","method":"POST","url":"https://api.example.com/v1/chat","request":{"headers":{"content-type":"application/json"},"body":"{...}"},"response":{"status":200,"headers":{"content-type":"text/event-stream"},"body":"data: {...}\n\n"},"is_sse":true,"sse_events":["data: {\"type\":\"delta\",...}","data: [DONE]"]}
```

**理由**:
- JSONL 天然支持追加写入（`append` 模式），无需文件锁或 rename 技巧
- 每天一个文件便于按日期归档和 `grep` 检索
- 相比每请求一个 JSON 文件，减少文件系统 inode 消耗
- 标准工具（`jq`、Python）均原生支持 JSONL

---

### 决策 5：打包方式使用 `pyproject.toml`

**选择**: 使用 `pyproject.toml`（PEP 517/518）+ `setuptools` 或 `hatchling` 打包，通过 `[project.scripts]` 注册 `deep-ai-analysis` 入口点

```toml
[project.scripts]
deep-ai-analysis = "deep_ai_analysis.cli:cli"
```

安装方式: `pip install -e .`（开发模式）或 `pip install .`

## Risks / Trade-offs

- **[风险] mitmproxy 版本 API 差异** → 缓解：锁定 `mitmproxy>=10.0` 版本，`response_chunk` API 在 mitmproxy 10+ 稳定；在 `pyproject.toml` 中声明最低版本
- **[风险] HTTPS 证书信任** → 缓解：`proxy` 命令启动时打印 CA 证书路径和安装指引（`~/.mitmproxy/mitmproxy-ca-cert.pem`）
- **[风险] asyncio 与 click 集成** → 缓解：click 子命令通过 `asyncio.run()` 包装 `start_proxy` coroutine，无需第三方 async click 扩展
- **[Trade-off] 进程内运行 mitmproxy** → 优点：参数共享简单；缺点：mitmproxy 内部日志与 CLI 输出混合，需设置 mitmproxy 日志级别为 WARNING 以减少噪音
