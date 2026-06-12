## Why

`turn-view-mode-projection` 已经提供了默认视图 / 调试视图的数据投影，但当前 Session Trace 树仍然主要按完整 Turn 列表渲染。用户在日常阅读 session 时，仍会被 `permission-mode`、`last-prompt`、`PostToolUse`、`file-history-snapshot`、`queue-operation`、system/context 注入等内部事件干扰。

这个 change 的目标是把已经存在的 projection 正式接入左侧 Trace 树 UI：

- 默认视图用于阅读主执行链路，只展示 primary Step。
- 调试视图用于完整可观测，展示全部 Turn 并保持原始时序。
- 原始类型筛选从主入口降级为调试筛选。
- 右侧 Detail 暂不重构，但切换视图不能让页面空白或丢失已选节点。

## What Changes

- 新增 Session Trace 视图模式状态：`default` / `debug`。
- 在 Session 顶部提供清晰的双视图切换控件：`默认视图`、`调试视图`。
- Trace 树渲染改为消费 `buildTurnViewProjection(mode, source)` 的结果，而不是直接渲染完整 Turn 列表。
- 默认视图隐藏普通 internal Turn，只显示连续编号的 `Step N`。
- 调试视图显示完整 `Turn N` 时间线，并保持原始顺序。
- 默认视图下隐藏底层类型筛选，调试视图下保留类型筛选作为高级调试筛选。
- 切换视图时保持 Task / Conversation 层级不变，并尽量保持当前选中节点。
- 如果当前选中的内部 Turn 在默认视图不可见，页面应提示该节点已隐藏，并定位到最近可见的 Conversation 或 Task。

## Non-Goals

- 不重新设计右侧 Detail 的证据完整性；那是后续 `turn-detail-complete-evidence` change。
- 不做 tool_use + tool_result 聚合。
- 不做 Task 编辑器、拖拽、手动划分或 overlay 持久化。
- 不修改 `classifyTurnForDefaultView` 的核心分类语义，除非修复接入时发现的明显 bug。
- 不修改后端 API。
- 不改变 Task / Conversation / Turn 的底层边界和锚点。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: Session Trace 树支持默认视图 / 调试视图双模式渲染，并将底层类型筛选降级为调试视图下的高级筛选。

## Impact

- 主要影响 `viewer/claude-log.html` 的顶部控制区、Trace 树渲染、类型筛选可见性和选择状态处理。
- 需要更新前端静态测试和 DOM 行为测试，覆盖默认/调试视图切换、projection 消费、筛选显示规则、选择状态回退和不空白。
- 不涉及后端数据结构和 adapter。
