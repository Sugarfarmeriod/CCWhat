## 1. claude-log.html

- [x] 1.1 在 `renderDetail(e)` 的「Message 元数据」section 中，`message.id` 行的值旁新增外链按钮，`href="req-resp.html?q=${msg.id}"`，`target="_blank"`，仅当 `msg.id` 非空时显示

## 2. req-resp.html

- [x] 2.1 在 `init()` 函数开头读取 `new URLSearchParams(location.search).get('q')`，若非空则填入 `searchBox` 的 `value`

## 3. 验证

- [x] 3.1 在 `claude-log.html` 点击 assistant 条目的跳转链接，确认新 tab 打开 `req-resp.html` 且搜索框已填入 `message.id`，选择 session 和日期后列表自动过滤
