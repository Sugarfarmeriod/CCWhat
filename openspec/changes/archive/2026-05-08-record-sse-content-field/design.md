## Context

SSE 记录写入 JSONL 时，当前结构中 `response.body` 存储所有事件拼接的完整字符串，`sse_events` 存储原始事件列表。两者都存在，但没有一个语义清晰的专用字段直接表达"SSE 完整内容"。新增 `sse_content` 字段，使消费方无需自行拼接即可获取完整文本。

## Goals / Non-Goals

**Goals:**
- 在 SSE JSONL 记录中新增 `sse_content` 顶层字段，值为 `"\n\n".join(sse_events)`
- 保持 `response.body` 字段不变（向后兼容）

**Non-Goals:**
- 不修改普通 HTTP 记录结构
- 不改变 `sse_events` 列表的内容或格式
- 不引入任何新的配置项

## Decisions

### 新增字段而非替换 `response.body`

保留 `response.body` 并新增 `sse_content`，而不是重命名或移除 `response.body`。

**Why**: `response.body` 已在 spec 中定义，修改会破坏已有消费方。增量添加字段是非破坏性变更。

### 字段位置：顶层而非嵌套在 `response` 内

`sse_content` 作为顶层字段与 `sse_events` 并列，而不是放入 `response` dict。

**Why**: `sse_content` 是 SSE 会话维度的聚合结果，与 `sse_events` 同级更符合语义；`response` dict 代表原始 HTTP 响应元数据。

## Risks / Trade-offs

- **日志体积略增**：`sse_content` 与 `response.body` 内容相同，等于重复存储一份拼接文本 → 可接受，SSE 内容本身已在内存中，写入时复用即可，无额外计算
