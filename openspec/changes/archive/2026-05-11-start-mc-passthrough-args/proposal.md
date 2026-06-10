## Why

`start-mc` 目前固定运行 `mc --code`，用户无法向 mc 传递额外参数（如 `--opt1`、`--resume` 等），限制了使用灵活性。

## What Changes

- `start-mc` 子命令支持接收任意额外参数，并将其原样透传给 `mc --code`
- 例如：`deep-ai-analysis start-mc --opt1` 实际执行 `mc --code --opt1`
- 例如：`deep-ai-analysis start-mc --resume /path` 实际执行 `mc --code --resume /path`

## Capabilities

### New Capabilities

- `start-mc-passthrough`: start-mc 子命令的参数透传能力，将用户提供的额外参数附加到 `mc --code` 命令之后

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- 修改 `deep_ai_analysis/commands/start_mc.py`：使用 Click 的 `context_settings` + `allow_extra_args` + `ignore_unknown_options` 收集额外参数，并拼接到 subprocess 调用中
