## Context

`claude-log.html` 中 assistant 条目的 `message.id` 存储在 `e.message.id`，在 `renderDetail(e)` 的「Message 元数据」section 中已渲染。

`req-resp.html` 已有搜索框（`id="searchBox"`），`renderList()` 读取其值过滤列表。

## Goals / Non-Goals

**Goals:**
- `claude-log.html`：`message.id` 值旁添加小图标/链接，`href="req-resp.html?q=<message.id>"`，`target="_blank"`
- `req-resp.html`：初始化时读取 `new URLSearchParams(location.search).get('q')`，若有值则填入搜索框，加载记录后触发 `renderList()`

**Non-Goals:**
- 不自动加载对应 session/date（用户需手动选择）
- 不做双向跳转（req-resp → claude-log）

## Decisions

### URL query 参数传递搜索词

`req-resp.html?q=msg_bdrk_xxx` 是最简单的跨页面传参方式，无需后端、无需 localStorage。

**Why**: 无状态，URL 可分享，实现最小。

### 在记录加载完成后再触发搜索

`req-resp.html` 的流程是：init() → onSessionChange() → loadRecords() → renderList()。URL 参数在 `init()` 时读入 searchBox，在 `loadRecords()` 完成后 `renderList()` 自然读取 searchBox 的值过滤，无需额外处理。
