# Release checklist

## Prerequisites

Install dev dependencies (includes pytest, build, twine):

```bash
pip install -e ".[dev]"
```

- PyPI account with API token configured

## Steps

0. **Remove legacy tracked files** (first release only)
   ```bash
   git rm -r --cached deep_ai_analysis/ deep_ai_analysis.egg-info/ dist/ sample_data/ 2>/dev/null || true
   git commit -m "chore: remove legacy deep_ai_analysis package from tracking"
   ```

1. **Bump version** in `pyproject.toml` and `ccwhat/__init__.py`

2. **Update `CHANGELOG.md`** with the user-facing highlights for this version

3. **Run pre-release safety scan** (fails on tokens, internal domains, legacy tracked files)
   ```bash
   python scripts/check-release-safety.py
   ```

4. **Run tests**
   ```bash
   # With pytest (requires dev dependencies):
   python -m pytest tests/ -v
   # Or without pytest:
   python -m unittest discover -v tests/
   ```

5. **Build**
   ```bash
   python -m build
   ```
   Produces `dist/ccwhat-<version>-py3-none-any.whl` and `dist/ccwhat-<version>.tar.gz`

6. **Inspect built wheel** (confirm no legacy packages)
   ```bash
   python - <<'PY'
   import zipfile, glob, sys
   wheels = glob.glob("dist/ccwhat-*.whl")
   if not wheels:
       print("ERROR: no wheel found in dist/"); sys.exit(1)
   bad = []
   for w in wheels:
       with zipfile.ZipFile(w) as zf:
           bad += [n for n in zf.namelist()
                   if n.startswith(("deep_ai_analysis", "sample_data"))]
   if bad:
       print("FAIL — legacy paths in wheel:"); [print(" ", p) for p in bad]; sys.exit(1)
   print(f"OK — wheel contents are clean ({wheels[0]})")
   PY
   ```

7. **Upload to PyPI**
   ```bash
   twine upload dist/ccwhat-<version>*
   ```

8. **Create GitHub Release**
   - Tag: `v<version>`
   - Attach the `.whl` and `.tar.gz` from `dist/`
   - Copy relevant CHANGELOG entries into the release notes

9. **Verify install**
   ```bash
   pip install ccwhat==<version>
   ccwhat --version
   ```
