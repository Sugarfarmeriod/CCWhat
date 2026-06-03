### Requirement: proxy 命令通过 mitmdump CLI 启动代理
`proxy` 子命令 SHALL 通过 `subprocess` 调用系统 `mitmdump` 命令启动代理，不使用 mitmproxy Python API。

#### Scenario: 正常启动
- **WHEN** 用户执行 `deep-ai-analysis proxy`
- **THEN** 系统调用 `mitmdump --listen-host 127.0.0.1 --listen-port 7788 -s <recorder.py路径>`，代理正常监听

#### Scenario: mitmdump 未安装时给出提示
- **WHEN** 系统中未安装 `mitmdump` 命令
- **THEN** 命令退出并提示用户执行 `brew install mitmproxy`

#### Scenario: 输出目录通过环境变量传递给 addon
- **WHEN** 用户指定 `--output /custom/path`
- **THEN** `DAA_OUTPUT_DIR` 环境变量设为该路径，`recorder.py` 从中读取输出目录

### Requirement: install.sh 通过 brew 安装 mitmproxy
`install.sh` SHALL 在安装 Python 包之前通过 `brew install mitmproxy` 安装 mitmproxy CLI。

#### Scenario: brew 可用时自动安装
- **WHEN** 系统中已安装 `brew`
- **THEN** 脚本执行 `brew install mitmproxy`，安装成功后继续安装 Python 包

#### Scenario: brew 不可用时给出提示
- **WHEN** 系统中未安装 `brew`
- **THEN** 脚本打印提示，跳过 mitmproxy 安装，继续安装 Python 包
