## ADDED Requirements

### Requirement: Turn-level Diff Projection
Claude Log Viewer SHALL build a frontend-only turn diff projection for the current session. The projection SHALL compare a selected Turn with its previous comparable Turn and SHALL NOT depend on task segmentation, Task Dataset save/export, Dataset `changes`, Dataset `patches`, or live repository `git diff`.

#### Scenario: Session 加载后可构建 Turn Diff
- **WHEN** viewer 已加载当前 session 的 Conversation/minimal Turn 数据
- **THEN** viewer SHALL be able to build a turn diff projection from the loaded frontend Turn data
- **AND** the projection SHALL preserve each Turn's stable label, kind, conversation key, group scope and anchor references
- **AND** the projection SHALL NOT mutate raw entries, minimal Turn objects, Task Trace Overlay data, or Dataset source payloads

#### Scenario: 不依赖 task segmentation
- **WHEN** 当前 session 尚未运行 task segmentation
- **AND** 用户打开 `Diff` 页面或选中某个 Turn 查看 diff
- **THEN** viewer SHALL still render turn-level diff from session Turn data
- **AND** viewer SHALL NOT call `/api/task-segments` solely to compute turn diff

#### Scenario: 不依赖 Dataset
- **WHEN** 用户查看 turn-level diff
- **THEN** viewer SHALL NOT require saving or exporting a Task Dataset
- **AND** viewer SHALL NOT read Dataset trace `changes` or `patches` as the primary diff source

### Requirement: Turn Diff 固定槽位
Turn-level diff SHALL compare only the stable observability slots `thinking`, `text`, `tool call`, and `tool result` by default. The modal SHALL always render these four slots in this order, with baseline content on the left and current content on the right. Metadata, parameters, system prompt, commands, files, errors, and other raw fields SHALL NOT appear in the default diff modal.

#### Scenario: 四个槽位始终展示
- **WHEN** turn diff modal is open
- **THEN** modal body SHALL render exactly the default slots `thinking`, `text`, `tool call`, and `tool result` in that order
- **AND** each slot SHALL contain a left baseline column and a right current column
- **AND** slots with no content SHALL remain visible and display `(无)` or an equivalent empty state

#### Scenario: 默认不展示噪声字段
- **WHEN** current or baseline Turn raw data contains metadata, parameters, system prompt, commands, files, errors, or adapter-specific fields
- **THEN** those fields SHALL NOT be rendered as default diff slots or sections
- **AND** the existing `原始 JSON` or debug view SHALL remain the path for inspecting those fields

#### Scenario: tool call 和 tool result 分离
- **WHEN** a Turn contains both tool invocation data and tool output data
- **THEN** tool invocation name/input SHALL render in the `tool call` slot
- **AND** tool output/result SHALL render in the `tool result` slot
- **AND** one slot SHALL NOT hide or replace the other

### Requirement: Turn Diff 视觉状态和完整内容
Turn-level diff SHALL use stable visual rules for each fixed slot. Added, removed, changed, and unchanged content SHALL be visually distinct. Content SHALL NOT be truncated with ellipses or irreversible summaries in the modal.

#### Scenario: 无变化内容不染色
- **WHEN** a slot has equivalent baseline and current content
- **THEN** modal SHALL render both columns with normal neutral styling
- **AND** the slot SHALL NOT use added, removed, or changed background colors
- **AND** both sides SHALL still show the slot content

#### Scenario: 新增、删除和修改状态
- **WHEN** baseline content is empty and current content is present
- **THEN** the current column SHALL use added styling and the baseline column SHALL show the empty state
- **WHEN** baseline content is present and current content is empty
- **THEN** the baseline column SHALL use removed styling and the current column SHALL show the empty state
- **WHEN** both sides have content but differ
- **THEN** the baseline column SHALL use removed/old styling and the current column SHALL use added/new styling

#### Scenario: 行级高亮
- **WHEN** both sides have textual content and the slot content differs
- **THEN** modal SHALL provide line-level diff highlighting for changed, added, and removed lines
- **AND** line-level highlighting SHALL apply to `thinking`, `text`, `tool call`, and `tool result` when their content is textual or can be formatted as text

#### Scenario: 内容不得省略
- **WHEN** a slot contains long thinking, text, tool call input, or tool result output
- **THEN** modal SHALL make the full slot content available without ellipsis truncation
- **AND** the slot MAY use an internal scroll container, expansion control, or equivalent complete-view mechanism
- **AND** copied or viewed slot content SHALL preserve line breaks and indentation when possible

### Requirement: Diff 页面展示 Turn Diff 总览
The left navigation `Diff` page SHALL provide a session-level index for turn-level diffs. It SHALL list comparable Turns in session order and provide an action that opens the same diff modal used by the selected Turn/Step detail.

#### Scenario: 打开 Diff 页面
- **WHEN** 用户点击左侧 `Diff`
- **AND** 当前 session 已加载
- **THEN** 主工作区 SHALL display a turn diff index for the current session
- **AND** each item SHALL identify the current Turn and its baseline Turn by stable labels and kind
- **AND** each item SHALL provide a `Diff with Prev` or equivalent action
- **AND** the page SHALL NOT show only task-level `Files Changed` / `Files Read` summaries

#### Scenario: Diff 总览打开弹层
- **WHEN** 用户点击 Diff 总览中的某个 Turn diff item
- **THEN** viewer SHALL open the turn diff modal for that Turn
- **AND** the modal SHALL identify the current Turn and baseline Turn by stable labels and kind
- **AND** viewer MAY also navigate to, select, scroll to, or highlight the corresponding Turn when useful

