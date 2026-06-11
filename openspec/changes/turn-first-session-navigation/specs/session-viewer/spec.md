## ADDED Requirements

### Requirement: Session 页面 Turn-first 浏览
Claude Log Viewer 的 `Session` 页面 SHALL 以稳定的人类可读 Turn 列表作为主要 session 浏览方式，而不是将原始 event ID、UUID 或文件行号作为主导航语言。

#### Scenario: 默认显示 Turn 列表
- **WHEN** 用户加载一个 session 并进入 `Session` 页面
- **THEN** 页面 SHALL 显示按顺序编号的 `Turn 1`、`Turn 2`、`Turn 3` 等 Turn 条目
- **AND** Turn 条目 SHALL 展示用户消息摘要、条目数量、工具调用数量、错误数量
- **AND** 页面 SHALL NOT 在 Turn 主标题中展示 UUID 或长 event ID

#### Scenario: Turn 编号稳定
- **WHEN** 用户启用搜索筛选或类型筛选
- **THEN** 已派生的 Turn 编号 SHALL 保持不变
- **AND** 页面 SHALL NOT 基于筛选后的可见 entries 重新编号 Turn

#### Scenario: Subagent 独立 Turn 编号
- **WHEN** session 包含 subagent group
- **THEN** 每个 subagent group SHALL 拥有独立的 Turn 列表
- **AND** subagent Turn SHALL 能在其所属 group 下展开和选中

#### Scenario: 无明确用户 root 的 entries
- **WHEN** group 中存在无法归入普通用户 Turn 的系统、元数据或前置 entries
- **THEN** 页面 SHALL 将其放入 group metadata、raw 区块或内部 `Turn 0`
- **AND** 页面 SHALL NOT 因这些 entries 改变普通用户 Turn 的编号

### Requirement: Turn Detail 展示
Claude Log Viewer SHALL 在用户选择某个 Turn 后展示该 Turn 的结构化详情，便于从轮次角度核对 Agent 执行过程。

#### Scenario: 点击 Turn 显示详情
- **WHEN** 用户点击 `Session` 页面中的某个 Turn 条目
- **THEN** 页面 SHALL 将该 Turn 标记为唯一选中 Turn
- **AND** 详情区 SHALL 展示该 Turn 的 label、所属 group、entry 范围、用户文本摘要、助手文本摘要、工具调用数量和错误数量

#### Scenario: 展示 Turn 内工具调用和结果
- **WHEN** 选中 Turn 包含 tool_use 或 tool_result entries
- **THEN** Turn detail SHALL 展示工具名称、输入摘要、结果摘要和错误状态
- **AND** 长输入或长结果 SHALL 默认截断或折叠

#### Scenario: 展示 Turn Raw JSON
- **WHEN** 用户需要调试原始数据
- **THEN** Turn detail SHALL 提供折叠的 Raw JSON 区块
- **AND** Raw JSON 展开前 SHALL 不占据主要阅读空间

### Requirement: 稳定导航索引
Claude Log Viewer SHALL 在 session 加载后基于完整 entries 构建稳定导航索引，用于在 event、uuid、file anchor 和 Turn 之间互相定位。

#### Scenario: 构建 event 到 Turn 映射
- **WHEN** session 加载成功
- **THEN** 页面 SHALL 为可定位 entry 建立从 eventId 到 `{groupId, turnKey, turnIndex, entryIndex}` 的映射
- **AND** 该映射 SHALL 基于完整 entries 构建

#### Scenario: 构建 uuid 到 Turn 映射
- **WHEN** entry 包含 `uuid` 或等价 message id
- **THEN** 页面 SHALL 建立从该 id 到 `{groupId, turnKey, turnIndex, entryIndex}` 的映射
- **AND** 定位逻辑 SHALL 能使用该 id 找到所属 Turn

#### Scenario: 构建 file anchor 到 Turn 映射
- **WHEN** entry 包含 `_gid` 和 `_fileLine` 或等价文件锚点
- **THEN** 页面 SHALL 建立从 `<groupId>:<fileLine>` 到所属 Turn 的映射
- **AND** Task Segment 返回的 `main:<line>` 或 subagent line anchor SHALL 能通过该映射定位

#### Scenario: 筛选不影响导航索引
- **WHEN** 用户启用搜索筛选或类型筛选后再触发定位
- **THEN** 定位 SHALL 使用 session 加载时基于完整 entries 构建的导航索引
- **AND** SHALL NOT 只搜索当前可见 DOM 节点

### Requirement: Tasks 页面使用 Turn 作为起止锚点
Claude Log Viewer 的 `Tasks` 页面 SHALL 将任务起止位置优先展示为人类可读 Turn label，并将机器 event id 降级为调试信息。

