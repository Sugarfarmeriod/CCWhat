# 🔬 codelenagent（see see what）

中文 | [English](README.en.md)

当前版本：`v2.1.2` · [更新日志](CHANGELOG.md)

## 当前版本状态

### v2.1.2 — 请求回放

- **回放历史请求**：抓包页面对含有真实用户消息的请求显示「🔁 回放」按钮，支持原文回放和改写后重新发送。核心用途是把某次 AI 请求单独拎出来，修改 prompt 再发一遍，直接验证 AI 响应质量或对比不同 prompt 的输出差异。
- **消息净化**：回放前自动剥离 `<system-reminder>` 等系统注入块，只保留用户实际输入内容。
- **自动注入认证**：后端从环境变量读取最新 `X-Client-Token`，解决录制 token 过期报 401 的问题。
- **零配置自动录制**：启动时自动读取 agent 本地配置文件提取 API domain，无需手动执行 `ccwhat setup`。

### v2.1.1 — Session 重命名

- **Session 重命名**：Viewer 顶部 title bar 直接显示 session 名称和时间范围。Codex / OpenCode session 支持内联重命名，直接写入各自原生 DB；Claude Code 标记为不支持。_由 [@tanzunsheng](https://github.com/tanzunsheng) 贡献。_

### v2.1.0 — Turn-Level Diff Viewer

- **`Diff with Prev` Modal**：在 Turn/Step 详情区一键打开相邻 Turn 结构对比弹层，9 个字段网格逐行展示，绿/红/橙色区分新增、删除、变更。支持上一组/下一组导航和手动 baseline 切换。
- **Diff 页面升级**：左侧 Diff 页面改为 Turn diff 总览，列出所有 primary Turn 的变化摘要，点击直接打开对比 Modal。

### v2.0.0 — Task Dataset Builder

- 从 Session 中切分出的 Task 清洗为标准 Dataset 格式：`manifest.json` + `dataset.jsonl` + `traces/*.json` + `scores.jsonl`。
- 支持保存到 `~/.ccwhat/datasets/` 本地 Registry 并导出 `dataset-*.tar.gz`，格式由 validator 自动校验。

---

## 😤 你肯定遇到过这种事

- 让 Claude Code 往东，它偏要往西，还自己发明一个新方向  
- 让它"参考这个文档"，它秒回"好的我已经参考了"，实际上连文件都没打开  
- 你追问："你真看了吗？"它理直气壮："看了。"  
- 你翻遍终端日志，也抓不到它"偷懒"的实锤，一肚子火  

**别再被 AI 当傻子糊弄了。Let me see see what！**  

---

## ❓ codelenagent 是什么

codelenagent只做一件事：

> **把你 AI 干活时的所有"小动作"录下来，放到网页里让你实时围观。**

- 它调用了什么工具  
- 它读了哪个文件（或者假装读了其实没读）  
- 它执行了什么命令，输出是什么  
- 它是真的"参考了文档"，还是张口就来  

**所有动作，尽收眼底。**

---

## 🚀 三秒上车

安装或更新：

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash
```

运行（注意空格，空格是灵魂）：

```bash
ccwhat -- claude
ccwhat -- codex
# 或者你自己的命令
ccwhat -- xx
```

卸载：

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash -s -- uninstall
```

*第一次运行会让你选要观察的 AI 环境，跟着提示走就行。*

---

## 🦥 极度懒人包

直接复制下面的话给 Claude Code / Codex CLI / 任何 OpenClaw 套壳工具：

> "按照readme的指示，帮我装好 codelenagent，链接是https://github.com/PacemakerG/CCWhat"

---

## 📺 现场直逼

启动后会自动打开一个网页查看器，Agent 的每一次操作都会实时跳出来。

不小心关了？重新打开：

```bash
ccwhat web
```
或者直接访问 `http://127.0.0.1:7789/claude-log.html`

---

## ⚠️ 注意事项

- 支持 macOS、Linux、WSL；Windows 原生暂时不支持（在搞了）
- 需要 Python 3.10+ 和 mitmproxy，安装脚本会自己查
- HTTPS 录制需要信任 mitmproxy 的 CA 证书（好比给 Agent 戴个监听耳机，你得先同意）
- Authorization、Cookie、API key 等敏感信息会被自动打码，不会让你社死
- 安装好后，如果你是Claude官方订阅请选择【1】，如果是中转模型或其他模型提供商请选择【2】并复制粘贴你的提供商的baseurl，模式【3】Discovery 暂不支持

---

## 🛠️ 常用命令

```bash
ccwhat setup                   # 修改录制配置
ccwhat web                     # 再次打开"显微镜"
ccwhat discover -- claude      # 探路模式：只记录动作，不偷看数据
ccwhat discover -- codex       # Codex 也可以探路
ccwhat run --no-web -- claude  # 低调运行，不自动弹网页
ccwhat export --list           # 看看都录了哪些"刑侦卷宗"
ccwhat export <session>        # 导出某个 session
ccwhat import <archive> --open # 还原别人的 session，一起破案
```

---

## 🤝 开发协作文档

想一起开发 CCWhat，可以先读这几份文档：

- [架构总览](docs/ARCHITECTURE.md)
- [多 Agent Log Adapter](docs/ADAPTERS.md)
- [Analyzer 报告生成协议](docs/ANALYZER.md)
- [贡献指南](docs/CONTRIBUTING.md)

---

## 🧬 还有更多功能在赶来的路上

这个项目正在疯狂迭代，欢迎提意见、提 PR、疯狂转发。

- **有想法？** 开 Issue，哪怕只骂一句"这功能怎么还没有"也行
- **会写代码？** 直接 PR
- **觉得有点意思？** 点个 Star ⭐，成为这个项目的精神股东！
