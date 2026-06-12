## Why

当前 Session Trace 将 Claude / Codex / OpenCode 的内部事件全部作为 Turn 展示，导致默认浏览噪声过大。用户想快速理解主执行链路时，会被 `permission-mode`、`last-prompt`、`PostToolUse`、`file-history-snapshot`、`queue-operation`、system/context 注入等内部事件干扰。

但这些内部事件又不能简单折叠到底部，因为它们的发生位置本身就是可观测证据。调试时必须保持完整时序。

本 change 引入 Turn View Mode 的数据投影层：

- 默认视图：展示主执行 Step。
- 调试视图：展示完整 Turn 时间线。

注意：本 change 只做数据投影和分类，不改 UI 主交互。后续 change 再把顶部切换和 Trace 树渲染接入这个投影。

## What Changes

- 新增 Trace view mode 概念：`default` 和 `debug`。
- 基于完整 minimal Turn 生成 view projection。
- 默认视图 projection 只包含 primary Step。
- 调试视图 projection 包含全部 minimal Turn。
- 默认视图中 `thinking / reasoning` 是 primary Step，完整展示，和 user/tool/result/text 平级。
- 普通 system/context/hook/snapshot/queue/permission-mode 等内部事件默认隐藏，但在调试视图保留完整顺序。
- 异常或影响执行的内部事件可升级为 primary Step，例如 permission denied、hook error、queue failure、system warning/error。
- 默认视图使用连续 `Step N` label；调试视图保留完整 `Turn N` label。
- 保留底层 turnKey、event anchor、block anchor、conversationKey、task mapping，不改变原始数据。

## Non-Goals

- 不改 Trace 树 UI。
- 不替换顶部筛选 UI。
- 不改右侧 Detail 展示。
- 不做 tool_use + tool_result 聚合。
- 不改变 Conversation/minimal Turn 派生算法。
- 不改变 Task Trace Overlay 或 Task 边界逻辑。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `session-viewer`: 为 Session Trace 提供默认视图/调试视图的数据投影能力。

## Impact

- 主要影响 `viewer/claude-log.html` 中 minimal Turn 后的前端派生层。
- 需要新增前端 helper 和测试，验证 primary/internal 分类、Step label、Debug Turn label、顺序和锚点稳定。
- 不修改后端 API。
