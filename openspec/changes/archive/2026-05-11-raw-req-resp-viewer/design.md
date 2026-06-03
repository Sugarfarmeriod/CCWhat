## Context

目录结构：
```
<req-resp-dir>/
  <sessionId>/
    YYYY-MM-DD.jsonl   # 每行一条原始记录
```

每条记录字段：`timestamp`、`domain`、`method`、`url`、`request`（headers+body）、`response`（status+headers+body）、`is_sse`、`sse_events`

## Goals / Non-Goals

**Goals:**
- 后端 `/api/req-resp/sessions`：扫描 req-resp-dir 子目录，返回 session ID 列表及每个 session 下的日期列表
- 后端 `/api/req-resp/records?session=&date=`：读取指定文件，返回全部记录
- 前端：session+日期选择 → 加载记录列表 → 点击查看明细

**Non-Goals:**
- 不做分页（文件内条数在合理范围内）
- 不修改现有接口

## Decisions

### 后端复用 `logs_dir` 参数（即 req-resp-dir）

`run_server()` 已有 `logs_dir` 参数，新接口直接使用此目录扫描 sessionId 子目录。

**Why**: 避免引入新参数，`logs_dir` 就是 `req-resp-dir`，语义一致。

### 列表摘要字段

时间（本地格式）、URL path、is_sse badge、HTTP 状态码。

### 右侧明细分区展示

- 基本信息（timestamp、url、session）
- 请求 headers（折叠）
- 请求 body（折叠，JSON 格式化）
- 响应 headers（折叠）
- SSE Events 列表 / 响应 body（默认展开）
