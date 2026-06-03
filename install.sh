#!/bin/bash
set -e

WHL_URL="https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/deep_ai_analysis-0.1.4-py3-none-any.whl"

echo "=================================================="
echo "  deep-ai-analysis 安装程序"
echo "=================================================="
echo ""

# Python 版本检测
PYTHON_BIN=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON_BIN" ]; then
  echo "❌ 未找到 Python，请先安装 Python 3.10+"
  exit 1
fi
PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
echo "Python 版本：$PYTHON_VERSION  ($PYTHON_BIN)"

# 虚拟环境检测
if [ -n "$VIRTUAL_ENV" ]; then
  ENV_INFO="虚拟环境 (venv): $VIRTUAL_ENV"
elif [ -n "$CONDA_DEFAULT_ENV" ]; then
  ENV_INFO="Conda 环境: $CONDA_DEFAULT_ENV"
else
  ENV_INFO="系统 Python（未激活虚拟环境）"
fi
echo "当前环境：$ENV_INFO"

# pip 路径
PIP_BIN=$(command -v pip3 || command -v pip || echo "")
if [ -z "$PIP_BIN" ]; then
  echo "❌ 未找到 pip，请先安装 pip"
  exit 1
fi
echo "pip 路径：$PIP_BIN"

# mitmproxy 检测
if command -v mitmproxy &>/dev/null; then
  MITMPROXY_VERSION=$(mitmproxy --version 2>/dev/null | head -1)
  MITMPROXY_INFO="已安装 ($MITMPROXY_VERSION)"
else
  MITMPROXY_INFO="未安装，将通过 brew 安装"
fi
echo "mitmproxy：$MITMPROXY_INFO"

# brew 检测（仅在需要安装 mitmproxy 时）
if ! command -v mitmproxy &>/dev/null; then
  if ! command -v brew &>/dev/null; then
    echo ""
    echo "❌ 未找到 Homebrew，无法自动安装 mitmproxy。"
    echo "   请先安装 Homebrew：https://brew.sh"
    echo "   或手动安装 mitmproxy：pip install mitmproxy"
    exit 1
  fi
  BREW_INFO="$(brew --version | head -1)  ($(command -v brew))"
  echo "Homebrew：$BREW_INFO"
fi

echo ""
echo "将安装 deep-ai-analysis 到上述环境。"
echo ""
read -p "确认继续安装？[y/N] " CONFIRM
case "$CONFIRM" in
  [yY][eE][sS]|[yY])
    ;;
  *)
    echo "已取消安装。"
    exit 0
    ;;
esac

# 安装 mitmproxy
if ! command -v mitmproxy &>/dev/null; then
  echo ""
  echo "正在通过 brew 安装 mitmproxy..."
  brew install mitmproxy
fi

echo ""
echo "正在安装 deep-ai-analysis..."
echo "将通过 --user 方式安装 deep-ai-analysis 到当前用户的 Python 目录。"
if "$PIP_BIN" install --help 2>&1 | grep -q -- '--break-system-packages'; then
  "$PIP_BIN" install --user --break-system-packages "$WHL_URL"
else
  "$PIP_BIN" install --user "$WHL_URL"
fi

echo ""
if command -v deep-ai-analysis &>/dev/null; then
  echo "✅ 安装完成！运行 'deep-ai-analysis --help' 查看使用说明。"
else
  USER_BIN=$("$PYTHON_BIN" -m site --user-base 2>/dev/null)/bin
  echo "✅ 安装完成！"
  echo ""
  echo "⚠️  注意：'deep-ai-analysis' 命令暂时不在 PATH 中。"
  echo "   请将以下路径添加到你的 shell 配置文件（~/.zshrc 或 ~/.bash_profile）："
  echo ""
  echo "   export PATH=\"$USER_BIN:\$PATH\""
  echo ""
  echo "   添加后执行 source ~/.zshrc（或重新打开终端），再运行 'deep-ai-analysis --help'。"
fi
