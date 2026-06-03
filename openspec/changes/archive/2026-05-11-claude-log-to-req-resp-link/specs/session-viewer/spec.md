## ADDED Requirements

### Requirement: Claude Log assistant entry link to req-resp viewer
`claude-log.html` 的 assistant 条目明细面板中，SHALL 在 `message.id` 旁展示「在请求日志中查看」链接，点击后在新 tab 打开 `req-resp.html?q=<message.id>`。

#### Scenario: Link visible for assistant entries with message.id
- **WHEN** 右侧明细展示 assistant 条目且 `message.id` 非空
- **THEN** `message.id` 值旁显示外链按钮，href 为 `req-resp.html?q=<message.id>`，target 为 `_blank`

#### Scenario: Link not shown without message.id
- **WHEN** assistant 条目的 `message.id` 为空
- **THEN** 不显示链接

### Requirement: Raw req-resp viewer URL search param
`viewer/req-resp.html` SHALL 在页面加载时读取 URL query 参数 `?q=`，若存在则自动填入搜索框，并在记录加载完成后触发过滤。

#### Scenario: URL param auto-fills search box
- **WHEN** 用户通过 `req-resp.html?q=msg_bdrk_xxx` 打开页面
- **THEN** 搜索框自动填入 `msg_bdrk_xxx`，记录加载完成后列表自动按该值过滤
