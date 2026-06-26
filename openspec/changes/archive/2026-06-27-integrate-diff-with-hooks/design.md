## Context

Change 7 已完成：
- `CCWhatIndex` 提供隔离的 git staging area
- `TaskStaging.record_step(tool_name, file_path)` 可记录单步 diff
- `diff.patch` 在 finish 时生成，带 step 注释头

当前缺失：触发 `record_step()` 的机制。

## Goals / Non-Goals

**Goals:**
- 实现 `ccwhat` 脚手架脚本（设置 `CCWHAT_ENABLED=1`）
- 实现 PostToolUse Hook 捕获 Write/Edit 工具调用
- 实现 `/step` controller endpoint 接收 hook 通知
- 实现 Hook 条件激活（环境变量控制）
- 验证完整流程：ccwhat start → /ccwhat:start → Write 文件 → diff.patch 包含该步骤

**Non-Goals:**
- 不修改 task_trace.json 生成逻辑
- 不实现 Bash 命令的 diff 记录（只记录文件修改）
- 不实现 GUI 或 Web 界面

## Decisions

### Decision 1: 环境变量条件激活

**选择**: `CCWHAT_ENABLED=1` 控制 hook 激活。

**理由**:
- 简单，进程隔离
- 用户正常用 `claude` → hook 不激活（零开销）
- 用户用 `ccwhat start` → hook 激活，记录 diff

**流程**:
```bash
# 正常模式
claude                    # CCWHAT_ENABLED 未设置 → hook 直接 exit 0

# 追踪模式
ccwhat start              # CCWHAT_ENABLED=1 → hook 激活，记录 diff
```

### Decision 2: Hook Payload 处理

**选择**: Hook 从 stdin 读取 payload，提取 `tool_name` 和 `tool_input.file_path`。

**Claude Code PostToolUse Payload**:
```json
{
  "tool_name": "Write",
  "tool_input": {"file_path": "/path/to/file.py", "content": "..."},
  "tool_result": {...}
}
```

**Hook 逻辑**:
```bash
if [[ "$CCWHAT_ENABLED" != "1" ]]; then
  exit 0
fi

tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$tool_name" =~ ^(Write|Edit|MultiEdit)$ ]]; then
  curl -X POST "http://localhost:$CCWHAT_RUNTIME_CONTROL_PORT/step" \
    -d "{\"tool_name\":\"$tool_name\",\"file_path\":\"$file_path\"}"
fi
```

### Decision 3: Controller /step Endpoint

**选择**: POST `/step`，接收 `tool_name` 和 `file_path`，调用 `staging.record_step()`。

**理由**:
- 简单，复用现有 controller 架构
- 无需认证（port 已隔离）

### Decision 4: ccwhat 脚手架脚本位置

**选择**: 作为 Python CLI 命令 `ccwhat start`，而非独立 shell 脚本。

**理由**:
- 与现有 `ccwhat -- claude` 架构一致
- 易于维护，统一入口

**实现**:
```python
# ccwhat/cli.py 新增子命令
@click.command()
def start():
    """Start CCWhat tracking session."""
    os.environ["CCWHAT_ENABLED"] = "1"
    # ... 启动 controller
    subprocess.run(["claude"])
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Hook 延迟影响用户体验 | Hook 只发 HTTP 请求，不等待响应（fire-and-forget） |
| 并发工具调用 | 顺序处理，HTTP 请求依次到达 |
| 环境变量未传递 | ccwhat 脚本显式设置并导出 |

## Migration Plan

- 无破坏性变更
- 现有功能不变，新增追踪模式
- 用户可选择使用 `claude` 或 `ccwhat start`

## Open Questions

1. **Q**: Hook 是否需要等待 controller 响应？
   **A**: 不需要，fire-and-forget 避免延迟。

2. **Q**: 是否记录 Bash 命令导致的文件变更？
   **A**: 当前不记录，只记录显式 Write/Edit。
