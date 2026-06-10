## 1. Implement start-mc Command

- [x] 1.1 创建 `deep_ai_analysis/commands/start_mc.py`，使用 `@click.command(name="start-mc")` 定义子命令，添加 `--port` 选项（int，默认 7788，与 proxy 子命令一致）
- [x] 1.2 在命令函数中构造 `HTTPS_PROXY=http://127.0.0.1:<port>` 和 `NODE_EXTRA_CA_CERTS=<home>/.mitmproxy/mitmproxy-ca-cert.pem`，通过 `os.environ.copy()` 叠加到父进程环境
- [x] 1.3 在启动前检测 CA 证书文件是否存在，不存在时向 stderr 打印警告（提示先运行 `deep-ai-analysis proxy`）
- [x] 1.4 使用 `subprocess.run(["mc", "--code"], env=merged_env)` 启动 mc，捕获 `FileNotFoundError` 并打印友好错误信息后 `sys.exit(1)`
- [x] 1.5 将 `mc` 的退出码透传给 `sys.exit(result.returncode)`

## 2. Register Subcommand

- [x] 2.1 在 `deep_ai_analysis/cli.py` 中导入 `start_mc` 命令并调用 `cli.add_command(start_mc)`

## 3. Verification

- [x] 3.1 运行 `deep-ai-analysis --help`，确认 `start-mc` 出现在子命令列表中
- [x] 3.2 运行 `deep-ai-analysis start-mc --help`，确认显示 `--port` 选项且默认值为 7788
- [x] 3.3 验证 mc 不存在场景：临时重命名或在无 mc 环境中运行，确认打印 "mc command not found" 并以退出码 1 退出
- [x] 3.4 验证 CA 证书缺失场景：临时移走证书文件，确认打印警告但仍尝试启动 mc
