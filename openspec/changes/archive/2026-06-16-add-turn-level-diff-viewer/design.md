## Context

主 Viewer 目前已有 `Session`、`Tasks`、`Diff` 等 App Shell 入口，并且已经具备 Conversation/minimal Turn 数据层和默认/调试视图 projection。现有 `Diff` 页面只汇总 task segmentation evidence 中的 `filesChanged` / `filesRead`，它依赖 task 数据，且不能回答“当前 Turn 相比上一个 Turn 多了什么”。

同时，Task Dataset 构建链路已经能在导出时抽取 `changes` / `patches`，但那条链路服务于离线数据集、评测和训练数据，不适合承担主 Viewer 的实时观测 UI。新的 turn diff 应在前端基于已加载 session 和 minimal Turn projection 计算，不新增后端 API，不要求先运行 task segmentation。

`claude-tap` 的 `Diff with Prev` 提供了更贴近本 change 目标的参考形态：用户在详情操作区点击按钮后打开 modal，顶部显示 `Turn A -> Turn B`、上一组/下一组导航、baseline selector 和关闭按钮，并在具体修改处使用左右 `OLD` / `NEW` 对照。CCWhat 应吸收这个交互模型，但内容组织不应照搬 network request body 的 `Parameters` / `System` / `Tools` 视角，而应面向本项目的 agent Turn 观测数据，固定展示 `thinking`、`text`、`tool call`、`tool result` 四个槽位。

## Goals / Non-Goals

**Goals:**

- 在主 Viewer 中提供 turn-level diff，用于比较当前 Turn 与前一个可比较 Turn 的可读变化。
- 在选中 Turn/Step 的详情操作区提供 `Diff with Prev` 按钮，并通过弹层展示当前 Turn 与 baseline Turn 的结构化差异。
- 将左侧 `Diff` 页面升级为当前 session 的 turn diff 入口/总览，而不是 task 文件列表。
- 在 diff 弹层中固定展示 `thinking`、`text`、`tool call`、`tool result` 四个槽位，帮助用户稳定阅读相邻 Turn 的核心差异。
- 对修改内容提供左右 `OLD` / `NEW` side-by-side 对照和行级高亮，新增/删除内容提供明显 badge 和边框，无变化内容保持普通样式。
- 保证四个槽位的完整内容可读；长内容使用块内滚动或展开，不以省略号或截断作为最终展示。
- 保持 diff 模型为前端 view projection，不修改底层 raw entries、minimal Turns、Task Trace Overlay 或 Dataset 输出。
- 不依赖 task segmentation；没有 task 结果时仍可使用 turn diff。

**Non-Goals:**

- 不实现 `req-resp.html` 的 network messages diff 改造。
- 不把 Dataset `changes` / `patches` 移植为主 Viewer 的数据源。
- 不新增后端 API、不读取当前仓库 `git diff`、不在第一版生成完整文件级 patch viewer。
- 不要求 diff 覆盖所有 raw JSON 字段；第一版只覆盖 `thinking`、`text`、`tool call`、`tool result`。
- 不在默认 diff 中展示 metadata、parameters、system prompt、commands、files、errors 等字段；这些内容保留在原始 JSON / debug 视图中查看。
- 不要求把 diff 弹层实现为与 `claude-tap` 完全相同的代码或视觉样式；参考其交互结构和可读性原则。

## Decisions

1. **直接在 Viewer 前端构建 `TurnDiffModel`，不复用 Dataset builder**

   - 选择：基于 `allEntries`、Conversation/minimal Turn 和当前 view projection，在 `viewer/claude-log.html` 中派生 diff model。
   - 理由：turn diff 是阅读/调试 UI，必须无需保存 Dataset、无需 task segmentation、无需后端导出。
   - 替代方案：从 `ccwhat/task_dataset/change_evidence.py` 或 Dataset trace 中取 `changes/patches`。该方案粒度是 task，字段偏文件改动，不覆盖 `text`、`thinking`、`tool_result`，并会把观测功能绑到导出链路上。

2. **比较相邻可比较 Turn，而不是比较 task 或 session 汇总**

   - 选择：默认将当前 Turn 与同一 session 顺序中的前一个 visible/comparable Turn 比较；调试视图中可比较完整 minimal Turn，默认视图中比较当前 Step 的 underlying Turn。
   - 理由：用户在观测时的心智是“这一轮比上一轮多了什么”，而不是“这个 task 最终改了哪些文件”。
   - 替代方案：按 task 聚合 diff。该方案会丢失 turn 顺序和即时变化，不适合作为 Session 观测入口。

