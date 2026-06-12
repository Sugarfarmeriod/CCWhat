## ADDED Requirements

### Requirement: Session 页面显示 Trace 树
Claude Log Viewer 的 `Session` 页面 SHALL 基于已有 Conversation/minimal Turn 数据层，以树状结构展示当前 session 的执行 Trace，而不是继续使用平铺 Turn 卡片作为主浏览结构。

#### Scenario: 默认显示会话与 Turn 树
- **WHEN** 用户加载一个 session 并进入 `Session` 页面
- **THEN** 页面 SHALL 显示按 group 分段的 Trace 树
- **AND** 每个 group 下 SHALL 展示按顺序编号的会话节点，例如 `会话 1`、`会话 2`
- **AND** 每个会话节点下 SHALL 展示该会话包含的 minimal Turn 节点，例如 `Turn 1`、`Turn 2`

#### Scenario: 会话节点展示摘要
- **WHEN** Trace 树渲染会话节点
- **THEN** 会话节点 SHALL 展示会话 label、用户请求摘要和 Turn 数量
- **AND** 会话节点 SHALL NOT 使用 UUID、event id 或文件行号作为默认标题

#### Scenario: Turn 节点展示摘要
- **WHEN** Trace 树渲染 Turn 节点
- **THEN** Turn 节点 SHALL 展示稳定 Turn label、kind badge 和当前 Turn 的简短内容摘要
- **AND** Turn 节点 SHALL NOT 混入同一会话内其他 Turn 的摘要

### Requirement: Trace 树节点交互
Claude Log Viewer SHALL 支持在 Trace 树中展开/折叠会话、选择会话和选择 Turn，并用右侧详情区展示对应层级的内容。

#### Scenario: 展开和折叠会话
- **WHEN** 用户点击会话节点的展开/折叠控件
- **THEN** 页面 SHALL 切换该会话下 Turn 节点的可见状态
- **AND** 其他会话的展开状态 SHALL 保持不变

#### Scenario: 选择会话
- **WHEN** 用户点击会话节点主体
- **THEN** 页面 SHALL 将该会话标记为当前选中节点
- **AND** 右侧详情区 SHALL 展示会话级摘要

#### Scenario: 选择 Turn
- **WHEN** 用户点击某个 Turn 节点
- **THEN** 页面 SHALL 将该 Turn 标记为当前选中节点
- **AND** 右侧详情区 SHALL 展示该 Turn 的极简详情
- **AND** 当前选中状态 SHALL 只落在一个 Trace 节点上

#### Scenario: Task 定位跳转到 Trace Turn
- **WHEN** 用户从 `Tasks` 页面点击“定位开始 Turn”或“定位结束 Turn”
- **THEN** 页面 SHALL 切换到 `Session` 页面
- **AND** 页面 SHALL 展开目标 Turn 所属会话
- **AND** 页面 SHALL 选中、滚动并临时高亮目标 Turn 节点

### Requirement: 会话详情极简展示
Claude Log Viewer SHALL 在用户选中会话节点时展示轻量会话摘要，用于确认该会话对应的一次用户请求和 Agent 回复范围。

#### Scenario: 会话详情内容
- **WHEN** 用户选中会话节点
- **THEN** 右侧详情区 SHALL 展示会话 label、所属 group、用户请求内容或摘要、Agent 最终反馈摘要、Turn 数量和起止锚点
- **AND** 右侧详情区 SHALL NOT 展示 task evidence、diagnostics、diff、test result 或 req/resp 明细

#### Scenario: 会话详情中的 Turn 入口
- **WHEN** 会话详情展示该会话包含的 Turn
- **THEN** 每个 Turn 入口 SHALL 使用稳定 Turn label 和 kind
- **AND** 用户点击该入口后 SHALL 选中 Trace 树中对应 Turn 节点

### Requirement: Turn 详情只展示 Agent 响应和原始 JSON
Claude Log Viewer SHALL 在用户选中 Turn 节点时只展示两个主要区块：`Agent 响应` 和 `原始 JSON`。

#### Scenario: Turn detail 区块数量
- **WHEN** 用户选中任意 Turn 节点
- **THEN** 右侧详情区 SHALL 展示 `Agent 响应` 区块
- **AND** 右侧详情区 SHALL 展示折叠的 `原始 JSON` 区块
- **AND** 右侧详情区 SHALL NOT 展示 evidence、files、diff、commands、tests、diagnostics 或 task boundary 字段

#### Scenario: Agent 响应按 Turn kind 渲染
- **WHEN** 选中的 Turn kind 为 `user_message`、`thinking`、`assistant_text`、`tool_use`、`tool_result`、`system`、`context` 或 `unknown`
- **THEN** `Agent 响应` 区块 SHALL 展示当前 minimal Turn 对应的文本、工具名、工具输入、工具结果或摘要
- **AND** 该区块 SHALL NOT 展示同一会话内其他 Turn 的内容

#### Scenario: Raw JSON 只对应当前 Turn
- **WHEN** 用户展开 `原始 JSON`
- **THEN** 页面 SHALL 展示当前 Turn 对应的原始 entry 或 block anchor 数据
- **AND** Raw JSON SHALL NOT 默认展示整个会话、整个 session 或相邻 Turn 的 JSON

### Requirement: 筛选与搜索不改变 Trace 树编号
Claude Log Viewer SHALL 保持会话编号、Turn 编号和 Trace node key 的稳定性，不因搜索或类型筛选而重新切分或重新编号。

#### Scenario: 类型筛选保持编号稳定
- **WHEN** 用户切换 `user / assistant / system / attachment / perm / fhs / queue / other` 类型筛选
- **THEN** 会话 label 和 Turn label SHALL 保持不变
- **AND** 页面 SHALL NOT 基于筛选后的可见节点重新生成编号

#### Scenario: 搜索保持编号稳定
- **WHEN** 用户在 Session 页面搜索文本
- **THEN** Trace 树 MAY 隐藏或标记不匹配的 Turn 节点
- **AND** 匹配节点 SHALL 保留原始会话编号和 Turn 编号

#### Scenario: 选中节点被筛选隐藏
- **WHEN** 当前选中的 Turn 被搜索或类型筛选隐藏
- **THEN** 右侧详情区 SHALL 显示“当前筛选隐藏了该 Turn”或等价提示
- **AND** 页面 SHALL NOT 自动选择另一个 Turn 或静默清空详情区

### Requirement: 本 change 不实现 Task 与 Tools/Skills 树层
本 change SHALL 只实现 `Trace -> 会话 -> Turn` 的 Session 页面树状浏览和极简 Turn 详情，不引入后续 change 的树顶层能力。

#### Scenario: 不注入 Task 顶层
- **WHEN** 用户完成任务切分或进入 `Tasks` 页面
- **THEN** `Session` 页面的 Trace 树 SHALL NOT 在本 change 中新增 `Task -> 会话 -> Turn` 顶层结构
- **AND** Task 注入 SHALL 留给后续 change 实现

#### Scenario: 不展示 Tools/Skills Snapshot 节点
- **WHEN** 用户进入 `Session` 页面
- **THEN** Trace 树 SHALL NOT 在本 change 中新增 `Tools Snapshot`、`Skills Snapshot` 或等价顶层节点
- **AND** Tools/Skills Snapshot SHALL 留给后续 change 实现
