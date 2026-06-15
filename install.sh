#!/bin/bash
# ccwhat installer script
set -e

ACTION="${1:-install}"
OS_NAME="$(uname -s 2>/dev/null || echo unknown)"
CCWHAT_PACKAGE_URL="${CCWHAT_PACKAGE_URL:-git+https://github.com/PacemakerG/CCWhat.git}"
INSTALL_ROOT="${CCWHAT_INSTALL_ROOT:-$HOME/.ccwhat/app}"
VENV_DIR="$INSTALL_ROOT/venv"
BIN_DIR="${CCWHAT_BIN_DIR:-$HOME/.local/bin}"
WRAPPER_PATH="$BIN_DIR/ccwhat"

echo "=================================================="
echo "  ccwhat installer"
echo "=================================================="
echo ""

case "$OS_NAME" in
  Darwin|Linux) ;;
  MINGW*|MSYS*|CYGWIN*)
    echo "Windows native is not supported by this installer yet."
    echo "Use WSL, then run this command inside Linux."
    exit 1
    ;;
  *)
    echo "Unsupported OS: $OS_NAME"
    echo "Supported: macOS, Linux, WSL"
    exit 1
    ;;
esac

find_python() {
  for candidate in \
    "${PYTHON_BIN:-}" \
    python3.13 python3.12 python3.11 python3.10 python3 python
  do
    if [ -z "$candidate" ]; then
      continue
    fi
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3.10+ is required."
  if [ "$OS_NAME" = "Darwin" ]; then
    echo "Install it with: brew install python@3.11"
  else
    echo "Install Python 3.10+ with your system package manager."
  fi
  exit 1
fi

PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
echo "Python: $PYTHON_VERSION  ($PYTHON_BIN)"

if [ "$ACTION" = "uninstall" ]; then
  echo "Uninstalling ccwhat app environment..."
  rm -f "$WRAPPER_PATH"
  rm -rf "$INSTALL_ROOT"
  echo "Uninstall complete. Local logs/config are kept at ~/.ccwhat"
  exit 0
fi

if [ "$ACTION" != "install" ]; then
  echo "Unknown action: $ACTION"
  echo "Usage: install.sh [uninstall]"
  exit 1
fi

echo ""
echo "Creating isolated environment..."
mkdir -p "$INSTALL_ROOT" "$BIN_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

VENV_PY="$VENV_DIR/bin/python"
VENV_CCWHAT="$VENV_DIR/bin/ccwhat"
VENV_MITMDUMP="$VENV_DIR/bin/mitmdump"

echo ""
echo "Installing ccwhat and dependencies..."
"$VENV_PY" -m pip install --upgrade pip
"$VENV_PY" -m pip install --upgrade "$CCWHAT_PACKAGE_URL"

if [ ! -x "$VENV_CCWHAT" ]; then
  echo "Install failed: ccwhat executable was not created at $VENV_CCWHAT"
  exit 1
fi

if [ ! -x "$VENV_MITMDUMP" ]; then
  echo "Install failed: mitmdump executable was not created at $VENV_MITMDUMP"
  exit 1
fi

echo ""
echo "Writing launcher: $WRAPPER_PATH"
cat > "$WRAPPER_PATH" <<EOF
#!/bin/bash
export PATH="$VENV_DIR/bin:\$PATH"
exec "$VENV_CCWHAT" "\$@"
EOF
chmod +x "$WRAPPER_PATH"

echo ""
if command -v ccwhat >/dev/null 2>&1; then
  echo "Install complete! Run: ccwhat --help"
else
  echo "Install complete!"
  echo ""
  echo "Add this to your shell config if ccwhat is not found:"
  echo "  export PATH=\"$BIN_DIR:\$PATH\""
  echo ""
  echo "Then open a new shell and run: ccwhat --help"
fi
