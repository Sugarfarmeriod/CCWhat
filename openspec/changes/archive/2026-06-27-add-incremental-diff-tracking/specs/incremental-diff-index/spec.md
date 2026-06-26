## ADDED Requirements

### Requirement: CCWhatIndex 提供隔离的 git staging area
系统 SHALL 通过 GIT_INDEX_FILE 环境变量创建独立的 git index，不污染主工作区。

#### Scenario: 初始化 CCWhatIndex
- **WHEN** 调用 `CCWhatIndex.init(workspace, index_path=".git/index.ccwhat")`
- **THEN** 系统 SHALL 创建空的 git index 文件
- **AND** 主 `.git/index` SHALL 不受影响

#### Scenario: 添加文件到隔离 index
- **WHEN** 调用 `CCWhatIndex.add(file_path)`
- **THEN** 文件 SHALL 被添加到备用 index
- **AND** `git status` SHALL 不显示该文件为 staged
- **AND** `GIT_INDEX_FILE=.git/index.ccwhat git status` SHALL 显示该文件为 staged

### Requirement: CCWhatIndex 支持生成 diff
系统 SHALL 基于备用 index 生成 diff，对比 HEAD。

#### Scenario: 生成完整 diff
- **WHEN** 调用 `CCWhatIndex.diff(base_commit="HEAD")`
- **THEN** 系统 SHALL 返回统一格式的 diff 字符串
- **AND** diff SHALL 包含所有已添加到备用 index 的变更

#### Scenario: 删除文件追踪
- **WHEN** 调用 `CCWhatIndex.remove(file_path)`
- **THEN** 文件 SHALL 从备用 index 中标记为删除
- **AND** 后续 diff SHALL 显示该文件被删除

### Requirement: CCWhatIndex 支持单步 diff
系统 SHALL 支持生成两次 add 之间的增量 diff。

#### Scenario: 生成单步 diff
- **WHEN** 调用 `CCWhatIndex.diff_step(prev_commit_or_ref)`
- **THEN** 系统 SHALL 返回自 prev_ref 以来的变更 diff
