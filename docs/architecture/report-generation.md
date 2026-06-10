# 报告生成模块架构

## 概述

报告生成由两个目录协作完成，分工明确：

- `ccwhat/analyzers/` — **执行层**：解决"用哪个 Agent CLI 执行分析、如何解析它的输出"
- `ccwhat/session_report/` — **业务层**：解决"如何把 session 数据变成有价值的分析报告"

两者通过 `session_report/pipeline.py` 连接。

---

## 目录结构

### `ccwhat/analyzers/`

```
analyzers/
├── base.py       # AnalyzerSpec 数据类：定义一个 analyzer 的命令、输出模式、解析器
├── registry.py   # 注册表：维护 claude/codex/opencode 三个 analyzer 的配置和别名
├── codex.py      # Codex 专属：解析 Codex CLI 的 JSONL 输出
└── opencode.py   # OpenCode 专属：解析 OpenCode CLI 的 JSONL 输出
```

这一层只关心：**用哪条命令调用 CLI、输出格式是什么、怎么从输出里提取文本**。不涉及 prompt 内容和报告结构。

### `ccwhat/session_report/`

```
session_report/
├── model.py       # 数据结构：ReportSession、ReportEvent、ReportTurn 等领域模型
├── normalize.py   # 归一化：把 Claude/Codex/OpenCode 的原始 session 数据统一成 ReportSession
├── core.py        # 报告引擎：从 ReportSession 计算阶段、工具耗时、findings，生成 yuanxi HTML
├── pipeline.py    # 编排层：把 normalize → core → analyzer → HTML 串起来，对外暴露两个入口
└── __init__.py    # 导出 build_html_session_report / build_generic_html_report
```

---

## 完整数据流

```
原始 session JSON（来自 Claude/Codex/OpenCode 日志）
        │
        ▼  normalize.py
   ReportSession（统一数据模型）
        │
        ▼  core.py
   ReportData（阶段 / 工具耗时 / findings / diagnosis_context）
        │
        ├─── diagnosis_context（结构化摘要文本）
        │           │
        │           ▼  pipeline.py 拼成 prompt
        │     analyzers/registry.py 查找对应 CLI
        │           │
        │           ▼  analyzer.py run_mc_analysis()
        │     调用 claude / codex / opencode CLI 执行分析
        │           │
        │           ▼  codex.py / opencode.py 解析输出
        │     返回 Markdown 分析文本
        │
        ▼  core.py render_html_report()
           或 pipeline.py _render_generic_html()
       最终 HTML 报告
```

---

## 两种报告模式

`pipeline.py` 对外暴露两个函数，对应前端的两种分析模式：

| 模式 | 函数 | Prompt 文件 | 输出 |
|------|------|-------------|------|
| `yuanxi` | `build_html_session_report()` | `assets/session-report/diagnosis_prompt.md` | 元析风格 HTML，含阶段时间线、工具耗时图表 |
| `generic` | `build_generic_html_report()` | `assets/session-report/generic_prompt.md` | 通用 HTML，含 Mermaid 流程图的 Markdown 分析报告 |

两种模式的共同流程：

1. `normalize_session_for_report()` 把原始 session 归一化
2. `build_report_data()` 计算结构化数据（阶段、工具、findings）
3. 把 `diagnosis_context` 填入对应 prompt 模板
4. 调用 `run_mc_analysis()` 执行 LLM 分析
5. LLM 失败时走本地 fallback（`_fallback_diagnosis_markdown` / `_fallback_generic_markdown`）
6. 把 LLM 输出渲染进 HTML 模板

---

## Analyzer 注册表

`registry.py` 维护三个内置 analyzer，每个 analyzer 声明：

- `default_command`：调用 CLI 的默认命令
- `output_mode`：`stdout` / `jsonl_text` / `last_message_file`
- `parse_output`：从 CLI 输出提取最终文本的解析函数

```
claude   → ["claude", "-p", "-"]                         stdout 直接读取
opencode → ["opencode", "run", "--format", "json"]       JSONL 解析
codex    → ["codex", "exec", "--json", "--ephemeral", …] JSONL 解析（experimental）
         → ["codex", "exec", "--output-last-message", …] 文件读取（fallback candidate）
```

---

## Analyzer 与 Session Report 的边界

| 关注点 | 归属 |
|--------|------|
| 哪个 Agent CLI 可用 | `analyzers/registry.py` |
| 如何调用 CLI、解析输出 | `analyzers/` + `analyzer.py` |
| session 数据归一化 | `session_report/normalize.py` |
| 阶段/耗时/findings 计算 | `session_report/core.py` |
| Prompt 构建与 HTML 渲染 | `session_report/pipeline.py` |
| 对外 API 入口 | `viewer/server.py` → `pipeline.py` |
