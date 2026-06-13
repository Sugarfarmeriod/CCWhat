## ADDED Requirements

### Requirement: Task Trace Overlay 状态
Claude Log Viewer SHALL 使用 Task Trace Overlay 表示当前 session 的可编辑任务划分，并保持 Raw Trace、Conversation 和 Turn 数据不可变。Task 的可编辑边界 SHALL 以 Conversation 为最小单位。

#### Scenario: 自动切分确认生成 overlay
- **WHEN** 用户确认自动 Task 切分结果
- **THEN** 页面 SHALL 为当前 session 创建 active Task Trace Overlay
- **AND** overlay source SHALL 为 `auto`
- **AND** Trace 树 SHALL 使用该 overlay 渲染 `Task -> 会话 -> Turn`

#### Scenario: 编辑后 overlay 标记为 edited
- **WHEN** 用户对 active overlay 执行任意人工编辑操作
- **THEN** overlay source SHALL 变为 `edited`
- **AND** overlay SHALL 标记为存在未保存修改
- **AND** Raw Trace、Conversation 和 Turn 派生数据 SHALL NOT 被修改

#### Scenario: 无 overlay 时保持普通 Trace
- **WHEN** 当前 session 没有 active Task Trace Overlay
- **THEN** Session Trace 树 SHALL 继续展示 `Tools / Skills Snapshot -> 会话 -> Turn`
- **AND** 用户 SHALL 仍可进入手动创建 Task 流程

### Requirement: Task Trace 编辑模式
Claude Log Viewer SHALL 提供 Task Trace 编辑模式，让用户对自动切分结果做人工校正。

#### Scenario: 进入编辑模式
- **WHEN** 当前 session 存在 active Task Trace Overlay 且用户点击“编辑 Task Trace”
- **THEN** 页面 SHALL 进入编辑模式
- **AND** 页面 SHALL 显示保存编辑、撤销编辑和退出编辑模式入口
- **AND** Trace 树 SHALL 继续显示当前 overlay 的 Task-first 结构

#### Scenario: 退出编辑模式
- **WHEN** 用户退出编辑模式且没有未保存修改
- **THEN** 页面 SHALL 回到浏览模式
- **AND** active overlay SHALL 保持不变

#### Scenario: 未保存修改提示
- **WHEN** 用户存在未保存 overlay 修改并尝试切换 session、重新切分或退出编辑模式
- **THEN** 页面 SHALL 显示未保存修改提示或执行明确的撤销操作
- **AND** 页面 SHALL NOT 静默丢弃编辑结果

### Requirement: 调整 Task 边界
Claude Log Viewer SHALL 允许用户通过按钮操作调整 Task 的起始会话和结束会话。

#### Scenario: 设为 Task 起始会话
- **WHEN** 用户在编辑模式下选中某个 Task 内或相邻范围内的会话并点击“设为 Task 起始会话”
- **THEN** 当前 Task 的 startConversationKey SHALL 更新为该会话
- **AND** Trace 树 SHALL 按新的 Task 范围刷新
- **AND** overlay SHALL 标记为未保存

#### Scenario: 设为 Task 结束会话
- **WHEN** 用户在编辑模式下选中某个 Task 内或相邻范围内的会话并点击“设为 Task 结束会话”
- **THEN** 当前 Task 的 endConversationKey SHALL 更新为该会话
- **AND** Trace 树 SHALL 按新的 Task 范围刷新
- **AND** overlay SHALL 标记为未保存

#### Scenario: 非法边界
- **WHEN** 用户选择的起点晚于终点或会导致 Task 范围无效
- **THEN** 页面 SHALL 阻止该操作并显示明确提示
- **AND** overlay SHALL 保持原状态

### Requirement: 移动会话到相邻 Task
Claude Log Viewer SHALL 允许用户将边界附近的完整会话移动到上一个或下一个 Task，用于快速修正相邻 Task 边界。

#### Scenario: 移到上一个 Task
- **WHEN** 用户在编辑模式下选中某个 Task 的首部会话并点击“移到上一个 Task”
- **THEN** 页面 SHALL 调整当前 Task 和上一个 Task 的边界
- **AND** 被选中会话及其全部 Turn SHALL 属于上一个 Task
- **AND** overlay SHALL 标记为未保存

#### Scenario: 移到下一个 Task
- **WHEN** 用户在编辑模式下选中某个 Task 的尾部会话并点击“移到下一个 Task”
- **THEN** 页面 SHALL 调整当前 Task 和下一个 Task 的边界
- **AND** 被选中会话及其全部 Turn SHALL 属于下一个 Task
- **AND** overlay SHALL 标记为未保存

#### Scenario: 无相邻 Task
- **WHEN** 用户选中的会话不存在可移动到的上一个或下一个 Task
- **THEN** 对应操作 SHALL disabled 或展示明确不可用提示

### Requirement: 拆分、合并和删除 Task
Claude Log Viewer SHALL 支持基础 Task 结构编辑，包括拆分、合并和删除。

#### Scenario: 从当前会话拆分 Task
- **WHEN** 用户在编辑模式下选中某个 Task 内的会话并点击“从当前会话拆分 Task”
- **THEN** 页面 SHALL 将原 Task 拆为两个连续 Task
- **AND** 新 Task SHALL 从选中会话开始
- **AND** 两个 Task SHALL 保持非重叠连续范围
- **AND** overlay SHALL 标记为未保存

