## Context

`proxy` 和 `web-server` 是两个独立命令，目前各自硬编码了 `./logs` 作为默认路径。两者实际上操作的是同一批日志文件（`proxy` 写入，`web-server` 读取），共享默认路径可以减少用户配置负担。

## Goals / Non-Goals

**Goals:**
- 将默认日志目录统一为 `~/.deep-ai-analysis/raw-req-resp`
- 两个命令共享同一常量，避免不一致
- 目录不存在时自动创建（`proxy` 命令已有此逻辑）

**Non-Goals:**
- 不引入配置文件（`.deepaianalysisrc` 等）
- 不改变 `--output` / `--logs-dir` 选项的名称或行为

## Decisions

### 在 `config.py` 定义常量

```python
DEFAULT_RAW_LOG_DIR: Path = Path.home() / ".deep-ai-analysis" / "raw-req-resp"
```

**Why**: 两处命令共享，修改一处即可，避免遗漏。`Path.home()` 在运行时解析，不受安装路径影响。

### click 选项 default 用字符串而非 Path 对象

click 的 `default=` 在帮助文本中显示，用 `str(DEFAULT_RAW_LOG_DIR)` 使 `--help` 输出可读（显示实际路径而非 `PosixPath(...)`）。

## Risks / Trade-offs

- **已有 `./logs` 数据**：用户升级后默认路径变更，旧日志不会自动迁移 → 文档说明即可，影响可接受
