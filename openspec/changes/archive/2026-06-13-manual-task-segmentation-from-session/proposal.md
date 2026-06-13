## Why

当前用户可以自动切分 Task，也可以在 Session 页面编辑已有 Task Trace Overlay。但“从零手动切分”还不够顺手：如果只在 Tasks 页面给一个会话编号列表，用户必须来回对照原始会话内容，记住从哪个会话到哪个会话属于同一个 Task，认知成本很高。

更合理的流程是：用户从 Tasks 页面进入“手动切分”，系统自动跳转到 Session 原始会话树，让用户直接看着会话内容选择起始会话和结束会话，连续创建 Task。完成后，Session 页面立即切换为 Task-first 展示。

## What Changes

- Tasks 页面提供清晰的两个入口：
  - 自动切分
  - 手动切分
- 点击“手动切分”后自动跳转到 Session 页面。
- Session 页面进入手动切分模式，展示原始会话树。
- 用户在原始会话树中选择起始会话和结束会话，创建 `Task 1 / Task 2 / ...`。
- 已创建 Task 的会话范围在手动切分模式中持续高亮，并标记对应 Task 编号。
- 用户可以连续创建多个 Task，直到点击“完成手动切分”。
- 用户可以撤销上一次手动 Task 切分，用于修正手滑或误选。
- 完成后生成或更新 Task Trace Overlay，并在 Session 页面展示 `Task -> 会话 -> Turn/Step`。
- 手动切分的最小单位仍然是会话，不允许把一个会话内部的 Step/Turn 拆到不同 Task。

## Non-Goals

- 不做拖拽切分。
- 不做后端持久化。
- 不做复杂 Task 元数据编辑器。
- 不重新设计自动切分算法。
- 不实现跨 session 手动切分。
- 不要求大量自动化测试；本 change 只做必要冒烟测试，主要交给真实 session 手动验收。

## Impact

- 主要影响 `viewer/claude-log.html` 的 Tasks 页面入口、Session 页面手动切分模式、Task Trace Overlay 创建流程。
- 复用现有会话级 Task Trace Overlay 能力。
- 测试以最小静态/DOM 冒烟为主，保证入口、模式状态和基础创建流程不崩。
