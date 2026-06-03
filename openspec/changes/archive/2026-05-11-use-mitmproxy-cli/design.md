## Context

`mitmdump` 支持 `-s <script.py>` 参数加载 addon，与 Python API 的 `master.addons.add()` 行为等价。`recorder.py` 无需修改，可直接作为 script 传给 `mitmdump`。

`recorder.py` 位于包内（`deep_ai_analysis/addons/recorder.py`），安装后路径通过 `importlib.resources` 或 `__file__` 获取。

## Goals / Non-Goals

**Goals:**
- `proxy` 命令调用系统 `mitmdump`，行为与现在一致（端口、输出目录、addon 功能不变）
- 移除 Python 依赖中的 `mitmproxy`，降低 wheel 大小
- `install.sh` 通过 brew 安装 mitmproxy

**Non-Goals:**
- 不修改 `recorder.py` 的 addon 逻辑
- 不支持非 macOS 平台的 brew 安装（当前用户为 macOS）

## Decisions

**`mitmdump` 调用方式：**

```bash
mitmdump --listen-host 127.0.0.1 --listen-port <port> \
         --set confdir=~/.mitmproxy \
         -s <recorder.py 绝对路径> \
         --set hardump=/dev/null
```

addon 脚本路径通过 `Path(__file__).parent / "../addons/recorder.py"` 解析为绝对路径，确保安装后也能找到。

**环境变量传参：** `recorder.py` 需要 `output_dir` 参数，当前通过构造函数传入。切换到 CLI 模式后，改用环境变量 `DAA_OUTPUT_DIR` 传递，`recorder.py` 在模块顶层读取。

**`mitmdump` 不存在时的错误处理：** `FileNotFoundError` 时提示用户 `brew install mitmproxy`。

## Risks / Trade-offs

- [风险] brew 安装的 mitmproxy 版本与 addon API 不兼容 → 当前 addon 只用了基础 hook（`responseheaders`/`response`），兼容性风险低
- [权衡] 移除 Python mitmproxy 依赖后，`recorder.py` 顶层的 `from mitmproxy import http` 在非运行时 import 会失败 → 已有的 `try/except ImportError` 保护可去掉，因为现在不从 Python 导入 mitmproxy
