## Context

`deep-ai-analysis proxy` 已能拦截 HTTPS 流量，但用户还需手动设置两个环境变量才能让基于 Node.js 的 `mc` CLI 走代理：
- `HTTPS_PROXY`：让 Node.js http/https 模块通过代理
- `NODE_EXTRA_CA_CERTS`：让 Node.js 信任 mitmproxy 的自签 CA，不报 `CERT_UNTRUSTED`

`start-mc` 子命令封装这两个步骤，让用户一条命令完成"启动 mc 并走代理"。

## Goals / Non-Goals

**Goals:**
- 提供 `deep-ai-analysis start-mc` 子命令，注入环境变量后执行 `mc --code`
- `--port` 选项与 `proxy` 子命令保持一致（默认 7788），便于两者配合使用
- `mc` 进程继承当前终端的 stdin/stdout/stderr（交互式透传）
- `mc` 不在 PATH 时给出友好错误
- CA 证书文件不存在时给出警告但仍继续（用户可能尚未启动过 proxy）

**Non-Goals:**
- 不自动启动 `proxy` 子命令（两者独立运行，用户自行在另一终端启动）
- 不修改系统级或 shell 级环境变量（仅对子进程生效）
- 不传递 `mc` 的其他参数（固定执行 `mc --code`）

## Decisions

### 决策 1：使用 `subprocess.execvpe` / `os.execvpe` 还是 `subprocess.run`

**选择**: `subprocess.run` with `env=merged_env`，继承父进程环境并叠加两个变量

**理由**:
- `os.execvpe` 会替换当前进程，导致 click 的清理逻辑无法执行；Python 进程直接被 `mc` 取代，错误处理困难
- `subprocess.run` 保留 Python 进程，可捕获 `FileNotFoundError`（mc 不存在）并给出友好提示
- 通过 `stdin=None, stdout=None, stderr=None`（默认继承）实现完全透传，交互式终端体验无差异

**环境变量合并**:
```python
import os
env = os.environ.copy()
env["HTTPS_PROXY"] = f"http://127.0.0.1:{port}"
env["NODE_EXTRA_CA_CERTS"] = str(Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem")
subprocess.run(["mc", "--code"], env=env)
```

### 决策 2：CA 证书路径硬编码为 `~/.mitmproxy/mitmproxy-ca-cert.pem`

**选择**: 固定使用 mitmproxy 默认 CA 证书路径，不提供 `--cert` 选项

**理由**: 与 `proxy` 子命令保持一致（proxy 子命令启动时打印的也是这个路径），用户心智模型简单。若有自定义需求可后续通过选项扩展。

## Risks / Trade-offs

- **[风险] `mc` 不在 PATH** → 缓解：捕获 `FileNotFoundError`，打印 "mc command not found" 并以非 0 退出
- **[风险] CA 证书不存在** → 缓解：启动前检测文件，不存在时打印警告（`mc` 本身会报 TLS 错误，用户需先运行 `proxy`）；不阻止启动，让用户决定
- **[Trade-off] 固定 `mc --code` 参数** → 简单直接，符合当前唯一使用场景；若需传递更多参数，后续可改为 `--` 透传
