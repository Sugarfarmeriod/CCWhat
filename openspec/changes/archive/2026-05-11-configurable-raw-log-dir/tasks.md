## 1. 定义常量

- [x] 1.1 在 `deep_ai_analysis/config.py` 中新增 `DEFAULT_RAW_LOG_DIR: Path = Path.home() / ".deep-ai-analysis" / "raw-req-resp"`

## 2. 更新命令默认值

- [x] 2.1 在 `deep_ai_analysis/commands/proxy.py` 中将 `--output` 的 `default` 改为引用 `DEFAULT_RAW_LOG_DIR`
- [x] 2.2 在 `deep_ai_analysis/commands/web_server.py` 中将 `--logs-dir` 重命名为 `--req-resp-dir`，默认值改为引用 `DEFAULT_RAW_LOG_DIR`，同步更新函数参数名及传参

## 3. 更新 README

- [x] 3.1 在 `README.md` 的 `proxy` 命令说明中更新默认 `--output` 路径
- [x] 3.2 在 `README.md` 的 `web-server` 命令说明中将 `--logs-dir` 改为 `--req-resp-dir` 并更新默认路径

## 4. 验证

- [x] 4.1 运行 `deep-ai-analysis proxy --help` 和 `deep-ai-analysis web-server --help`，确认选项名和默认路径正确
