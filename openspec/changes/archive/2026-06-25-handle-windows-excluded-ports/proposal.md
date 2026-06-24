## Why

Windows 会把部分 TCP 端口放入 excluded port range。ccwhat 当前只检查端口是否有进程监听，无法识别“没有 listener 但不可 `bind()`”的端口，导致默认 `7788` 或 `7789` 被系统保留时，用户只能看到泛化且误导的 mitmproxy/port free 提示。

这个问题已经能在 Windows 上用最小 socket bind 稳定复现，并且影响 `ccwhat -- <cli>`、`ccwhat proxy`、`ccwhat discover` 以及 viewer 端口启动路径。

## What Changes

- 在代理和 viewer 启动前增加端口可绑定性判断，区分“被其他进程监听”和“系统拒绝绑定”。
- 当 Windows excluded port range 或其他权限原因导致 `bind()` 失败时，输出更准确的错误信息，并提示用户使用 `--port` 或 `--web-port` 换端口。
- 保留现有默认端口和已有“端口被非 ccwhat 进程占用”的行为，不做端口自动分配。
- 为不可绑定端口场景补充单元测试，覆盖 managed proxy、discovery proxy 和 viewer 入口的关键提示。

## Capabilities

### New Capabilities
- `port-bindability-diagnostics`: 定义 CLI 在端口未被监听但不可绑定时应给出的诊断行为。

### Modified Capabilities
- 无。现有代理和 viewer 能力保持不变，本 change 增加横切的端口诊断能力。

## Impact

- 影响 `ccwhat/commands/run.py`、`ccwhat/commands/proxy.py`、`ccwhat/commands/discover.py` 和 viewer 启动相关代码。
- 影响测试：`tests/test_run_command.py` 以及必要的新测试覆盖。
- 不引入新依赖，不改变 CLI 参数，不改变默认端口。
