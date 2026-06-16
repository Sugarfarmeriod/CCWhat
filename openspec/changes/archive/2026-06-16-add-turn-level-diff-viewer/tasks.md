## 1. Turn Diff 数据模型

- [x] 1.1 梳理 `viewer/claude-log.html` 中现有 Conversation/minimal Turn 和 view projection 数据结构，确认可复用的 Turn label、kind、anchor、raw/detail helpers。
- [x] 1.2 实现前端 `buildTurnDiffProjection` / `buildTurnDiffModel` 等 helper，从已加载 session Turn 数据生成 diff model，且不修改底层 Turn 对象。
- [x] 1.3 为 diff model 抽取固定四槽位：`thinking`、`text`、`tool call`、`tool result`；默认排除 metadata、parameters、system prompt、commands、files、errors 等噪声字段。
- [x] 1.4 实现 baseline 选择逻辑：默认视图比较前一个 comparable visible Step/Turn，调试视图比较前一个 comparable minimal Turn，并生成可手动选择的 previous Turn 候选列表。
- [x] 1.5 实现轻量 line diff / side-by-side diff 数据结构，支持 `OLD` / `NEW` 对照、行级高亮和新增/删除/修改/无变化状态。

## 2. Diff with Prev 弹层

- [x] 2.1 在选中 Turn/Step 的右侧详情操作区加入 `Diff with Prev` 或等价按钮；无 baseline 时提供清晰反馈。
- [x] 2.2 实现 diff modal overlay，包含 `Turn A -> Turn B` 标题、关闭按钮、上一组/下一组 diff 导航和 baseline selector。
- [x] 2.3 固定渲染 `thinking`、`text`、`tool call`、`tool result` 四个槽位；每个槽位始终包含 baseline/current 两列，空值显示 `(无)` 或等价空态。
- [x] 2.4 对修改内容渲染左右 `OLD` / `NEW` 对照和行级高亮；对新增/删除内容使用清晰边框、颜色和 label；无变化内容使用中性样式但仍完整展示。
- [x] 2.5 处理长 thinking、text、tool call、tool result：不得用省略号截断，必须通过块内滚动、展开或等价机制完整可读，并支持 Escape/关闭按钮关闭。
- [x] 2.6 确保 modal 不展示 Task Dataset `changes` / `patches`，也不聚合 task-level 或 session-level 文件改动作为当前 Turn diff。

## 3. Diff 页面入口

- [x] 3.1 将左侧 `Diff` 页面从 task evidence 文件汇总改为 turn diff index/入口。
- [x] 3.2 按 session 顺序列出可比较 Turn 的 diff 条目，展示 current/baseline label、kind 和主要变化 section 计数或摘要。
- [x] 3.3 为每个 diff item 提供打开同一 diff modal 的交互，必要时复用现有选中、滚动、高亮能力定位到对应 Turn。
- [x] 3.4 实现 session 未加载、无 Turn、无 previous comparable Turn 等清晰空态，确保页面不空白。

## 4. 回归测试与验证

- [x] 4.1 增加或更新前端静态测试，验证 `Diff` 页面不再只渲染 task-level `Files Changed` / `Files Read` 汇总。
- [x] 4.2 增加 DOM/前端测试，验证没有 task segmentation result 时仍可打开 `Diff with Prev` modal。
- [x] 4.3 增加测试覆盖 modal header、baseline selector、prev/next 导航、固定四槽位、side-by-side `OLD` / `NEW` 渲染、行级高亮和滚动容器。
- [x] 4.4 增加测试覆盖 Turn detail 中 `Agent 响应`、`原始 JSON` 保持存在，`Diff with Prev` 作为操作入口而不是 Dataset 替代内容。
- [x] 4.5 增加测试覆盖 metadata、parameters、system prompt、commands、files、errors 不进入默认 diff modal。
- [x] 4.6 增加测试覆盖长内容不出现省略截断且可完整滚动/展开查看。
- [x] 4.7 运行相关 Python/Node 测试，记录无法运行的环境限制或失败原因。
