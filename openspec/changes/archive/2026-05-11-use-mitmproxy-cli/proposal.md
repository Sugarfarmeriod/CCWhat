## Why

当前 `proxy` 子命令通过 Python API（`DumpMaster`）启动 mitmproxy，要求 `mitmproxy` 作为 Python 包安装在同一环境中。这导致：
1. 安装时需要 pip 安装较大的 mitmproxy 包（含所有 Python 依赖）
2. 与 brew 安装的独立 mitmproxy CLI 不兼容
3. pyproject.toml 的 `mitmproxy>=10.0` 依赖增加 wheel 安装复杂度

改用 `mitmdump -s <addon.py>` 命令行方式启动，mitmproxy 作为独立 CLI 工具通过 brew 安装，与 Python 包解耦。

## What Changes

- `proxy` 子命令改为通过 `subprocess` 调用 `mitmdump` 命令，以 `-s` 参数加载 `recorder.py` addon
- `recorder.py` 保持不变（`mitmdump -s` 同样支持 mitmproxy addon API）
- `pyproject.toml` 移除 `mitmproxy>=10.0` 依赖
- `install.sh` 添加 `brew install mitmproxy` 步骤
- README 更新安装说明

## Capabilities

### New Capabilities

- `mitmproxy-cli-launch`: `proxy` 子命令通过 `mitmdump` CLI 启动代理，而非 Python API

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- 修改 `deep_ai_analysis/commands/proxy.py`：移除 asyncio/DumpMaster，改用 `subprocess.run(["mitmdump", ...])`
- 修改 `pyproject.toml`：移除 `mitmproxy>=10.0` 依赖
- 修改 `install.sh`：添加 `brew install mitmproxy`
- 修改 `README.md`：更新环境要求和安装说明