#### Scenario: Task detail 显示 Turn 范围
- **WHEN** 当前 task 的 `startEventId` 和 `endEventId` 能映射到 Turn
- **THEN** Task detail SHALL 显示“开始：Turn N”和“结束：Turn M”
- **AND** SHALL NOT 将 UUID 或长 event id 作为默认主文本

#### Scenario: Task detail 保留原始锚点
- **WHEN** 当前 task 包含 `startEventId` 或 `endEventId`
- **THEN** Task detail SHALL 在折叠调试区或 Raw 区展示原始锚点
- **AND** 原始锚点 SHALL 可用于排查定位问题

#### Scenario: 无法映射 Turn
- **WHEN** 当前 task 的起止 event 无法映射到任何 Turn
- **THEN** Task detail SHALL 显示“无法定位 Turn”或等价提示
- **AND** 对应定位按钮 SHALL disabled 或点击后展示明确错误

### Requirement: Task 到 Session Turn 定位
Claude Log Viewer SHALL 支持从 Task detail 跳转到 Session 页面中的开始 Turn 和结束 Turn，并保持 Task 与原始执行过程可对照。

#### Scenario: 定位开始 Turn
- **WHEN** 用户在 Task detail 点击“定位开始 Turn”
- **THEN** 页面 SHALL 切换到 `Session` 页面
- **AND** 页面 SHALL 展开目标 group
- **AND** 页面 SHALL 选中并滚动到目标开始 Turn
- **AND** 目标 Turn SHALL 显示临时高亮状态

#### Scenario: 定位结束 Turn
- **WHEN** 用户在 Task detail 点击“定位结束 Turn”
- **THEN** 页面 SHALL 切换到 `Session` 页面
- **AND** 页面 SHALL 展开目标 group
- **AND** 页面 SHALL 选中并滚动到目标结束 Turn
- **AND** 目标 Turn SHALL 显示临时高亮状态

#### Scenario: 定位到 Turn 内具体 entry
- **WHEN** 目标 event 在目标 Turn 内且当前筛选允许该 entry 可见
- **THEN** 页面 SHALL 在选中 Turn 的同时高亮目标 entry
- **AND** Turn detail SHALL 能展示该 entry 的原始信息或摘要

#### Scenario: 目标 entry 被筛选隐藏
- **WHEN** 目标 event 存在但被当前搜索筛选或类型筛选隐藏
- **THEN** 页面 SHALL 仍然定位到目标 Turn header
- **AND** 页面 SHALL 显示目标 entry 被当前筛选隐藏的提示
- **AND** 页面 SHALL NOT 抛出脚本错误

#### Scenario: 目标无法定位
- **WHEN** 定位锚点不存在于当前 session 的导航索引中
- **THEN** 页面 SHALL 保持当前页面可用
- **AND** 页面 SHALL 显示不可定位提示
- **AND** SHALL NOT 静默无反应

### Requirement: Task 与 Turn 双向关联
Claude Log Viewer SHALL 在 Session Turn 和 Task Segment 之间展示双向关联，帮助用户从任务诊断跳到原始轮次，也能从原始轮次看到所属任务。

#### Scenario: Turn 展示关联 Task badge
- **WHEN** 某个 Turn 落在一个或多个 Task Segment 的起止范围内
- **THEN** `Session` 页面中的 Turn 条目 SHALL 展示对应 Task badge
- **AND** badge 文案 SHALL 使用 `Task 1`、`Task 2` 等人类可读标签

#### Scenario: 点击 Turn 中的 Task badge
- **WHEN** 用户点击 Turn 条目中的 Task badge
- **THEN** 页面 SHALL 切换到 `Tasks` 页面
- **AND** 页面 SHALL 选中对应 Task
- **AND** Task detail SHALL 展示该 Task 的详情

#### Scenario: Task Turns tab 展示包含 Turn
- **WHEN** 用户在 Task detail 查看 `Turns` tab 或等价区块
- **THEN** 页面 SHALL 展示该 Task 覆盖的 Turn 列表
- **AND** 每个 Turn SHALL 使用 `Turn N` 标签和消息摘要

### Requirement: Raw Events 调试入口保留
Claude Log Viewer SHALL 保留查看原始 event 和 Raw JSON 的能力，但普通浏览路径 SHALL 优先使用 Turn 和 Task 标签。

#### Scenario: Session 页面保留 Raw JSON
- **WHEN** 用户查看 Turn detail
- **THEN** 页面 SHALL 提供折叠 Raw JSON 入口
- **AND** 默认 SHALL 不展开完整原始 JSON

#### Scenario: Raw Events 页面继续可用
- **WHEN** 用户进入 `Raw Events` 或等价原始日志入口
- **THEN** 页面 SHALL 允许按原始 entries 查看 session 数据
- **AND** 该入口 SHALL 不影响 `Session` 页面的 Turn-first 默认展示
