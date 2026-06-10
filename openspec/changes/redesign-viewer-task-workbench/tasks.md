## 1. 基础状态与导航模型

- [x] 1.1 盘点 `viewer/claude-log.html` 当前全局状态、session 加载、Raw Events 渲染、Task Segment 渲染、Req/Resp、Diff、Export 入口
- [x] 1.2 新增 workbench 状态：active view、active task、active task detail tab、active nav target、active scope
- [x] 1.3 建立 canonical navigation alias index，覆盖 `eventId`、`main:<line>`、`agent-<id>:<line>`、normalized event id、message id、uuid、tool use id
- [x] 1.4 为每个可导航 entry 标记稳定 `_idx`、`_gid`、`_turnKey`、`_turnRootIdx`
- [x] 1.5 增加解析 helper：task boundary / evidence / turn / file / command 能生成 canonical nav target
- [x] 1.6 增加不可定位状态与 debug alias 信息，避免导航失败时只显示 disabled 且无原因

## 2. App Shell 与全局上下文栏

- [x] 2.1 将页面重构为 App Shell：左侧一级导航、顶部 context bar、主工作区
- [x] 2.2 左侧导航按工作流分组展示 `Tasks`、`Overview`、`Timeline`、`Sessions`、`Raw Events`、`Req / Resp`、`Diff`、`Diagnostics`、`Export`、`Settings`
- [x] 2.3 默认 active view 设置为 `Tasks`，不再默认展示 Raw Events 日志树
- [x] 2.4 顶部 context bar 只保留 Agent、Project、Session、Search、Refresh
- [x] 2.5 将原顶栏中的具体功能动作迁移到对应页面内部
- [x] 2.6 保持桌面端开发者工具风格，避免营销页、大屏页或聊天软件式布局

## 3. Tasks 页面

- [x] 3.1 将现有 task segmentation 面板迁移为 `Tasks` 页面主内容
- [x] 3.2 实现 Task List + Task Detail 双栏布局
- [x] 3.3 Task card 展示 task id、title、task type、status、turn range、files changed、commands、tests、errors、confidence、boundary reason
- [x] 3.4 Task card 点击设置 active task，并稳定切换 Task Detail
- [x] 3.5 Task Detail 增加 `Overview`、`Evidence`、`Turns`、`Files & Diff`、`Commands`、`Raw` tabs 或等价区块
- [x] 3.6 `Agent 最终声明` 默认摘要展示，可展开全文，并明确不代表任务成功
- [x] 3.7 errors 默认展示短摘要和数量，长日志折叠展示原文
- [x] 3.8 Task Detail 中的 start/end/evidence/turn/file/command 链接使用 canonical nav target 跳转

## 4. Overview / Timeline / Sessions 页面

- [x] 4.1 `Overview` 展示当前 session 的 task 数、turn 数、tool calls、files changed、commands、tests、failed tests、failed tasks、ambiguous tasks、low confidence tasks
- [x] 4.2 `Overview` 展示 Task Timeline 或 Task Map，并支持点击定位到 task
- [x] 4.3 `Timeline` 提供当前 session 的 task timeline 视图；若暂未完整实现，必须显示清晰的开发中状态
- [x] 4.4 `Sessions` 提供当前项目 session 列表入口；若暂未完整实现，必须显示清晰的开发中状态

## 5. Evidence 页面迁移

- [x] 5.1 将原始 user turn 日志树迁移到 `Raw Events` 页面内部
- [x] 5.2 `Raw Events` 支持从 canonical nav target 展开并定位到 turn/entry
- [x] 5.3 `Diff` 页面支持 session scope 文件列表和 diff 预览
- [x] 5.4 `Diff` 页面在 active task 存在时支持 task scope 相关文件与 patch 摘要
- [x] 5.5 `Req / Resp` 页面保留当前请求响应查看能力入口，并支持 active message/request target 聚焦
- [x] 5.6 证据页面跳转后应保留当前 session scope 和 active task scope

## 6. Diagnostics / Export / Settings 页面

- [x] 6.1 `Diagnostics` 展示失败任务、低置信度边界、测试失败、重复工具调用、Agent 声明与证据不一致、不可定位事件等诊断项
- [x] 6.2 Diagnostic item 支持跳转到关联 task 或 evidence page
- [x] 6.3 `Export` 页面集中展示 Session、Task Trace、Raw Logs、Req / Resp、Diff、Dataset preview 导出选项
- [x] 6.4 Dataset 导出入口标记为 preview/experimental，不暗示完整 Dataset Builder 已实现
- [x] 6.5 `Settings` 保留工作台配置入口；若暂未完整实现，必须显示清晰的开发中状态

## 7. 样式与可用性

- [x] 7.1 参考 `/Users/elon-ge/Downloads/index.html` 的布局和视觉密度实现克制的开发者工具样式
- [x] 7.2 确保 paths、commands、errors、JSON、diff、request/response data 可控换行、截断、滚动或折叠
- [x] 7.3 确保主工作区在桌面宽度下不会出现文本重叠、按钮溢出或固定控件被内容撑开
- [x] 7.4 保持已有暗色/亮色主题或主题切换能力不回归

## 8. 测试与验证

- [x] 8.1 更新或新增前端静态测试，覆盖左侧导航结构、默认 `Tasks` 页面、顶部 context bar 内容
- [x] 8.2 更新或新增测试，覆盖 canonical navigation alias index 和 Claude line-based event id 映射
- [x] 8.3 更新或新增测试，覆盖 Codex/OpenCode/generic normalized event id 映射
- [x] 8.4 更新或新增测试，覆盖 Task card 切换、Task Detail tabs、final claim 摘要、errors 摘要
- [x] 8.5 更新或新增测试，覆盖 Raw Events / Diff / Diagnostics / Export 页面入口和 scope 保留
- [x] 8.6 运行 task segmentation、viewer、current-session analysis 相关测试
- [x] 8.7 抽取 `viewer/claude-log.html` 内脚本执行 `node --check`
- [x] 8.8 运行 `openspec validate redesign-viewer-task-workbench --strict`

## 9. 手动验收

- [ ] 9.1 启动本地 viewer server，打开至少一个 Claude Code session，验证默认进入 `Tasks`
- [ ] 9.2 打开至少一个 Codex 或 OpenCode session，验证 task start/end 能通过 normalized event id 定位到 Raw Events
- [ ] 9.3 验证 `Tasks`、`Overview`、`Raw Events`、`Diff`、`Diagnostics`、`Export` 之间切换不丢失当前 session 和 active task
- [ ] 9.4 验证 Task Detail 中的 Overview、Evidence、Turns、Files & Diff、Commands、Raw 都能展示真实数据或明确空状态
- [ ] 9.5 验证长 command、error、diff、JSON、req/resp 内容不会撑坏布局
- [ ] 9.6 对照 OpenDesign 原型确认布局方向一致，但以真实数据可用性为准
