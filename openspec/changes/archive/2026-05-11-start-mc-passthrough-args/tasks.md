## 1. 修改 start-mc 命令实现

- [x] 1.1 在 `start_mc` 函数签名上添加 `context_settings={"allow_extra_args": True, "ignore_unknown_options": True}`
- [x] 1.2 添加 `@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)` 参数
- [x] 1.3 将 `subprocess.run(["mc", "--code"], env=env)` 改为 `subprocess.run(["mc", "--code", *extra_args], env=env)`
- [x] 1.4 更新函数签名，添加 `extra_args: tuple` 参数

## 2. 验证

- [x] 2.1 手动验证：`deep-ai-analysis start-mc --help` 不报错，显示正确帮助信息
- [x] 2.2 手动验证：无额外参数时行为与修改前一致（运行 `mc --code`）
