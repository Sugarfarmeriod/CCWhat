## ADDED Requirements

### Requirement: 增量 diff 追踪记录每次文件修改
系统 SHALL 在每次文件修改后生成 diff 片段，关联到 tool_call。

#### Scenario: 记录 Write 操作产生的 diff
- **WHEN** Agent 执行 Write 操作创建新文件
- **AND** 调用 `record_step(tool_name="Write", file_path="src/app.py")`
- **THEN** diff.patch SHALL 追加该步骤的 diff
- **AND** diff SHALL 显示为新增文件

#### Scenario: 记录 Edit 操作产生的 diff
- **WHEN** Agent 执行 Edit 操作修改文件
- **AND** 调用 `record_step(tool_name="Edit", file_path="src/app.py")`
- **THEN** diff.patch SHALL 追加该步骤的 diff
- **AND** diff SHALL 显示为修改文件

#### Scenario: diff.patch 格式包含元数据注释
- **WHEN** 查看 diff.patch 文件
- **THEN** 每个 diff 块前 SHALL 有注释头
- **AND** 注释头 SHALL 包含 step_index、timestamp、tool_name、file_path

### Requirement: diff.patch 格式规范
系统 SHALL 生成标准统一 diff 格式，带 step 注释头。

#### Scenario: diff.patch 格式验证
- **WHEN** 查看生成的 diff.patch
- **THEN** 文件格式 SHALL 为：
  ```
  # Step N: Tool file_path
  # Timestamp: ISO8601
  diff --git a/file b/file
  ...
  ```
