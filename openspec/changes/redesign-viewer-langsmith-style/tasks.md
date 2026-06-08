## 1. Open Design 设计稿

- [x] 1.1 使用 Open Design 创建 CCWhat Viewer 的 LangSmith 风格设计 artifact
- [x] 1.2 在设计 prompt 中明确：对标 LangSmith 的深色观测工作台，不复制品牌资产，不做 landing page
- [x] 1.3 设计稿必须覆盖 Claude/Codex/OpenCode agent badge、project/session 选择、trace/turn/event 列表、详情区域、usage 区域和 Raw Req/Resp 入口
- [x] 1.4 将 Open Design preview URL 或 artifact 摘要提供给用户 review
- [x] 1.5 根据用户反馈确认当前设计稿可作为实现依据

## 2. Viewer 前端实现

- [x] 2.1 读取 Open Design artifact：project `71acf6a9-38cc-40b4-bb00-f7200b01cdf4` 的 `ccwhat-viewer.html`
- [x] 2.2 梳理 `viewer/claude-log.html` 当前布局、渲染函数和状态变量，标记必须保留的功能入口
- [x] 2.3 将设计稿中的左侧导航、顶部上下文操作栏、主 trace/turn/event 区和详情区映射到真实 Viewer
- [x] 2.4 更新 CSS 为 LangSmith 风格的深色、高密度、低圆角、细边框视觉系统
- [x] 2.5 保持 Claude Code `main/subagents` 的现有展示能力
- [x] 2.6 增强 Codex/OpenCode `events/turns/usage` 的展示，不退回到只显示 raw JSON
- [x] 2.7 增加 usage 展示区域，显示 token/cache 计数并避免无公式 cache hit rate
- [x] 2.8 保留搜索、类型过滤、导出、分析当前 Session、刷新和 Raw Req/Resp 跳转
- [x] 2.9 增强空状态和错误状态，避免无上下文的 failed to fetch

## 3. 验证

- [x] 3.1 运行现有测试，确认 export/import 和 adapter 相关测试不回退（190 passed）
- [ ] 3.2 手动验证 `ccwhat web --agent claude`
- [ ] 3.3 手动验证 `ccwhat web --agent codex`
- [ ] 3.4 手动验证 `ccwhat web --agent opencode`
- [ ] 3.5 手动验证 `ccwhat -- claude`、`ccwhat -- codex`、`ccwhat -- opencode` 的 Viewer agent 显示和日志加载
- [ ] 3.6 手动验证 Raw Req/Resp 页面仍可独立打开
- [ ] 3.7 用桌面和窄屏视口检查文字不重叠、控件不溢出、详情区可滚动

## 4. 文档和交付

- [ ] 4.1 如前端体验变化明显，更新 README 中的截图或说明入口
- [ ] 4.2 在 CHANGELOG 中记录 Viewer LangSmith 风格重设计
- [ ] 4.3 输出改动文件、支持的 agent、验证命令和后续可继续优化项
