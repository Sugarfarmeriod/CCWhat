## Context

`deep-ai-analysis proxy` 命令通过 mitmproxy addon 拦截 HTTP/HTTPS 流量，将匹配域名的请求和响应以 JSONL 格式记录到本地日志文件。当前实现将请求的完整 headers dict 序列化写入日志，其中包含 `Authorization` header（携带 Bearer token 等凭证）。这意味着用户的 API token 会以明文形式持久化在本地磁盘上。

## Goals / Non-Goals

**Goals:**
- 在写入日志前，从请求 headers 中过滤掉 `Authorization` header
- 过滤逻辑覆盖普通 HTTP 请求和 SSE 流式请求两条记录路径
- 过滤大小写不敏感（HTTP headers 规范不区分大小写）

**Non-Goals:**
- 不过滤响应 headers（响应头中通常不含凭证）
- 不提供可配置的 header 黑名单（单一硬编码即可满足需求）
- 不对已存在的历史日志做任何处理

## Decisions

### 在构建日志 dict 时过滤，而非修改 flow 对象

在序列化 headers 为 dict 时直接跳过 `Authorization` key，不修改 mitmproxy flow 中的原始 headers。

**Why**: 修改 flow 对象会影响代理转发行为（下游服务收不到 Authorization header），破坏代理的透明性；而我们只需要在记录时隐藏，不影响实际流量。

### 硬编码过滤列表，不做可配置化

将敏感 header 名称以常量 `SENSITIVE_HEADERS = {"authorization"}` 硬编码（小写集合），过滤时做 `.lower()` 比较。

**Why**: 当前场景只有一个明确需求（Authorization），过早抽象为可配置项会增加复杂度而无收益。

## Risks / Trade-offs

- **遗漏其他敏感 headers**（如 `Cookie`, `X-Api-Key`）→ 当前范围仅处理 Authorization，未来可扩展常量集合
- **大小写变体**（如 `AUTHORIZATION`, `authorization`）→ 统一 `.lower()` 比较，已覆盖

## Migration Plan

1. 修改 `proxy.py` 中构建 `request_headers` dict 的代码，增加过滤逻辑
2. 无需数据迁移，历史日志保持不变
3. 无 CLI/API 接口变更，无需通知用户
