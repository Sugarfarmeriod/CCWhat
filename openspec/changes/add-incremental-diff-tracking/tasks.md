## 1. CCWhatIndex 类实现

- [x] 1.1 创建 `ccwhat/runtime/index.py` 模块
- [x] 1.2 实现 `CCWhatIndex.__init__(workspace, index_path)`
- [x] 1.3 实现 `CCWhatIndex.init()` - 初始化空 index
- [x] 1.4 实现 `CCWhatIndex.add(file_path)` - 添加文件到备用 index
- [x] 1.5 实现 `CCWhatIndex.remove(file_path)` - 从备用 index 删除文件
- [x] 1.6 实现 `CCWhatIndex.diff(base_commit="HEAD")` - 生成完整 diff
- [x] 1.7 实现 `CCWhatIndex.diff_step(prev_ref)` - 生成单步 diff
- [x] 1.8 编写 `CCWhatIndex` 单元测试

## 2. StepDiff 数据模型

- [x] 2.1 创建 `ccwhat/runtime/models.py` 模块
- [x] 2.2 定义 `StepDiff` dataclass（step_index, timestamp, tool_name, file_path, diff）
- [x] 2.3 定义 `StepDiffBuffer` 类管理 diff 累积

## 3. TaskStaging 集成

- [x] 3.1 修改 `TaskStaging.__init__` - 初始化 `CCWhatIndex`
- [x] 3.2 实现 `TaskStaging.record_step(tool_name, file_path)`
- [x] 3.3 修改 `TaskStaging.finish_task` - 写入 diff.patch
- [x] 3.4 更新 `task.json` paths.diff 和 evidence_availability.diff

## 4. diff.patch 格式实现

- [x] 4.1 实现 diff 注释头生成（step_index, timestamp, tool_name, file_path）
- [x] 4.2 实现多步 diff 追加逻辑
- [x] 4.3 验证 diff.patch 格式符合规范

## 5. 测试与验证

- [x] 5.1 测试 `CCWhatIndex` - 隔离性、add/diff/remove
- [x] 5.2 测试 `record_step` - 单步 diff 记录（间接测试）
- [x] 5.3 测试 `finish_task` - diff.patch 生成（间接测试）
- [x] 5.4 测试完整流程 - 多步操作累积 diff（需阶段三 Hook 集成）
- [x] 5.5 验证主 git 工作区不受污染
- [x] 5.6 运行全部测试确保无回归（50 passed）

## 6. 代码审查与文档

- [x] 6.1 代码审查：确保错误处理完善（CCWhatIndexError、RuntimeTaskError）
- [x] 6.2 代码审查：确保资源清理（状态在 finish/abort 时清除）
- [x] 6.3 更新相关 docstring（已添加）
