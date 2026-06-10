## ADDED Requirements

### Requirement: import 命令解压诊断包并导入本机
`deep-ai-analysis import <file_or_dir>` SHALL 解压诊断包，将数据写入用户可见的 `~/Downloads/deep-ai-analysis-imports/` 目录，接收方可在任意路径执行此命令。

#### Scenario: 成功导入 tar.gz 文件
- **WHEN** 用户执行 `deep-ai-analysis import /任意路径/export-xxx.tar.gz`
- **THEN** 数据写入 `~/Downloads/deep-ai-analysis-imports/<projectDir>/<sessionId>.jsonl`
- **AND** 原始请求响应写入 `~/Downloads/deep-ai-analysis-imports/raw-req-resp/<sessionId>/`
- **AND** 终端输出导入成功的提示，包含 session ID 和存储路径

#### Scenario: 成功导入已解压的目录
- **WHEN** 用户执行 `deep-ai-analysis import ./deep-ai-analysis-export/`
- **THEN** 数据被导入到 `~/Downloads/deep-ai-analysis-imports/<projectDir>/<sessionId>.jsonl`

#### Scenario: manifest.json 不存在时报错
- **WHEN** 用户传入的文件/目录不包含 manifest.json
- **THEN** 命令以非零退出码退出
- **AND** 输出错误信息，提示这不是一个有效的诊断包

### Requirement: --open 选项自动打开浏览器查看
`import` 命令支持 `--open` 选项，导入完成后 SHALL 自动启动 web-server 并在浏览器中打开对应 session。

#### Scenario: --open 触发 web-server 并打开浏览器
- **WHEN** 用户执行 `deep-ai-analysis import /任意路径/export-xxx.tar.gz --open`
- **THEN** 导入完成后启动新 web-server，projects-dir 指向 `~/.deep-ai-analysis/imports/`
- **AND** 若默认端口 7789 已被占用，自动寻找下一个空闲端口（7790、7791…）
- **AND** 默认浏览器打开 `http://127.0.0.1:<端口>/claude-log.html`

### Requirement: 重复导入同一 session 时提示覆盖确认
若目标目录已存在，import SHALL 提示用户确认是否覆盖。

#### Scenario: 目标目录已存在时询问用户
- **WHEN** `~/Downloads/deep-ai-analysis-imports/<projectDir>/<sessionId>.jsonl` 已存在
- **THEN** 命令输出提示并询问是否覆盖
- **AND** 用户确认后继续，拒绝则退出且不修改现有数据
