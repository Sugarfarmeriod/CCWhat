### Requirement: 长字符串节点 hover 显示格式化按钮
JSON tree 中，字符串值长度 ≥ 80 字符的叶子节点，鼠标悬停时 SHALL 显示一个格式化按钮。

#### Scenario: 短字符串不显示按钮
- **WHEN** 字符串值长度 < 80 字符
- **THEN** 不渲染格式化按钮，hover 行为与普通文本相同

#### Scenario: 长字符串 hover 显示按钮
- **WHEN** 字符串值长度 ≥ 80 字符，用户鼠标悬停在该节点行上
- **THEN** 格式化按钮变为可见

#### Scenario: 鼠标移开按钮隐藏
- **WHEN** 用户鼠标离开节点行
- **THEN** 格式化按钮恢复隐藏

### Requirement: 点击格式化按钮弹出浮层
点击格式化按钮 SHALL 弹出全屏遮罩浮层，展示格式化后的内容。

#### Scenario: 内容为合法 JSON 时展示 JSON 树
- **WHEN** 字符串内容能被 JSON.parse 成功解析
- **THEN** 浮层标题显示"JSON"，内容区展示可折叠的 JSON tree（默认展开 2 级）

#### Scenario: 内容非 JSON 时展示 Markdown
- **WHEN** 字符串内容不能被 JSON.parse 解析
- **THEN** 浮层标题显示"Markdown"，内容区展示 Markdown 渲染结果

#### Scenario: 点击遮罩背景关闭浮层
- **WHEN** 用户点击浮层外部遮罩区域
- **THEN** 浮层关闭

#### Scenario: 按 Esc 键关闭浮层
- **WHEN** 浮层打开时用户按下 Esc 键
- **THEN** 浮层关闭
