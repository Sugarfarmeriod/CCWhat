# 🔬 codelenagent（see see what）

[English](README.en.md) | 中文

当前版本：`v2.2.2` · [更新日志](CHANGELOG.md)

**你的 AI 又嘴硬了？see see what！看看他在做什么。**

---

## 😤 你肯定遇到过这种事

- 让 Claude Code 往东，它偏要往西，还自己发明一个新方向  
- 让它“参考这个文档”，它秒回“好的我已经参考了”，实际上连文件都没打开  
- 你追问：“你真看了吗？”它理直气壮：“看了。”  
- 你翻遍终端日志，也抓不到它“偷懒”的实锤，一肚子火  

**别再被 AI 当傻子糊弄了。Let me see see what！**  

---

## ❓ codelenagent 是什么

codelenagent（读作”see see what”）  
它只做一件事：

> **把你 AI 干活时的所有“小动作”录下来，放到网页里让你实时围观。**

- 它调用了什么工具  
- 它读了哪个文件（或者假装读了其实没读）  
- 它执行了什么命令，输出是什么  
- 它是真的“参考了文档”，还是张口就来  

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

直接把这个链接丢给你的 Claude Code / Codex CLI / 任何 OpenClaw 套壳工具，说一句：

> “帮我装好 codelenagent”

它自己就会装好，全程不用你动手。
（这也算帮 AI 戴上一个”诚实手环”）

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
- Discovery 模式只记录动作类型，不保存具体内容，适合“先看看它老不老实”

---

## 🛠️ 常用命令

```bash
ccwhat setup                   # 修改录制配置
ccwhat web                     # 再次打开“显微镜”
ccwhat discover -- claude      # 探路模式：只记录动作，不偷看数据
ccwhat discover -- codex       # Codex 也可以探路
ccwhat run --no-web -- claude  # 低调运行，不自动弹网页
ccwhat export --list           # 看看都录了哪些“刑侦卷宗”
ccwhat export <session>        # 导出某个 session
ccwhat import <archive> --open # 还原别人的 session，一起破案
```

---

## 🧬 还有更多功能在赶来的路上

这个项目正在疯狂迭代，欢迎提意见、提 PR、疯狂转发。

- **有想法？** 开 Issue，哪怕只骂一句“这功能怎么还没有”也行
- **会写代码？** 直接 PR
- **觉得有点意思？** 点个 Star ⭐，成为这个项目的精神股东！
