## 1. Project Setup

- [x] 1.1 创建 `pyproject.toml`，配置项目名称、版本、Python 版本要求（>=3.10）、依赖（`click>=8.0`、`mitmproxy>=10.0`），并在 `[project.scripts]` 中注册 `deep-ai-analysis = "deep_ai_analysis.cli:cli"`
- [x] 1.2 创建 Python 包目录结构：`deep_ai_analysis/__init__.py`、`deep_ai_analysis/commands/__init__.py`、`deep_ai_analysis/addons/__init__.py`
- [x] 1.3 执行 `pip install -e .` 验证包可安装，`deep-ai-analysis --version` 可运行

## 2. CLI Framework

- [x] 2.1 创建 `deep_ai_analysis/cli.py`，使用 `@click.group()` 定义主命令 `cli`，设置 `invoke_without_command=True`（无子命令时显示帮助），添加 `--version` 选项
- [x] 2.2 在 `cli.py` 中通过 `cli.add_command()` 注册子命令，确保未知子命令时 click 自动打印错误并以非 0 退出
- [x] 2.3 验证：`deep-ai-analysis --help` 显示子命令列表；`deep-ai-analysis --version` 输出版本；`deep-ai-analysis badcmd` 非 0 退出

## 3. Proxy Subcommand Entry

- [x] 3.1 创建 `deep_ai_analysis/commands/proxy.py`，使用 `@click.command()` 定义 `proxy` 子命令，添加选项：`--port`（int，默认 **7788**）、`--output`（Path，默认 `./logs`）；**不添加 `--domain` 参数**
- [x] 3.2 在 `deep_ai_analysis/config.py` 中定义 `RECORD_DOMAINS: list[str] = ["api.example.com"]`，供 addon 导入使用
- [x] 3.3 在命令入口处检测 `mitmproxy` 是否可导入（`try: import mitmproxy`），不可用时打印安装指引并调用 `sys.exit(1)`
- [x] 3.4 使用 `asyncio.run()` 调用 `start_proxy(port, output_dir)` coroutine，处理 `OSError`（端口占用）并打印友好错误信息

## 4. mitmproxy Addon — Recorder

- [x] 4.1 创建 `deep_ai_analysis/addons/recorder.py`，定义 `RecorderAddon` 类，`__init__` 接收 `output_dir: Path`，从 `config.RECORD_DOMAINS` 读取域名过滤列表，初始化 per-flow SSE 缓冲字典 `_sse_buffers: dict`
- [x] 4.2 实现域名过滤辅助方法 `_should_record(flow)`：检查 `flow.request.pretty_host` 是否在 `RECORD_DOMAINS` 列表中
- [x] 4.3 实现 `responseheaders(flow)` 钩子：检测 `content-type: text/event-stream`，若是则设置 `flow.response.stream = True` 并在 `_sse_buffers` 中为该 flow 初始化空缓冲（`{"events": [], "buffer": ""}`）
- [x] 4.4 实现 SSE streaming callback：接收 chunk bytes，解码后与缓冲区拼接，按 `\n\n` 分割提取完整事件，追加到 `_sse_buffers[flow.id]["events"]` 列表；不完整部分留在 `"buffer"` 中等待下一 chunk
- [x] 4.5 实现 `response(flow)` 钩子：
      - 调用 `_should_record(flow)` 过滤
      - 确定当天 JSONL 文件路径：`output_dir / f"{date.today()}.jsonl"`，目录不存在时自动创建
      - 构造记录 dict（含 `is_sse` 标志、`sse_events` 列表，SSE 时 `response.body` 为所有事件拼接）
      - 以 **追加模式**（`"a"`）打开 JSONL 文件，写入 `json.dumps(record, ensure_ascii=False) + "\n"`

## 5. Proxy Master Bootstrap

- [x] 5.1 在 `deep_ai_analysis/commands/proxy.py` 中实现 `start_proxy` coroutine：创建 `mitmproxy.options.Options(listen_host="127.0.0.1", listen_port=port)`，实例化 `DumpMaster(opts)`，添加 `RecorderAddon(output_dir)` 实例，调用 `await master.run()`
- [x] 5.2 在启动前打印代理地址（`http://127.0.0.1:<port>`）、CA 证书路径（`~/.mitmproxy/mitmproxy-ca-cert.pem`）和当前生效的域名过滤列表（从 `config.RECORD_DOMAINS` 读取）
- [x] 5.3 捕获 `KeyboardInterrupt`（Ctrl+C），调用 `master.shutdown()`，打印关闭提示，等待最多 5 秒后以退出码 0 退出

## 6. Verification

- [x] 6.1 运行 `deep-ai-analysis --help` 和 `deep-ai-analysis proxy --help`，确认默认端口显示为 7788，无 `--domain` 选项
- [x] 6.2 启动 `deep-ai-analysis proxy`，配置 curl 使用代理，执行请求到 `api.example.com`，验证 `logs/YYYY-MM-DD.jsonl` 生成且每条记录是合法的单行 JSON
- [x] 6.3 向非过滤域名（如 `httpbin.org`）发送请求，验证 JSONL 文件中无该域名的记录
- [x] 6.4 使用本地 mock SSE 服务或实际 SSE 端点，验证 `is_sse: true`、`sse_events` 包含所有事件，且整条记录为 JSONL 文件中的单行
- [x] 6.5 在 SSE 连接活跃时按 Ctrl+C，确认代理优雅关闭且已接收的 SSE 事件被完整保存到 JSONL
