## ADDED Requirements

### Requirement: Tasks 页面提供手动切分入口
Session Viewer SHALL 在 Tasks 页面提供“手动切分”入口，并与现有“自动切分”入口并列展示。

#### Scenario: 显示两个切分入口
- **WHEN** 用户打开 Tasks 页面并已选择 session
- **THEN** 页面 SHALL 显示“自动切分”和“手动切分”两个入口
- **AND** “自动切分” SHALL 沿用现有自动切分流程
- **AND** “手动切分” SHALL 不调用自动切分 API

#### Scenario: 从 Tasks 页面进入手动切分
- **WHEN** 用户点击“手动切分”
- **THEN** 页面 SHALL 自动跳转到 Session 页面
- **AND** Session 页面 SHALL 进入手动切分模式
- **AND** Trace 树 SHALL 优先展示原始会话结构，便于用户对照内容切分

### Requirement: Session 页面支持手动切分模式
Session Viewer SHALL 允许用户在原始 Session 会话树上选择连续会话范围并创建 Task。

#### Scenario: 选择起始和结束会话
- **WHEN** 用户处于手动切分模式
- **AND** 用户点击第一个会话
- **THEN** 页面 SHALL 将该会话标记为起始会话
- **WHEN** 用户点击第二个会话
- **THEN** 页面 SHALL 将该会话标记为结束会话
- **AND** 页面 SHALL 高亮当前候选会话范围

#### Scenario: 创建手动 Task
- **WHEN** 用户已选择有效起始会话和结束会话
- **AND** 用户点击“创建 Task”
- **THEN** 页面 SHALL 在当前 Task Trace Overlay 中追加一个 Task
- **AND** Task SHALL 使用 `startConversationKey` 和 `endConversationKey` 作为主边界
- **AND** Task 标题 SHALL 默认生成为 `任务 N`
- **AND** Task 类型 SHALL 默认为 `manual` 或 `unknown`
- **AND** 该 Task 覆盖的会话范围 SHALL 在手动切分模式中持续高亮
- **AND** 高亮区域 SHALL 标记对应 Task 编号

#### Scenario: 连续创建多个 Task
- **WHEN** 用户创建一个 Task 后仍处于手动切分模式
- **THEN** 页面 SHALL 清空当前起止选择
- **AND** 用户 SHALL 可以继续选择下一段会话创建下一个 Task
- **AND** 已创建 Task 的持续高亮 SHALL 保留

#### Scenario: 撤销上一次 Task 切分
- **WHEN** 用户已在手动切分模式中创建至少一个 Task
- **AND** 用户点击“撤销上一次”
- **THEN** 页面 SHALL 删除最近一次创建的 Task
- **AND** 页面 SHALL 移除该 Task 对应的持续高亮
- **AND** 该范围内的会话 SHALL 恢复为未分配状态
- **AND** 页面 SHALL 继续停留在手动切分模式

#### Scenario: 确认执行手动切分
- **WHEN** 用户点击“确认执行这次 Task 划分”
- **THEN** 页面 SHALL 退出手动切分模式
- **AND** Session Trace SHALL 使用 active Task Trace Overlay 渲染为 `Task -> 会话 -> Turn/Step`
- **AND** 未分配会话 SHALL 显示在 Unassigned 区域
- **AND** 手动切分模式中的临时候选高亮和持续标注高亮 SHALL 被清除

### Requirement: 手动切分边界安全
Session Viewer SHALL 保证手动切分不会产生重叠 Task，也不会拆分单个会话内部的 Turn/Step。

#### Scenario: 阻止重叠范围
- **WHEN** 用户选择的会话范围与已有 Task 范围重叠
- **THEN** 页面 SHALL 阻止创建 Task
- **AND** 页面 SHALL 显示明确提示
- **AND** 已有 Task 的持续高亮 SHALL 保持不变

#### Scenario: 会话不可拆分
- **WHEN** 用户创建手动 Task
- **THEN** 该 Task SHALL 覆盖完整会话
- **AND** 会话内部所有 Turn/Step SHALL 整体归属同一个 Task

#### Scenario: 无 session 时不可进入
- **WHEN** 当前没有选中的 session
- **THEN** “手动切分”入口 SHALL disabled 或显示明确不可用提示

### Requirement: 最小自动化测试
本 change SHALL 只要求最小必要自动化测试，复杂体验由真实 session 手动验收。

#### Scenario: 静态和 DOM 冒烟测试
- **WHEN** 执行测试
- **THEN** 测试 SHOULD 覆盖手动切分入口存在
- **AND** SHOULD 覆盖点击入口后进入 Session 手动切分模式
- **AND** SHOULD 覆盖选择两个会话后能创建一个 manual Task Overlay
- **AND** SHOULD 覆盖撤销上一次会移除最近创建的 Task

#### Scenario: 手动验收
- **WHEN** 实现完成
- **THEN** 用户 SHALL 使用真实 session 验收连续创建多个 Task、持续高亮、撤销上一次、确认执行、Task-first 展示和未分配会话展示
