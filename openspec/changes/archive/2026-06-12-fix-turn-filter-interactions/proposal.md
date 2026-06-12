## Why

Turn-first Session 页面已经能按 `Turn 1 / Turn 2` 展示会话，但顶部 `user / assistant / system / ...` 属性筛选点击后，下方 Turn 列表和 Turn detail 几乎没有变化。用户会认为筛选按钮失效，无法用类型筛选快速核对某一轮里的用户消息、助手回复、工具调用和错误证据。

这次 change 修复属性筛选与 Turn-first 展示之间的语义断层：Turn 结构保持稳定，筛选结果必须反映到 Turn 卡片元信息和 Turn detail 内容中。

## What Changes

- `Session` 页顶部属性筛选仍作为 event type filter，不新增 `Turn` 作为同级类型。
- Turn 列表继续保留完整 Turn 结构，避免取消所有类型后整个 session 视图空白。
- Turn 卡片展示筛选后的可见 entry 数、tool 数、error 数，并在有隐藏内容时显示隐藏数量。
- Turn detail 只展示当前筛选允许的用户消息、助手回复、工具调用和错误内容。
- 当前筛选隐藏 Turn 内部分或全部 event 时，Turn detail 显示明确提示。
- 全部类型取消时，Turn 列表仍可见，选中 Turn 的 detail 显示“当前筛选隐藏了该 Turn 的全部事件”之类提示，而不是展示未筛选内容。
- 补充 DOM 回归测试，覆盖点击属性筛选后 Turn detail 确实变化。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 明确 Turn-first Session 页面中 type filter 对 Turn 卡片和 Turn detail 的影响。

## Impact

- 主要影响 `viewer/claude-log.html` 的 Turn 卡片渲染、Turn detail 渲染和 filter 后重渲染行为。
- 需要更新前端静态测试和 DOM 行为测试。
- 不修改后端 API、不修改 task segmentation 算法、不改变 Turn 边界派生规则。
