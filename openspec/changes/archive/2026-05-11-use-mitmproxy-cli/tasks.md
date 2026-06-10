## 1. recorder.py — 改用环境变量读取输出目录

- [x] 1.1 在 `recorder.py` 顶层添加从 `DAA_OUTPUT_DIR` 环境变量读取输出目录的逻辑，构造 `RecorderAddon` 时使用该路径
- [x] 1.2 移除 `RecorderAddon.__init__` 的 `output_dir` 参数，改为在 `__init__` 内从环境变量读取

## 2. proxy.py — 改用 subprocess 调用 mitmdump

- [x] 2.1 移除 `asyncio`、`mitmproxy` 相关 import
- [x] 2.2 实现新的 `proxy` 函数：设置 `DAA_OUTPUT_DIR` 环境变量，组装 `mitmdump` 命令行参数
- [x] 2.3 用 `subprocess.run` 调用 `mitmdump`，`FileNotFoundError` 时提示 `brew install mitmproxy`
- [x] 2.4 移除 `_start_proxy` async 函数

## 3. pyproject.toml — 移除 mitmproxy 依赖

- [x] 3.1 从 `dependencies` 列表中移除 `mitmproxy>=10.0`

## 4. install.sh — 添加 brew install mitmproxy

- [x] 4.1 在 `pip install` 之前添加 brew 安装逻辑：检测 brew 是否可用，可用则执行 `brew install mitmproxy`，不可用则打印提示跳过

## 5. README — 更新安装说明

- [x] 5.1 将环境要求中的 mitmproxy 说明改为"通过 brew 安装"，移除"作为依赖自动安装"的表述

## 6. 验证

- [x] 6.1 执行 `deep-ai-analysis proxy`，确认 mitmdump 进程正常启动，日志写入正确目录
