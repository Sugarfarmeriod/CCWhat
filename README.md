# deep-ai-analysis

拦截并分析 AI 服务 HTTP/HTTPS 流量的 CLI 工具包。

## 环境要求

- Python 3.10+
- [mitmproxy](https://mitmproxy.org/)（通过 `brew install mitmproxy` 安装）

## 安装

### 一键安装脚本（推荐⭐️⭐️⭐️⭐️⭐️）

```bash
bash <(curl -s https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/install.sh)
```

或者手动下载后执行：

```bash
curl -O https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/install.sh
bash install.sh
```

### 从源码安装（开发模式）

```bash
git clone ssh://git@git.sankuai.com/~zhoukang04/deep-ai-analysis.git
cd deep-ai-analysis
pip install -e .
```

## 快速开始 ⭐️⭐️⭐️⭐️⭐️

```bash
# 终端 1 — 启动代理
deep-ai-analysis proxy

# 终端 2 — 通过代理启动 mc，开始 AI Coding
deep-ai-analysis start-mc

# 终端 3 — 打开浏览器查看 AI 工作内容
deep-ai-analysis web-server
```

## 数据导出

### 方式一：在 Viewer 页面点击导出（推荐）

启动 `web-server` 后，打开 `http://127.0.0.1:7789/claude-log.html`，加载任意 session 后，顶栏会出现「导出」按钮：

1. 点击「**导出**」
2. 在弹窗中确认 session 信息，填写或修改文件名
3. 点击「**选择位置并导出**」，在系统文件夹选择对话框中选择保存目录
4. 导出完成后弹窗显示「✓ 已导出」

### 方式二：命令行导出

```bash
# 查看当前可导出的 session
deep-ai-analysis export --list

# 导出指定 session
deep-ai-analysis export <session-id> -o /path/to/export.tar.gz
```

导出包结构：

```
<session_id>/
  claude-log.jsonl          # Claude Code 主日志
  subagents/                # Subagent 日志（如有）
  raw-req-resp/             # 原始请求响应（如有）
    YYYY-MM-DD.jsonl
```

## 命令说明

```bash
deep-ai-analysis --help
```
