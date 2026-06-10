## Why

记录请求和响应时，当前实现会将完整的请求 headers 写入 JSONL 日志文件，包括 `Authorization` header。这会导致 token 等敏感凭证以明文形式存储在本地日志中，存在安全风险。

## What Changes

- 在将请求 headers 写入日志之前，过滤掉 `Authorization` header（大小写不敏感匹配）
- 同样适用于普通 HTTP 请求记录和 SSE 流式请求记录

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `proxy-interceptor`: 修改"Record raw request and response"需求——请求 headers 记录时须排除 `Authorization` header，其余 headers 仍完整保留

## Impact

- `deep_ai_analysis/proxy.py`（或对应的 addon 实现文件）：在构建日志记录的 headers dict 时增加过滤逻辑
- 日志文件格式不变，仅 `request.headers` 字段中不再包含 `Authorization` key
- 无破坏性变更，无 API/CLI 接口变动
