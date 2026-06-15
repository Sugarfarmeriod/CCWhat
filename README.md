# 🔬 codelenagent（see see what）

中文 | [English](README.en.md)

当前版本：`v2.0.0 preview` · [更新日志](CHANGELOG.md)

## 当前版本状态

### v2.0.0 preview — Task Dataset Builder：数据标准化

从 Agent Session 中切分出的 Task 被清洗为标准 Dataset 格式，核心是四层结构：

```text
ccwhat-dataset/
├── manifest.json        # 数据集元信息
├── dataset.jsonl        # 任务定义索引，每行一个 task
├── traces/              # task 执行过程详情
│   ├── trace-task-001.json
│   └── trace-task-002.json
└── scores.jsonl         # 评分占位，第一版为空
```

- **`dataset.jsonl`**：只存任务定义，`id`、`input.instruction`、`input.repo`、`expected.success_criteria`、`metadata.agent/session_id/task_source/trace_path` 等。
- **`traces/*.json`**：存完整执行过程，events、commands、files.read/changed、changes、patches、errors、final_claim、repo_state。
- **`scores.jsonl`**：第一版为空，留给后续 evaluator 追加。
- **`manifest.json`**：schema_version、tool、session、counts 等。

Dataset 可保存到 `~/.ccwhat/datasets/` 本地 Registry，也可导出为 `dataset-*.tar.gz` 压缩包。格式由 Dataset validator 自动校验。

### v1.0.0 — Session Trace 双视图 + 自动任务切分闭环

- **Session Trace 双视图**：默认视图只展示主执行 Step（用户请求、思考过程、Agent 回复、工具调用/结果），调试视图展示完整 Turn 时间线（含 system/context/permission/snapshot/queue 等内部事件）。
- **自动任务切分**：从长 Session 中自动识别多个 Coding Task，切分后 Session Trace 自动切换为 `Task → 会话 → Step/Turn` 树形结构。
- **Turn Detail 完整证据**：右侧详情区展示当前选中 Turn 的完整 tool input/output、thinking 全文、internal event 结构化字段、可展开 raw JSON 和定位信息。
- **三 Agent 支持**：Claude Code（VS Code）、Codex、OpenCode 三类 Agent 的日志查看、任务切分、证据定位和分析报告完整覆盖。

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
