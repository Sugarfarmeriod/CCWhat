# Task Segmentation — 第一版规则策略说明

## 概述

`ccwhat/task_segments/` 模块将 AI Coding Agent 的长 session 日志切分为可复盘、可测试的任务片段（Task Segments），使用**纯规则 pipeline**，不依赖 LLM 判断边界。

---

## 调用方式

```python
from ccwhat.task_segments import segment_session

result = segment_session(session_dict)  # session_dict 来自 ClaudeAdapter.load_session()
for task in result.tasks:
    print(task.task_id, task.title, task.status)   # status 永远是 "unevaluated"
```

HTTP API：

```http
POST /api/task-segments
Content-Type: application/json

{"sessionId": "<session-id>"}
```

---

## 模块结构

```
ccwhat/task_segments/
  models.py      — 数据类：NormalizedEvent, EvidenceBundle, TaskSegment, ...
  events.py      — 将 raw JSONL 归一化为 NormalizedEvent 列表
  rules.py       — 规则加载器、意图分类、延续否决、Todo 抽取
  evidence.py    — 证据抽取：文件、命令、错误、final claim
  bm25.py        — 本地内存 BM25，用于 Todo/证据关联
  overlap.py     — 加权 Jaccard overlap，用于文件主题变化检测
  segmenter.py   — 核心状态机，整合上述模块
```

规则词典路径：`ccwhat/assets/task_segment_rules.json`

---

## 边界评分逻辑

每个候选边界（来自用户消息）计算一个综合分数：

| 信号 | 分值 |
|------|------|
| 命中新任务 marker（帮我/实现/修复/add/fix...） | +2.0 |
| 命中强边界词（另外/还有一件事...） | +2.0 |
| 用户 Todo 列表 | +1.5 |
| 前一任务已有 final claim | +1.0 |
| 前瞻窗口有 edit/write evidence（权重≥3） | +1.5 |
| 前瞻窗口有测试命令 | +1.0 |
| 文件 overlap 低（<0.25）且 module overlap 低（<0.5）且有 edit 证据 | +2.0 |
| **抑制：** 命中延续 marker（还是/继续/没通过...） | 否决（score→0） |
| **抑制：** 前瞻窗口只有 Read/Grep，无 edit | -1.0 |
| **抑制：** 文件 overlap 高（>0.5） | -1.5 |

**默认阈值**：`score >= 3.0` → 开新 Task。

可通过修改 `task_segment_rules.json` 中的 `thresholds.split_score` 调整。

---

## 调参旋钮

所有旋钮都在 `ccwhat/assets/task_segment_rules.json`：

| 字段 | 作用 |
|------|------|
| `thresholds.split_score` | 边界分数阈值，越高越保守（默认 3.0） |
| `thresholds.file_overlap_low` | 文件 overlap 低阈值（默认 0.25） |
| `thresholds.module_overlap_low` | 模块 overlap 低阈值（默认 0.5） |
| `new_task_markers.zh_phrases` | 中文新任务关键词列表 |
| `continuation_markers.zh_phrases` | 中文延续/反馈关键词列表 |
| `file_weights.edit_weight` | 编辑操作文件权重（默认 3.0） |
| `file_weights.downgrade_patterns` | 通用文件降权系数（README、lock 等） |

---

## 设计原则

- **Precision > Recall**：宁可少切（保守），也不把一个连续任务切碎
- **第一版 status 永远是 `unevaluated`**：不做成功/失败判断
- **Subagent 归属主任务**：subagent 不单独开新 Task
- **工具 Todo 不切分**：只有用户目标型 Todo 才能产生候选 Task
- **Final claim 关闭 Task**：后续反馈消息 reopen，而非开新 Task

---

## 已知局限

1. 隐含的新需求（用户没有明确说"新任务"）可能漏切
2. 前后端同时修改但属同一任务的场景可能误切（通过 module overlap 缓解）
3. 中文分词依赖 2-gram，罕见词组可能误判
4. 对于频繁跨主题来回的 session，会标记 `is_ambiguous: true`，不强行细切

---

## 调试

API 返回 `debugBoundaries` 数组，每项包含：

```json
{
  "eventId": "main:32",
  "score": 4.5,
  "shouldSplit": true,
  "reasons": ["user_new_task:feature:+2.0", "window_edit_weight:3.0:+1.5", ...]
}
```

通过 reasons 可以快速定位是哪个信号触发了切分，方便补充规则。
