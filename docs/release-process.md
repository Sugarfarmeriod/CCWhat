# 发布流程

本文档是每次发版时的操作手册。按顺序执行，不要跳步。

---

## 一、版本号规则

遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)：

```
v<MAJOR>.<MINOR>.<PATCH>

MAJOR  不兼容的 API 变更
MINOR  向后兼容的新功能
PATCH  向后兼容的 bug 修复
```

**示例**：`v2.3.2`

---

## 二、发布前：需要更新的文件清单

每次发版必须同步更新以下文件，缺一不可：

| 文件 | 更新内容 | 时机 |
|------|---------|------|
| `pyproject.toml` | `version` 字段 | 改版本号时 |
| `CHANGELOG.md` | 新增版本条目 | 写完所有改动后 |
| `README.md` | 顶部 Changelog 链接的版本号 + `v2 版本演进` 章节 | minor/major 发版 |

---

## 三、逐文件操作说明

### 3.1 `pyproject.toml` — 更新版本号

找到 `version` 字段，直接改数字：

```toml
[project]
name = "ccwhat"
version = "2.3.2"   # ← 改这里
```

改完后验证：

```bash
uv run ccwhat --version
# 应输出新版本号
```

---

### 3.2 `CHANGELOG.md` — 写新版本条目

在文件**最顶部**（现有内容之前）插入新条目，格式如下：

```markdown
## v<version> - <YYYY-MM-DD>

### <本次发布的主题标题，一句话>

一段话说明这次改动的背景或动机（可选，1-3 句）。

### 新增

- **`文件或功能名`**：做了什么

### 修复

- 修复了 XXX 在 YYY 时崩溃的问题（#issue编号）

### 改动

- `module.py`：调整了 XXX 行为

---
```

**格式规范**：
- 日期用 UTC 当天日期，格式 `YYYY-MM-DD`
- 每条条目加粗关键词，后跟冒号和说明
- 如果有关联 issue/PR，在行末加 `(#123)`
- 条目之间用 `---` 水平线分隔

---

### 3.3 `README.md` — 两处更新

**第一处：顶部 Changelog 链接**（第 21 行附近）

```markdown
<a href="./CHANGELOG.md">v2.3.2</a> ·
```

把版本号改成新版本号。

**第二处：`v2 版本演进` 章节**（仅 minor 及以上版本发版时更新）

规则：
- 把新 minor 版本加到最顶部，标注 `— 当前版本`
- 把上一个 minor 版本的 `— 当前版本` 标记去掉
- patch 版本（如 v2.3.1 → v2.3.2）不需要新增一行，在现有 minor 条目里补充即可

```markdown
## 📈 v2 版本演进

**v2.4** — 当前版本        ← 新加

- 新功能描述 1
- 新功能描述 2

**v2.3**                   ← 去掉"— 当前版本"标记

- ...
```

---

## 四、发布操作

### 4.1 本地验证

```bash
# 确认版本号一致
grep 'version' pyproject.toml
grep 'v2\.' README.md | head -5
head -5 CHANGELOG.md

# 跑测试
uv run python -m unittest
```

### 4.2 提交并打 Tag

```bash
git add pyproject.toml CHANGELOG.md README.md
git commit -m "chore: release v<version>"
git tag v<version>
git push origin main
git push origin v<version>
```

### 4.3 GitHub Release（可选）

在 GitHub 仓库页面 → Releases → Draft a new release：
- Tag：选刚打的 `v<version>`
- Title：`v<version> — <主题>`
- Body：直接粘贴 CHANGELOG.md 里对应条目的内容

---

## 五、接收 PR 时如何标记贡献者

### 5.1 Merge commit 里加 Co-authored-by

合并 PR 时，在 merge commit message 里加上共同作者行：

```
chore: merge PR #42 - add attribution diagnosis engine

Co-authored-by: 贡献者名字 <贡献者邮箱>
```

GitHub 识别 `Co-authored-by:` 格式后，会自动在 commit 页面和 contributor 列表里显示贡献者头像。

贡献者的邮箱获取方式：
- 对方的 GitHub profile → 公开邮箱
- 或用 `<username>@users.noreply.github.com`（GitHub 匿名邮箱，始终有效）

### 5.2 CHANGELOG.md 里注明

在对应版本条目的相关行末尾加 `by @username`：

```markdown
### 新增

- **归因诊断引擎**：消费 V2 Dataset 生成 diagnosis.json，by @contributor-name
```

如果贡献较大（整个功能模块），可以在条目末尾单独加一行：

```markdown
感谢 @contributor-name 贡献了本版本的 XXX 功能（#PR编号）。
```

### 5.3 操作顺序

```
1. 审核 PR，在 GitHub 页面 Review
2. 合并时选择 "Squash and merge" 或 "Create a merge commit"
3. 在 commit message 里加 Co-authored-by
4. 在 CHANGELOG.md 对应条目里加 by @username
5. 照常走发布流程（打 tag、push）
```

### 5.4 不需要做的事

- 不需要维护单独的 `CONTRIBUTORS.md`（GitHub 的 Contributors 页面自动统计）
- 不需要在 README 里加贡献者头像墙（除非项目到了需要这么做的规模）

---

## 六、发版前核对清单

发版前确认以下各项均已完成：

- `pyproject.toml` 的 version 已更新
- `CHANGELOG.md` 顶部已插入新版本条目，日期正确
- `README.md` 顶部链接版本号已更新
- `README.md` v2 版本演进章节已更新（minor/major 版本时）
- `uv run ccwhat --version` 输出正确
- 测试全部通过
- git tag 已打，已 push
- 如有 PR 贡献者，Co-authored-by 和 CHANGELOG 已注明
