## Why

当前 viewer 改版把页面拆成了很多导航项：Overview、Timeline、Sessions、Raw Events、Req / Resp、Diff、Diagnostics、Export、Settings。这个方向过早扩大了范围，导致最基本的两个工作流没有稳定落地：

- 用户选择 session 后，`Session` 页面应该能直接看到旧版日志树和日志详情。
- 用户进入 `Tasks` 页面后，应该能进行任务切分并查看 Task List + Task Detail。

现在用户在左侧点击 `Sessions` 后主区域没有可用的 session 详情展示，这属于迁移 bug，而不是“功能尚未实现”的可接受状态。

## What Changes

- 将本 change 的目标收敛为两个核心模块：
  - `Session`：承接旧版本地日志展示能力，包括 turn 树、entry 列表、entry 详情、类型筛选、搜索和定位。
  - `Tasks`：承接任务切分能力，包括切分入口、Task List、Task Detail、证据跳转和 raw debug。
- 左侧导航第一阶段只需要稳定支持 `Session` 和 `Tasks`。
- 其他页面，如 Overview、Timeline、Req / Resp、Diff、Diagnostics、Export、Settings，不作为本阶段核心验收目标；可以保留入口或占位，但不能影响 Session / Tasks 主流程。
- 用户选择 Project + Session 后，主页面必须有可见内容，不允许出现空白主工作区。
- 默认页面改为 `Session`，因为当前最重要的是先完整迁移旧版日志查看能力。
- Task 跳转到原始事件时，应跳回 `Session` 页面并定位对应 entry。
- 已加载 session 后点击 `Tasks`，页面必须自动基于当前 session 发起任务切分或展示已有切分结果，不允许显示空白。
- 从 `Session -> Tasks -> Session` 往返切换时，必须保留当前 session 的日志列表和详情区。
- `Session` 页面恢复“报告分析”入口，复用已有 `/api/analyze` 与分析模式弹窗，不新建报告链路。

## Capabilities

### Modified Capabilities

- `session-viewer`: 从过宽的多页面工作台收敛为 `Session + Tasks` 双模块工作台，优先保证本地日志查看和任务切分可用。

## Impact

- 主要影响：
  - `viewer/claude-log.html`
  - `tests/test_task_segmentation_frontend.py`
  - `tests/test_current_session_analysis.py`
  - `tests/test_task_segmentation_dom.js`
- OpenSpec 影响：
  - 重写本 change 的 design/spec/tasks，使验收目标聚焦于 Session 展示和 Tasks 切分。
- 回归修复：
  - 修复点击 `Tasks` 后空白。
  - 修复 `Tasks` 切回 `Session` 后仍空白。
  - 修复报告分析入口在新版 `Session` 页面缺失。
- 不要求本阶段完成：
  - Diff 页面完整实现
  - Req / Resp 页面迁移
  - Diagnostics 页面完整实现
  - Export 页面重构
  - Dataset preview
