## 1. 端口诊断实现

- [x] 1.1 增加端口 bind probe 辅助逻辑，返回可用于错误提示的不可绑定原因
- [x] 1.2 在 `ccwhat -- <cli>` managed proxy 启动前接入 bind probe，保留已有 ccwhat proxy 复用语义
- [x] 1.3 在 `ccwhat proxy` 和 `ccwhat discover` 启动前接入同等诊断
- [x] 1.4 在 viewer 启动前接入同等诊断，并使用 `--web-port` 建议

## 2. 测试与验证

- [x] 2.1 为不可绑定端口补充单元测试，覆盖 `WinError 10013` 文案和换端口建议
- [x] 2.2 验证已有端口 listener 场景仍走原有复用或占用提示
- [x] 2.3 运行相关测试，确认本次变更关键路径通过
