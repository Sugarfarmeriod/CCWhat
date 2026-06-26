## 1. ccwhat CLI start 命令

- [x] 1.1 新增 `ccwhat/commands/start.py` 模块
- [x] 1.2 实现 `start` 命令：设置 `CCWHAT_ENABLED=1`
- [x] 1.3 实现 `start` 命令：启动 runtime controller
- [x] 1.4 实现 `start` 命令：启动 Claude Code 并传递环境变量
- [x] 1.5 在 `ccwhat/cli.py` 注册 `start` 子命令

## 2. PostToolUse Hook 脚本

- [x] 2.1 创建 `.claude/hooks/ccwhat-diff-hook.sh` 脚本
- [x] 2.2 实现条件激活检查：`CCWHAT_ENABLED=1`
- [x] 2.3 实现 payload 解析：`tool_name`、`tool_input.file_path`
- [x] 2.4 实现 controller 通知：POST `/step`
- [x] 2.5 实现工具过滤：只处理 Write/Edit/MultiEdit

## 3. Controller /step Endpoint

- [x] 3.1 修改 `controller.py`：新增 POST `/step` 路由
- [x] 3.2 实现 step handler：提取 `tool_name` 和 `file_path`
- [x] 3.3 实现 step handler：调用 `staging.record_step()`
- [x] 3.4 实现错误处理：无 active task、参数缺失等

## 4. Hook 配置注册

- [x] 4.1 修改 `claude_integration.py`：生成 `.claude/settings.json` 的 PostToolUse 配置
- [x] 4.2 确保 hook 配置正确引用 `ccwhat-diff-hook.sh`
- [x] 4.3 确保 matcher 正确匹配 Write/Edit/MultiEdit

## 5. 集成测试

- [x] 5.1 测试 `ccwhat start` 设置环境变量
- [x] 5.2 测试 Hook 条件激活（CCWHAT_ENABLED）
- [x] 5.3 测试 `/step` endpoint 接收通知
- [x] 5.4 测试完整流程：start → Write → diff.patch 包含步骤
- [x] 5.5 测试主 git 工作区不受污染
- [x] 5.6 运行全部测试确保无回归

## 6. 文档与审查

- [x] 6.1 更新 CLI 帮助文档
- [x] 6.2 代码审查：错误处理完善
- [x] 6.3 代码审查：资源清理