#### Scenario: Diff 空态
- **WHEN** 当前 session 未加载、没有 Turns、或没有 previous comparable Turn
- **THEN** `Diff` page SHALL show a clear empty state explaining why no turn diff is available
- **AND** the page SHALL NOT be blank

### Requirement: Turn Diff 比较对象
Turn-level diff SHALL make the comparison baseline explicit. In default view it SHALL compare the selected visible Step's underlying Turn to the previous comparable visible Step or Turn; in debug view it SHALL compare the selected minimal Turn to the previous comparable minimal Turn in original order.

#### Scenario: 默认视图比较对象
- **WHEN** 用户在默认视图中选择一个 Step
- **THEN** Turn diff SHALL identify the selected Step's underlying Turn as the current Turn
- **AND** baseline SHALL be the previous comparable visible Step or Turn in the current session order
- **AND** the diff header SHALL show both current and baseline labels

#### Scenario: 调试视图比较对象
- **WHEN** 用户在调试视图中选择一个 minimal Turn
- **THEN** Turn diff SHALL compare it with the previous comparable minimal Turn in original Turn order
- **AND** ordinary internal Turns SHALL be eligible as baselines in debug view

#### Scenario: 没有 baseline
- **WHEN** 用户选择 session 中第一个 comparable Turn
- **THEN** Turn diff SHALL show a clear "no previous Turn" or equivalent baseline-empty state
- **AND** the current Turn's fields MAY be shown as initial added content

#### Scenario: 手动选择 baseline
- **WHEN** 用户打开 Turn diff modal
- **AND** 当前 Turn 前面存在多个可比较 Turns
- **THEN** modal SHALL provide a baseline selector or equivalent manual target control
- **AND** selecting a different baseline SHALL recompute the modal diff without mutating session Turn data

### Requirement: Turn Diff Modal
Claude Log Viewer SHALL present turn-level diff in a modal overlay opened from a `Diff with Prev` action. The modal SHALL provide enough width and scrolling space for structured, side-by-side comparison.

#### Scenario: Turn 详情提供 Diff 按钮
- **WHEN** 用户选中可比较的 Turn 或 Step
- **THEN** 右侧详情操作区 SHALL show a `Diff with Prev` or equivalent button
- **AND** clicking the button SHALL open a modal overlay instead of replacing the Turn detail content

#### Scenario: Modal header controls
- **WHEN** turn diff modal is open
- **THEN** modal header SHALL show current Turn and baseline Turn labels in an `A -> B` form
- **AND** modal header SHALL provide close control
- **AND** modal header SHALL provide previous/next diff navigation when adjacent diff pairs exist
- **AND** modal header SHALL provide manual baseline selection when candidates exist

#### Scenario: Modal body sections
- **WHEN** turn diff modal is open
- **THEN** modal body SHALL organize comparison into the fixed slots `thinking`, `text`, `tool call`, and `tool result`
- **AND** each slot SHALL show added, removed, changed, or unchanged status using clear badges or labels

#### Scenario: Side-by-side rendering
- **WHEN** a slot contains modified content with both old and new values
- **THEN** modal SHALL render the values in side-by-side `OLD` and `NEW` columns or an equivalent two-sided comparison
- **AND** added-only and removed-only content SHALL be visually distinct from modified content

#### Scenario: Modal scroll and close behavior
- **WHEN** diff content exceeds the viewport
- **THEN** modal body SHALL be scrollable
- **AND** large slot blocks SHALL remain independently scrollable, expandable, or otherwise bounded without losing content
- **AND** user SHALL be able to close the modal with the close control and Escape key

## MODIFIED Requirements

### Requirement: Turn 详情只展示 Agent 响应和原始 JSON
Claude Log Viewer SHALL 在用户选中 Turn 节点时展示当前 Turn 的核心观测内容。详情区 SHALL 展示 `Agent 响应` 和折叠的 `原始 JSON`，并可在操作区提供 `Diff with Prev` 入口打开 turn diff modal。Turn diff modal SHALL only compare the selected Turn with its explicit baseline Turn and SHALL NOT replace the raw JSON inspection path.

#### Scenario: Turn detail 区块数量
- **WHEN** 用户选中任意 Turn 节点
- **THEN** 右侧详情区 SHALL 展示 `Agent 响应` 区块
- **AND** 右侧详情区 SHALL 展示折叠的 `原始 JSON` 区块
- **AND** 右侧详情操作区 MAY 展示 `Diff with Prev` 或等价按钮
- **AND** 右侧详情区 SHALL NOT 展示 task boundary、Task Dataset `changes` / `patches` 或 req/resp network messages diff 作为当前 Turn diff 的替代内容

#### Scenario: Agent 响应按 Turn kind 渲染
- **WHEN** 选中的 Turn kind 为 `user_message`、`thinking`、`assistant_text`、`tool_use`、`tool_result`、`system`、`context` 或 `unknown`
- **THEN** `Agent 响应` 区块 SHALL 展示当前 minimal Turn 对应的文本、工具名、工具输入、工具结果或摘要
- **AND** 该区块 SHALL NOT 展示同一会话内其他 Turn 的内容

#### Scenario: Turn Diff modal 只对应当前 Turn
- **WHEN** 用户通过当前 Turn 的 `Diff with Prev` 打开 modal
- **THEN** modal SHALL display differences for the selected Turn and its explicit baseline Turn only
- **AND** the diff SHALL NOT aggregate all task evidence or all session file changes into the selected Turn detail

#### Scenario: Raw JSON 只对应当前 Turn
- **WHEN** 用户展开 `原始 JSON`
- **THEN** 页面 SHALL 展示当前 Turn 对应的原始 entry 或 block anchor 数据
- **AND** Raw JSON SHALL NOT 默认展示整个会话、整个 session 或相邻 Turn 的 JSON
