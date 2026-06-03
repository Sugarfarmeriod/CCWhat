# mitmproxy addon import 问题复盘

## 背景

`deep-ai-analysis proxy` 会启动一个本地 HTTP/HTTPS 代理，用 mitmproxy 录制目标域名的请求和响应。`install.sh` 的安装方式是：

1. 用当前环境的 `pip` 安装 `deep_ai_analysis-0.1.1-py3-none-any.whl`。
2. 如果本机没有 mitmproxy，则通过 Homebrew 安装 mitmproxy。

这会形成两个运行环境：

- `deep-ai-analysis` 位于用户当前 Python 环境，例如 conda 或 venv。
- `mitmdump` 可能位于 Homebrew 的独立 binary 环境，例如 `/opt/homebrew/bin/mitmdump`。

## 现象

执行 `deep-ai-analysis proxy` 后，代理先打印启动信息，随后退出：

```text
Proxy listening on http://127.0.0.1:7788
Recording domains : mcli.sankuai.com
Log directory     : /Users/liji05/.deep-ai-analysis/raw-req-resp

error in script .../deep_ai_analysis/addons/recorder.py
ModuleNotFoundError: No module named 'deep_ai_analysis'
```

## 根因

当前 `proxy` 命令通过 subprocess 调用外部 `mitmdump`：

```python
subprocess.run(["mitmdump", "-s", ".../recorder.py"], env=env)
```

`mitmdump -s recorder.py` 会在 mitmproxy 自己的 Python 环境里加载 addon 文件。原先 `recorder.py` 顶层依赖：

```python
from deep_ai_analysis.config import RECORD_DOMAINS
```

当 `mitmdump` 来自 Homebrew 或其他独立安装方式时，它的 Python 环境里没有安装 `deep_ai_analysis` 包，因此 addon 加载失败。

## 影响范围

使用 `install.sh` 的用户较容易遇到该问题，尤其是：

- `deep-ai-analysis` 安装在 conda/venv 环境。
- `mitmdump` 来自 Homebrew 或 mitmproxy 官方 binary。
- `proxy` 使用外部 `mitmdump` 加载本项目的 addon 文件。

如果 `deep-ai-analysis` 和 `mitmdump` 恰好安装在同一个 Python 环境中，则该问题可能不会复现。

## 修复方案

保持现有外部 `mitmdump` 启动方式不变，但让 addon 在 mitmproxy 环境里自包含：

1. `proxy.py` 从 `deep_ai_analysis.config.RECORD_DOMAINS` 读取配置。
2. 启动 `mitmdump` 时把域名列表写入 `DAA_RECORD_DOMAINS` 环境变量。
3. `recorder.py` 不再 import `deep_ai_analysis.config`，改为从 `DAA_RECORD_DOMAINS` 读取域名。
4. `DAA_RECORD_DOMAINS` 缺失时使用内置默认值 `["mcli.sankuai.com"]`，保证 addon 仍可被裸加载。

## 验证

新增回归测试覆盖两点：

- `recorder.py` 在禁止 import `deep_ai_analysis` 的隔离环境中可以成功加载。
- `proxy` 调用外部 `mitmdump` 时会传入 `DAA_RECORD_DOMAINS`。

建议验证命令：

```bash
python -m unittest -v tests.test_proxy_recorder_isolation
deep-ai-analysis proxy --port 7799
```

第二条命令只需确认启动阶段不再出现 `ModuleNotFoundError: No module named 'deep_ai_analysis'`。
