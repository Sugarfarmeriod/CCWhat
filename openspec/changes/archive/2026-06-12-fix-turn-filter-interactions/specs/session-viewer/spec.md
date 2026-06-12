## ADDED Requirements

### Requirement: Turn-first Session type filter affects visible Turn content
Claude Log Viewer 的 Turn-first `Session` 页面 SHALL 将顶部 `user / assistant / system / attachment / perm / fhs / queue / other` 作为 Turn 内 event 的类型筛选器，并让筛选结果反映到 Turn 卡片和 Turn detail 的可见内容中。

#### Scenario: 筛选 user 后只显示用户内容
- **WHEN** 用户在 `Session` 页面只启用 `user` 类型筛选
- **THEN** Turn detail SHALL 展示当前 Turn 中可见的用户消息
- **AND** Turn detail SHALL NOT 展示被筛选隐藏的助手回复正文
- **AND** Turn detail SHALL 显示隐藏事件数量提示

#### Scenario: 筛选 assistant 后只显示助手内容
- **WHEN** 用户在 `Session` 页面只启用 `assistant` 类型筛选
- **THEN** Turn detail SHALL 展示当前 Turn 中可见的助手回复和 assistant tool_use 内容
- **AND** Turn detail SHALL NOT 展示被筛选隐藏的用户消息正文
- **AND** Turn card 的可见 entry/tool/error 计数 SHALL 使用筛选后的 entries 计算

#### Scenario: 全部类型取消后保留 Turn 结构
- **WHEN** 用户取消所有类型筛选
- **THEN** `Session` 页面 SHALL 继续显示 Turn card 列表
- **AND** 选中 Turn 的 detail SHALL 显示当前筛选隐藏了该 Turn 全部事件的提示
- **AND** Turn detail SHALL NOT 展示未筛选的用户消息、助手回复、工具调用或错误正文

#### Scenario: 筛选不改变 Turn 编号
- **WHEN** 用户切换任意类型筛选组合
- **THEN** Turn label 和 turnKey SHALL 保持稳定
- **AND** 页面 SHALL NOT 因筛选而重新切分或重新编号 Turn

#### Scenario: Raw JSON 保留完整调试数据
- **WHEN** Turn detail 受类型筛选影响隐藏部分 entries
- **THEN** 折叠 Raw JSON 区块 MAY 保留完整 Turn entries
- **AND** Raw JSON SHALL 位于折叠区，不作为筛选后的主内容展示
