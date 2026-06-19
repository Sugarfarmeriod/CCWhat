# 发布清单

## 前置准备

安装开发依赖（包含 pytest、build、twine）：

```bash
pip install -e ".[dev]"
```

同时确保已配置 PyPI 账号的 API Token。

---

## 发布步骤

### 第 0 步：移除旧版跟踪文件（仅首次发布需要）

```bash
git rm -r --cached deep_ai_analysis/ deep_ai_analysis.egg-info/ dist/ sample_data/ 2>/dev/null || true
git commit -m "chore: 从 git 跟踪中移除旧版 deep_ai_analysis 包"
```

### 第 1 步：升版本号

同时修改以下两处，保持一致：
- `pyproject.toml` 中的 `version = "x.y.z"`
- `agentlens/__init__.py` 中的 `__version__ = "x.y.z"`

### 第 2 步：更新 CHANGELOG

在 `CHANGELOG.md` 中补充本版本面向用户的重要变化。

### 第 3 步：运行发布安全扫描

检测是否有内部域名、私有路径、真实 Token、旧包名等泄漏：

```bash
python scripts/check-release-safety.py
```

扫描范围：所有已跟踪文件 + 未跟踪但不被 `.gitignore` 排除的文件（即所有会进入本次 commit 的内容）。

### 第 4 步：运行测试

```bash
# 使用 pytest（需要先安装 dev 依赖）：
python -m pytest tests/ -v

# 或不依赖 pytest：
python -m unittest discover -v tests/
```

### 第 5 步：构建

```bash
python -m build
```

产物：`dist/agentlens-<version>-py3-none-any.whl` 和 `dist/agentlens-<version>.tar.gz`

### 第 6 步：检查 wheel 内容

确认构建出的 wheel 里没有旧版包或样本数据：

```bash
python - <<'PY'
import zipfile, glob, sys
wheels = glob.glob("dist/agentlens-*.whl")
if not wheels:
    print("ERROR: dist/ 下没有找到 wheel"); sys.exit(1)
bad = []
for w in wheels:
    with zipfile.ZipFile(w) as zf:
        bad += [n for n in zf.namelist()
                if n.startswith(("deep_ai_analysis", "sample_data"))]
if bad:
    print("FAIL — wheel 中发现旧版路径:"); [print(" ", p) for p in bad]; sys.exit(1)
print(f"OK — wheel 内容干净（{wheels[0]}）")
PY
```

### 第 7 步：上传到 PyPI

```bash
twine upload dist/agentlens-<version>*
```

### 第 8 步：创建 GitHub Release

- 标签：`v<version>`（例如 `v0.2.0`）
- 附件：`dist/` 下的 `.whl` 和 `.tar.gz`
- Release Notes：复制 `CHANGELOG.md` 中对应版本的条目

### 第 9 步：验证安装

```bash
pip install agentlens==<version>
agentlens --version
agentlens --help
agentlens setup --preset claude --yes
agentlens run --help
```
