### Requirement: web-server 启动后自动打开浏览器
`web-server` 命令就绪后 SHALL 自动在系统默认浏览器中打开 `claude-log.html` 页面。

#### Scenario: 服务器就绪后打开浏览器
- **WHEN** `web-server` 命令成功绑定端口并开始监听
- **THEN** 系统默认浏览器自动打开 `http://127.0.0.1:<port>/claude-log.html`

#### Scenario: 无桌面环境时不中断服务
- **WHEN** 在无桌面环境（如 headless server）中运行 `web-server`
- **THEN** 浏览器打开失败被静默忽略，服务器正常继续运行
