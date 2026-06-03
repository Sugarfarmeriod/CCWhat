# Claude日志数据清洗

## 输入

1. claude session id，例如 f0ca6786-e6c4-4406-b6fc-33066b6775f1。
2. Claude目录，默认 ~/.claude
3. 开始时间
4. 结束时间

## 输出

树形json结构，表示Claude的处理过程。根节点是Main Session，一级子节点是Turn，表示一次用户输入后的所有处理步骤，二级子节点是Step，表示一个Claude处理步骤。

## 处理逻辑

### 1、读取并解析Claude日志jsonl文件

根据输入的Claude目录、sessionId，读取jsonl文件。
并补充原始行号字段`_fileLine`。

Claude日志目录结构与文件说明：

```
~/.claude/projects/
└── <project-slug>/                        # 项目目录，由工作路径转义而来（/ → -）
    ├── <sessionId>.jsonl                  # main agent 对话日志
    ├── <sessionId>/                       # 同名目录，存放该 session 的 subagent 数据
    │   └── subagents/
    │       ├── agent-<agentId>.jsonl      # subagent 对话日志（isSidechain: true）
    │       └── agent-<agentId>.meta.json  # subagent 元信息
    └── ...
```

**agentId 与文件名的对应关系**：subagent 文件名格式为 `agent-<agentId>.jsonl`，agentId 即去掉 `agent-` 前缀后的字符串。

### 2、日志过滤

1. 根据输入的开始时间和结束时间过滤日志。日志中的时间字段为`timestamp`,示例：`2026-05-21T01:43:59.904Z`。
2. 保留type为user和assistant的日志

## 原始日志排序

- 日志行号✅
- parentUuid和uuid的关系没有什么实质含义。且只有部分日志类型有：user、assistant、system、attachment。
- 时间戳主要用来展示。

❓❓❓或者按parentUuid和uuid的关系进行切分，然后展示DAG图？

## 切分

✅方案1：同一个promptId的user消息，第一条。注意：
1. 一种已知的情况是，bash结果回调，单独有个promptId。聚合在一起也合理
2. 可以正确处理自动压缩的user消息。

❌方案2：按用户真实输入切分。用户输入的定义是：
1. user类型的日志，
2. 且`origin.kind`字段不为 `task-notification` （这条规则要看下这个回调是否会往context里面放，已经对行为的影响是什么？）
3. 其他未知情况



## 关联关系

1. 原始HTTP请求响应和日志的关联:可以通过assistant日志的 message.id 字段 和 HTTP请求关联起来。但多条日志有可能关联到同一个原始请求、原始请求有可能关联不到日志，一种情况是请求小模型获取title，还有一种是compact
2. **tool调用和结果的关联**。assistant日志 message.content[].type=='tool_use' 时，message.content[].id 可以和 user message.content[].type==tool_result 的消息，通过message.content[].tool_use_id匹配上。
3. Main session和subagent的日志关联。assistant消息，类型为agent的 tool_use 消息 找到 user的tool_result消息, 再找agent即可定位到。
4. skill打标
   1. 打标。assistant 的 tool_use消息，且name=='Agent'。
   2. ❓❓❓卸载需要看http请求/上下文是否被实际压缩


## 日志类型

每行 JSON 的顶层 `type` 字段

| type                    | 说明　　　　　　　　　　　　　　　　　　　　　　　　　　　　 |
| -------------------------| --------------------------------------------------------------|
| `user`                  | 用户输入或工具执行结果回调　　　　　　　　　　　　　　　　　 |
| `assistant`             | AI 回复（含文字和工具调用）　　　　　　　　　　　　　　　　　|
| `system`                | 系统提示词　　　　　　　　　　　　　　　　　　　　　　　　　 |
| `attachment`            | attachment.type 字段记录了类型，需要保留用于通过uuid串联顺序 |
| `permission-mode`       | 权限模式设置，一般出现在日志首行　　　　　　　　　　　　　　 |
| `file-history-snapshot` | 文件快照元数据　　　　　　　　　　　　　　　　　　　　　　　 |
| `queue-operation`       | 当前正在处理其他任务，用户输入的消息会先入队列　　　　　　　 |
| `last-prompt`           | 用于在 /resume 会话列表　　　　　　　　　　　　　　　　　　　|

**user消息**

message.content字段一定有，可能是文本，可能是数组。

message.content为文本的示例：

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "继续"
  }
}
```

message.content为数组时，实际测试下来长度为1。数组内对象有两种类型, type为text和tool_result.
message.content[0].type==='text'的示例：

message.content[0].type==='text'时，message.content[0].content可以是str或者列表.
message.content[0].content为str的示例：

```json
{
    "type": "tool_result",
    "tool_use_id": "toolu_bdrk_01FFDhpUtNSWSyYTmD2ZNymK",
    "content": "Launching skill: finishing-a-development-branch"
}
```

message.content[0].content为数组的示例：
```json

[
    {
        "type": "text",
        "text": "massive messages."
    },
    {
        "type": "text",
        "text": "agentId: ab49d5098e41cad37 (use SendMessage with to: \"ab49d5098e41cad37\" to continue this agent)\n<usage>total_tokens: 141696\ntool_uses: 51\nduration_ms: 322780</usage>"
    }
]
```

**assistant消息**

实际测试的message.content都是list，长度为1。`message.type`都是`message`.

```json
{
"type": "assistant",

  "message": {
    "id": "msg_bdrk_01FydqXTkrQNPzmKc2dLqzfp",
    "type": "message",
    "role": "assistant",
    "model": "claude-sonnet-4-6",
    "content": [
      {
        "type": "text",
        "text": "需要看一下实际生成的 HTML 文件，找出乱码原因："
      }
    ]
  }
}
```


`message.content[0].type`为`text`或者`tool_use`。
`message.content[0].type`为`text`时，可直接使用`message.content[0].text`
`message.content[0].type`为`tool_use`的时候，有id（即tool_id）、type、name、input四个字段。
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_bdrk_01UJYCXbLKjPwMEigaGVpthr",
    "type": "message",
    "role": "assistant",
    "model": "claude-sonnet-4-6",
    "content": [
      {
        "type": "tool_use",
        "id": "toolu_bdrk_011va7YhRQr91Xb8MUXbdh3Z",
        "name": "Bash",
        "input": {
          "command": "python3 -m deep_ai_analysis.cli create-report --session-id 9fcdf91f-3cd3-41c2-9b4a-bdccc17b7025 --output /tmp/test-report.html 2>&1",
          "description": "Generate a test report"
        }
      }
    ]
    }
}

```

可以使用message.content[0].name处理不同的工具调用。不同工具调用的input字段内容不一样。

**通过message.id可以关联到同一个LLM请求。**