#### Scenario: 合并下一个 Task
- **WHEN** 用户在编辑模式下选中 Task 并点击“合并下一个 Task”
- **THEN** 页面 SHALL 将当前 Task 与下一个 Task 合并为一个 Task
- **AND** 合并后 Task SHALL 覆盖两个原 Task 的连续范围
- **AND** overlay SHALL 标记为未保存

#### Scenario: 删除 Task
- **WHEN** 用户在编辑模式下选中 Task 并点击“删除 Task”
- **THEN** 页面 SHALL 从 overlay 中移除该 Task
- **AND** 被删除 Task 覆盖的会话 SHALL 进入 unassigned 状态或被相邻 Task 接管
- **AND** 页面 SHALL 明确展示处理结果
- **AND** overlay SHALL 标记为未保存

### Requirement: 编辑 Task 元数据
Claude Log Viewer SHALL 允许用户修改 Task 的基础人工标注信息。

#### Scenario: 修改标题
- **WHEN** 用户在编辑模式下修改 Task 标题并保存
- **THEN** overlay 中该 Task 的 title SHALL 更新
- **AND** Trace 树 Task 节点 SHALL 显示新标题

#### Scenario: 修改类型
- **WHEN** 用户在编辑模式下修改 Task 类型并保存
- **THEN** overlay 中该 Task 的 taskType SHALL 更新
- **AND** Trace 树 Task 节点 SHALL 显示新类型

### Requirement: 手动创建 Task
Claude Log Viewer SHALL 允许用户不依赖自动切分，直接从 Trace 树中选择会话范围创建 Task。

#### Scenario: 进入手动创建模式
- **WHEN** 用户点击“手动创建 Task”
- **THEN** 页面 SHALL 进入手动创建模式
- **AND** 页面 SHALL 引导用户选择起始会话和结束会话

#### Scenario: 创建手动 Task
- **WHEN** 用户选择有效起始会话、结束会话、标题和类型并点击“创建”
- **THEN** 页面 SHALL 创建或更新 active Task Trace Overlay
- **AND** 新 Task SHALL 覆盖选定的连续会话范围
- **AND** overlay source SHALL 为 `manual` 或 `edited`
- **AND** Trace 树 SHALL 刷新为 Task-first 结构

#### Scenario: 手动范围无效
- **WHEN** 用户选择的会话范围为空、顺序错误或跨越当前版本不支持的范围
- **THEN** 页面 SHALL 阻止创建并显示明确提示

### Requirement: 会话不可被拆分
Claude Log Viewer SHALL 保证一个会话内部的所有 Step/Turn 始终整体归属同一个 Task 或 unassigned 区域。

#### Scenario: 选中 Turn 时回退到会话
- **WHEN** 用户在编辑模式下选中某个 Turn 并执行 Task 边界操作
- **THEN** 页面 SHALL 使用该 Turn 所属会话作为操作对象
- **AND** 页面 SHALL NOT 只移动或拆分该 Turn

#### Scenario: 渲染 Task-first 树
- **WHEN** Trace 树使用 active overlay 渲染 Task-first 结构
- **THEN** 每个 Task SHALL 包含完整会话节点
- **AND** 会话节点下 SHALL 保留全部原始 Turn/Step 明细

### Requirement: 保存、撤销和导出 Overlay
Claude Log Viewer SHALL 提供基础 overlay 生命周期操作，用于后续数据集构建。

#### Scenario: 保存编辑
- **WHEN** 用户点击“保存编辑”
- **THEN** 当前 overlay SHALL 标记为 saved
- **AND** revision SHALL 增加或 updatedAt SHALL 更新
- **AND** Trace 树 SHALL 继续使用保存后的 overlay

#### Scenario: 撤销编辑
- **WHEN** 用户点击“撤销编辑”
- **THEN** 页面 SHALL 恢复到最近一次 saved overlay
- **AND** 未保存修改 SHALL 被丢弃
- **AND** Trace 树 SHALL 重新渲染

#### Scenario: 导出 overlay JSON
- **WHEN** 用户点击“导出 Task Trace Overlay”
- **THEN** 页面 SHALL 导出包含 sessionId、overlayId、source、revision、tasks、start/end Conversation、start/end Turn 和 start/end event anchor 的 JSON
- **AND** 导出内容 SHALL NOT 包含完整 Raw Trace JSON

### Requirement: 第一版不实现拖拽和后端持久化
本 change SHALL 使用按钮和选择模式实现 Task Trace Overlay 编辑，不要求拖拽交互或后端数据库持久化。

#### Scenario: 不要求拖拽
- **WHEN** 用户进入编辑模式
- **THEN** 页面 SHALL 提供按钮或菜单操作
- **AND** 本 change SHALL NOT 要求通过拖拽移动 Task、会话或 Turn

#### Scenario: 不要求后端持久化
- **WHEN** 用户保存 overlay
- **THEN** 第一版 MAY 只保存为前端内存态
- **AND** 页面 SHALL 提供导出 JSON 作为持久化替代
- **AND** 本 change SHALL NOT 要求新增后端数据库 API
