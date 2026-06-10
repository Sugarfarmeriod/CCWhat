## Context

当前 export 功能（`exporter.py` + `commands/export.py`）将日志文件打包为 tar.gz，但结构松散、无元数据、接收方无标准入口。本次重构分两个部分：重设计打包格式、新增 import 命令。现有 Web UI 导出弹窗也需配套升级。

## Goals / Non-Goals

**Goals:**
- 压缩包内部结构固定，带 manifest.json，可机器读取
- import 命令一步完成解压、导入、可选打开浏览器
- 导出默认路径改为 `~/Downloads/deep-ai-analysis-exports/`，开箱即用
- Web UI 导出弹窗增加内容勾选和成功后的操作引导

**Non-Goals:**
- 不做加密或脱敏（后续迭代）
- 不支持跨版本 manifest 升级迁移（当前 exportVersion 固定为 "1.0"）
- 不做 Web UI 的导入入口（只做 CLI import）

## Decisions

### Decision 1：manifest.json 作为包的元数据契约

manifest.json 放在压缩包根目录，内容：

```json
{
  "exportVersion": "1.0",
  "toolVersion": "<deep-ai-analysis 版本>",
  "sessionId": "<uuid>",
  "projectDir": "<项目目录名>",
  "createdAt": "<ISO 8601>",
  "included": {
    "claudeLogs": true,
    "subagentLogs": true,
    "reqResp": true
  },
  "counts": {
    "subagentFiles": 3,
    "reqRespFiles": 5
  }
}
```

之所以不用 YAML/TOML：JSON 无需额外依赖，Python 标准库直接解析，接收方脚本也容易处理。

### Decision 2：固定的包内目录结构

```
deep-ai-analysis-export/
├── manifest.json
├── README.md
├── view.command          # macOS 双击脚本
├── claude-logs/
│   ├── main-session.jsonl
│   └── subagents/
│       └── *.jsonl
├── req-resp/
│   └── *.jsonl
└── metadata/
    ├── session.json
    └── project.json
```

根目录名固定为 `deep-ai-analysis-export/`，而非 session ID，方便接收方识别。

### Decision 3：import 命令写入 ~/.deep-ai-analysis/imports/<session-id>/

不复用原始 `~/.claude/projects/` 路径，原因：
- 接收方可能没有同名项目目录
- 导入数据应和本机数据隔离，避免污染
- imports/ 目录专门存放外来包，便于清理

import 执行流程：
1. 读取 manifest.json，校验 exportVersion
2. 解压到 `~/.deep-ai-analysis/imports/<session-id>/`
3. 如有 `--open`，调用已有 web-server 逻辑打开浏览器（或自动启动）

### Decision 4：view.command 内容

```bash
#!/bin/bash
cd "$(dirname "$0")"
deep-ai-analysis import . --open
```

仅在 macOS 下有效（`.command` 扩展名双击执行）。Windows/Linux 不生成，或后续补充 `.sh`。

### Decision 5：Web UI 导出弹窗默认导出路径

前端通过 File System Access API 选择目录时，默认提示 `~/Downloads/deep-ai-analysis-exports/`，但实际选择权在浏览器/用户，不强制。CLI export 则直接写入该目录（不弹选择框）。

## Risks / Trade-offs

- **File System Access API 兼容性** → 已有 fallback（`<a download>`），影响可控
- **import 命令依赖工具已安装** → view.command 里的 `deep-ai-analysis` 必须在 PATH 中，README 需说明
- **manifest.json exportVersion 硬编码为 "1.0"** → 后续格式变化需加版本判断逻辑，现在先欠债

## Migration Plan

- 旧格式压缩包（无 manifest.json）不支持 import，import 命令读不到 manifest 时报错并提示用户手动解压
- exporter.py 的 `build_tar_gz_bytes()` 接口签名不变，内部实现替换，CLI 和 Web 调用方无感
