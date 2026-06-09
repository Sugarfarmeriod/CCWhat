# 🔬 codelenagent（see see what）

中文 | [English](README.en.md)

当前版本：`v0.1.3` · [更新日志](CHANGELOG.md)

## 当前版本状态

`v0.1.3` 完成了 Codex 的完整适配。**现在 codelenagent 已全面支持三大主流 AI Coding Agent：Claude Code（VS Code）、Codex 和 OpenCode。** 日志查看、分析报告、时间轴、工具耗时统计、Agent 摘要等核心功能对三者均可用。

**你的 AI 又嘴硬了？see see what！看看他在做什么。**

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

## 🧬 还有更多功能在赶来的路上

这个项目正在疯狂迭代，欢迎提意见、提 PR、疯狂转发。

- **有想法？** 开 Issue，哪怕只骂一句"这功能怎么还没有"也行
- **会写代码？** 直接 PR
- **觉得有点意思？** 点个 Star ⭐，成为这个项目的精神股东！
