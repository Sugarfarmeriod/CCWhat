## Context

当前实现已经把 export 的入口参数放宽到多个 session，但包内仍固定写入 `main-session.jsonl`、单份 `manifest.json` 和单份 `metadata/session.json`。这使得多 session 导出时后写入的 session 覆盖前一个 session 的路径语义，导入端也只能读取单个 `sessionId`。本次设计需要同时解决三个问题：包结构去冲突、import 按包级清单批量导入、旧单 session 包继续可用。

## Goals / Non-Goals

**Goals:**
- 定义一个真正支持多 session 的包级 manifest 和目录结构
- 让 CLI export、Web export、CLI import 在新格式上完全闭环
- 保持单 session 导出体验简单，默认文件名和提示文案对单/多 session 都合理
- 兼容旧格式单 session 包的导入
- 用自动化测试覆盖多 session 与兼容路径

**Non-Goals:**
- 不引入加密、脱敏或权限控制
- 不新增 Web UI 导入入口
- 不做跨版本复杂迁移框架，只处理当前旧单 session 包与新多 session 包两类格式

## Decisions

### Decision 1：引入包级 manifest v2

新格式继续使用 `deep-ai-analysis-export/manifest.json`，但内容升级为包级描述：

- `exportVersion` 变为 `"2.0"`
- `toolVersion`
- `createdAt`
- `sessionCount`
- `sessions`: 数组，每项包含 `sessionId`、`projectDir`、`included`、`counts`

这样 manifest 可以准确表达一个导出包中包含哪些 session，并允许 import 无歧义地逐个写入本地导入目录。

保留旧格式识别逻辑：如果 manifest 里存在顶层 `sessionId`/`projectDir` 且不存在 `sessions` 数组，则按 v1 单 session 包处理。

### Decision 2：目录结构改为按 session 分目录

新包结构统一为：

```text
deep-ai-analysis-export/
├── manifest.json
├── README.md
├── view.command
├── sessions/
│   ├── <session-id>/
│   │   ├── metadata/session.json
│   │   ├── metadata/project.json
│   │   ├── claude-logs/main-session.jsonl
│   │   ├── claude-logs/subagents/*
│   │   └── req-resp/*.jsonl
```

这样每个 session 的日志、子代理日志和 req/resp 都在自己目录下，天然避免冲突，也使 tar.gz 和解压目录的导入逻辑一致。

### Decision 3：单 session 也使用新结构，但 import 同时兼容旧结构

为了避免维护双写导出逻辑，新的 export 无论单 session 还是多 session 都统一输出 v2 结构。import 则支持：
- v2：从 `sessions/<session-id>/...` 读取多个 session
- v1：从旧根目录 `claude-logs/`、`req-resp/` 和顶层 `sessionId` 字段读取单个 session

这样实现最简单，且不会继续产生新的旧格式包。

### Decision 4：默认文件名和交互文案按单/多 session 区分

CLI 和 Web UI 的默认文件名规则：
- 单 session：保留 `export-YYYYMMDD-HHmmss-<短ID>.tar.gz`
- 多 session：使用 `export-YYYYMMDD-HHmmss-<count>-sessions.tar.gz`

CLI 成功提示和 Web UI 导入命令仍只展示一个 import 命令，因为导入动作针对整个包，不针对某一个 session。

### Decision 5：import 采用包级覆盖确认与逐 session 拷贝

import 在读取 manifest 后先计算所有将写入的目标 session。如果其中任意目标已存在且未传 `--force`，则提示一次总确认；确认后按 session 逐个覆盖。这样避免多 session 包在导入过程中半途停住并留下部分覆盖状态。

### Decision 6：tar 导入使用通用读取模式并校验解压路径

import 读取压缩包时使用 `tarfile.open(..., "r:*")` 兼容 gzip 及标准 tar，并在解压前校验成员路径必须落在临时目录中，避免路径穿越。

## Risks / Trade-offs

- 包结构升级后，手工查看路径与旧版本不同 → 通过 README 和 import 兼容降低迁移成本
- 多 session 导入时一次确认会覆盖多个目标 → 在提示中明确列出数量与目标根目录
- 单 session 也升级到 v2 会改变老用户对包内容路径的预期 → 但 CLI import/README 是主路径，且结构一致性优于继续维护双格式导出
- Web UI 支持多选 session 导出 → 需要保持默认只选当前 session，避免打开弹窗后误导出全部历史记录；用户显式多选时再生成多 session 包

## Migration Plan

1. 新增 v2 导出结构与 manifest 生成逻辑。
2. 更新 import 逻辑，先兼容 v2，再回退兼容 v1。
3. 更新 CLI/Web 默认文件名与提示文案，Web UI 导出弹窗支持多选 session。
4. 新增自动化测试覆盖 v2 单/多 session 导出、v2 导入、v1 导入兼容。
5. 若实现中发现规格需要微调，再回写对应 specs。

## Open Questions

- 是否需要在 manifest 中记录包级 included 汇总字段：当前不需要，逐 session 信息足够且避免汇总歧义。
