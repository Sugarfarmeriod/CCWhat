# ccwhat

本地录制并查看 AI 编码 CLI 的流量。

[English](README.md) | 中文

## 快速开始

安装或更新：

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash
```

运行：

```bash
ccwhat -- claude
```

卸载：

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash -s -- uninstall
```

第一次运行会引导你选择要录制的模型 API 域名。Claude 直连用户选 Claude preset；网关或中转站用户填自己的域名；不确定就用 discovery。

## 它做什么

`ccwhat -- claude` 会启动本地代理，通过代理启动 Claude Code，只录制你确认过的域名/路径，并把日志保存在 `~/.ccwhat/`。

它也会自动在浏览器打开查看器。如果你关掉了网页，用下面命令重新打开：

```bash
ccwhat web
```

## 注意

- 支持 macOS、Linux 和 WSL；暂不支持 Windows 原生环境。
- 需要 Python 3.10+ 和 mitmproxy；安装脚本会检查。
- HTTPS 录制需要按提示信任 mitmproxy CA 证书。
- Authorization、Cookie、API key、token/secret/key 相关 header 会脱敏。
- Discovery 只保存元数据，不保存请求或响应 body。

## 常用命令

```bash
ccwhat setup              # 修改录制配置
ccwhat discover -- claude # 不保存 payload，探测 API 端点
ccwhat --no-web -- claude
ccwhat -- mc --code       # 启动任意 AI 编码 CLI
ccwhat export --list      # 查看已录制 session
ccwhat export <session>   # 导出 session
ccwhat import <archive> --open
```

兼容旧版 `deep-ai-analysis` 导出的包。
