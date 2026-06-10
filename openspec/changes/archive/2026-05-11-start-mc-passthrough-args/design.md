## Context

`start-mc` 通过 Click 定义，当前固定执行 `subprocess.run(["mc", "--code"], env=env)`。Click 默认会拒绝识别不到的选项，因此用户传入 `--opt1` 会报错。

## Goals / Non-Goals

**Goals:**
- 用户可在 `start-mc` 后附加任意参数，这些参数会被原样拼接到 `mc --code` 之后
- 已有的 `--port` 选项保持不变

**Non-Goals:**
- 不对透传参数做校验或解析
- 不修改 `mc` 本身的行为

## Decisions

**使用 Click 的 `context_settings(allow_extra_args=True, ignore_unknown_options=True)` + `@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)`**

Click 提供了专门用于参数透传的机制：
- `context_settings={"allow_extra_args": True, "ignore_unknown_options": True}` 让 Click 不报错、不解析未知选项
- `@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)` 将所有剩余 token 收集为元组

subprocess 调用改为 `["mc", "--code", *extra_args]`。

## Risks / Trade-offs

- [风险] 用户传入的参数可能与 `mc` 不兼容 → 由 mc 自身报错，不影响本工具
- [权衡] `UNPROCESSED` 类型不做 shell 分词，参数按 CLI 分词规则传入，与 shell 直接执行行为一致

## Migration Plan

无需迁移，现有调用方式 `start-mc` 无参数时行为完全不变。
