## MODIFIED Requirements

### Requirement: import 命令解压诊断包并导入本机
`deep-ai-analysis import <file_or_dir>` SHALL 解压诊断包，将数据写入用户可见的 `~/Downloads/deep-ai-analysis-imports/` 目录，接收方可在任意路径执行此命令。

#### Scenario: 成功导入新的多 session tar.gz 文件
- **WHEN** 用户执行 `deep-ai-analysis import /任意路径/export-xxx.tar.gz`
- **THEN** 包内每个 session 的数据都写入 `~/Downloads/deep-ai-analysis-imports/<projectDir>/<sessionId>.jsonl`
- **AND** 每个 session 的原始请求响应写入 `~/Downloads/deep-ai-analysis-imports/raw-req-resp/<sessionId>/`
- **AND** 终端输出导入成功的 session 数量和存储根路径

#### Scenario: 成功导入已解压的多 session 目录
- **WHEN** 用户执行 `deep-ai-analysis import ./deep-ai-analysis-export/`
- **THEN** 目录中的所有 session 都被导入到 `~/Downloads/deep-ai-analysis-imports/`

#### Scenario: 兼容导入旧单 session 包
- **WHEN** 用户传入旧格式单 session 导出包
- **THEN** 该 session 仍可被成功导入
- **AND** 输出导入成功提示，不要求用户手动迁移包结构

#### Scenario: manifest.json 不存在时报错
- **WHEN** 用户传入的文件/目录不包含 manifest.json
- **THEN** 命令以非零退出码退出
- **AND** 输出错误信息，提示这不是一个有效的诊断包

### Requirement: --open 选项自动打开浏览器查看
`import` 命令支持 `--open` 选项，导入完成后 SHALL 自动启动 web-server 并在浏览器中打开对应查看页面。

#### Scenario: --open 触发 web-server 并打开浏览器
- **WHEN** 用户执行 `deep-ai-analysis import /任意路径/export-xxx.tar.gz --open`
- **THEN** 导入完成后启动新 web-server，projects-dir 指向 `~/Downloads/deep-ai-analysis-imports/`
- **AND** 若默认端口 7789 已被占用，自动寻找下一个空闲端口（7790、7791…）
- **AND** 默认浏览器打开 `http://127.0.0.1:<端口>/claude-log.html`

### Requirement: 重复导入目标 session 时提示覆盖确认
若目标目录已存在，import SHALL 提示用户确认是否覆盖。

#### Scenario: 多 session 包中存在已导入目标时询问用户
- **WHEN** 包内任意一个 session 的目标文件已存在且未传 `--force`
- **THEN** 命令输出提示并询问是否覆盖现有导入结果
- **AND** 用户确认后继续导入包内所有 session，拒绝则退出且不修改现有数据