3. **使用固定四槽位 projection，而不是 raw JSON deep diff**

   - 选择：先把 Turn 归一为稳定槽位：`thinking`、`text`、`tool call`、`tool result`，再做槽位级和行级 diff。每个槽位在 modal 中始终出现，空值显示 `(无)` 或等价空态。
   - 理由：raw JSON deep diff 噪声大、adapter 差异多，容易把 metadata、parameters、system prompt 等内部字段变化展示给用户；固定四槽位更符合阅读目标，也让每次打开 diff 的版式稳定。
   - 替代方案：完整 JSON diff。保留为未来 debug 增强，不作为第一版默认体验。

4. **采用 `Diff with Prev` 弹层，而不是常驻详情区 diff**

   - 选择：在 Turn/Step 详情操作区放置 `Diff with Prev` 按钮，点击打开 modal。modal 顶部提供 current/baseline label、prev/next diff pair 导航、baseline selector 和关闭按钮；正文按固定四槽位渲染。
   - 理由：diff 内容可能很长，弹层能提供足够宽度和滚动空间；用户平时浏览 Turn 时不会被 diff 常驻内容打断；左右对照需要比右侧详情栏更宽的布局。
   - 替代方案：在 Turn 详情中常驻 `Turn Diff` 区块或 tab。该方案空间不足，也会让每次选中 Turn 的详情过重。

5. **左侧 `Diff` 页面作为 diff 入口/索引，而不是主要阅读面板**

   - 选择：`Diff` 页面列出可比较 Turn diff 条目，点击后打开同一 modal 或跳转到对应 Turn 后打开 modal。
   - 理由：主要阅读体验应集中在 modal，避免左侧页面和 Turn 详情实现两套 diff 阅读布局。
   - 替代方案：`Diff` 页面直接渲染全部 diff。该方案在 session 较长时过重，且不如 modal 适合逐个比较。

6. **借鉴 `claude-tap` 的 baseline 匹配和手动选择思路**

   - 选择：默认 baseline 使用前一个 comparable Turn，同时提供 manual baseline selector，使用户可以在默认匹配不理想时选择更合适的 previous Turn。
   - 理由：实际 agent trace 可能存在 subagent、并发、隐藏 internal Turn、默认视图过滤等情况，单纯“上一条”可能不总是最有意义。
   - 替代方案：只允许固定 previous Turn。实现简单但可解释性和修正能力较弱。

## Risks / Trade-offs

- [Risk] 固定四槽位 projection 可能遗漏某些 adapter 特有字段。  
  Mitigation: 第一版有意只覆盖核心阅读字段，并在 raw JSON 中保留完整数据；后续可为特定 adapter 增加 projection handler，但默认 diff 不扩大到 metadata 噪声。

- [Risk] 文本 diff 太细会影响可读性和性能。  
  Mitigation: 第一版采用行级 side-by-side diff 和必要的行内高亮，并对长块设置块内滚动或展开；避免对整个 raw JSON 做昂贵字符级 diff。

- [Risk] 不允许截断可能导致内容块很高。  
  Mitigation: 每个槽位内容块应有清晰的最大高度和独立滚动，保证内容完整可读但不撑爆 modal。

- [Risk] 默认视图隐藏 internal Turn 后，用户可能不理解比较对象。  
  Mitigation: modal header 显示当前 Turn 和 baseline Turn 的 label/kind；baseline selector 展示可选 previous Turn；必要时显示 fallback/提示。

- [Risk] 弹层在移动端或窄屏可能难以展示左右对照。  
  Mitigation: modal 应可滚动；窄屏可将 side-by-side 降级为上下堆叠或横向滚动，关闭按钮和主要内容保持可访问。

## Migration Plan

- 在前端新增 turn diff projection、baseline 选择和 modal renderer，保持底层数据不可变。
- 在 Turn/Step 详情操作区新增 `Diff with Prev` 按钮，并实现无 baseline 时的反馈。
- 将现有左侧 `Diff` 页面的文件汇总实现替换为 turn diff 入口/索引。
- 增加静态/DOM 测试，验证 Diff modal、固定四槽位、行级高亮、完整内容滚动、baseline selector、prev/next 导航，以及不依赖 task segmentation 或 Dataset。
- 回滚时可移除 turn diff renderer，并恢复 `Diff` 页面占位或文件汇总；无需数据迁移。
