# AI Coding诊断

# 使用场景：用于分析AI输出结果不符合预期时的根因。

不知道为什么好，为什么不好，harness作用结果靠猜想。目前人工诊断主要靠对话完成。

## 场景一：知识库没有发挥作用
回答知识库什么时候被使用到、命中率、粒度是否合适。


## 场景二：context影响模型能力

context的结构、水位、污染情况会影响模型表现，需要采用不同策略管理context。

[Escaping the Dumbzone, Part 1: Why Your AI Gets Stupider the More You Talk to It](https://dev.to/diggidydale/escaping-the-dumbzone-part-1-why-your-ai-gets-stupider-the-more-you-talk-to-it-4d8k)

# 难点

## 难点一：影响AI输出的因素多，链路复杂，数据串联困难

以下几层因素都会影响AI输出的结果：
- AI Coding框架（元析、openspec、superpowers、Spec Kit）的设计
- 使用的AI coding工具（Claude、Codex）的功能、机制
- 用的底层LLM模型能力、交互协议有差异

## 难点二：原始数据量大
- 人工分析困难
- 直接用AI分析同样面临上下文太大导致的降智问题


# 概要设计

整体分为三个环节
1. 分层记录全量数据，通过sessionId、toolId等关键信息串联原始请求、工具日志、框架日志。
1. 问题发现。
   - 自动发现为主，用户主动触发为辅。
   - 通过原始数据找模式，通过模式写规则发现问题。
2. 根因定位。以知识库的使用和上下文水位问题开始试验。
   - 逐级进行数据清洗
   - 针对问题，渐进披露信息诊断根因
3. 反向驱动流程优化


# 详细设计

## 分层记录全量数据

### HTTP请求层
使用类似ccwhat的方案，代理请求和返回，记录全量数据。
ccwhat已经支持的功能：
- 代理http请求，记录每次http请求和返回
- **将原始请求返回内容按turn、session、project向上汇总**。按用户输入message分隔turn，每个turn保留message列表最长的请求和响应；按用户第一条message的hash分隔session；project取system字段的工作目录。
- **main agent和subagent内容关联**。检测到 Agent tool_use 时，记录 prompt 的 MD5 → 父 session 映射；当新请求的第一条消息 hash 命中已知 agent prompt，则自动关联 parent_session_id。
- 可视化界面。支持cache使用情况计算，从原始response中的usage字段取值。
- 监控team agents变化
- 简单的cache、session分析，通过claude运行prompt实现。

需要新增功能：
1. 支持存储原始请求和响应内容到后端，相较于现在的方案，需要解决：
   1. 不同用户的数据隔离。
   2. 原始数据已经被清洗过一轮。
2. 原始请求间的变化抽取。例如：
   1. **单turn内的context变化分析**，用于context压缩分析。
   2. skill使用情况。

方式：
- fork ccwhat。
- 和ccwhat 开发同学共建功能。

### AI Coding工具内部的数据、状态变化
例如context压缩、Agent创建、Skill触发、文件的读写。

数据来源：
1. 工具自身存储的日志 `~/.claude/projects`。**日志内有sessionId、promptId、uuid、messageid等字段可以关联。**
   1. 读取、解析。
   2. 可视化展示（Cluade Code History Viewer）
2. 使用AI Coding工具自带的hook机制。
3. 从原始的请求响应内容反推。确认下是否能和原始的HTTP请求响应关联。
4. Claude自带上报，使用OpenTelemetry，参考 https://code.claude.com/docs/en/monitoring-usage 。

### AI Coding框架自身的流程(待细化)

1. 元析看板，自身有记录状态的方案，例如元析在skill中指定进出具体开发环节的上报内容
2. 元析用进程的方案解析`~/.claude/projects`的日志，参考元析代码仓库`lib/session-monitor`。

### 以上串联方案

- http请求和CC日志可以通过sessionId关联
- tool-use可以通过tool use id关联
- main agent和sub-agent关联方案。subagent 的sessionId会变吗？【待确认】
- team agents 关联【待确认】


## 问题发现（待细化）

当用户出现如下表达的时候，需要自动进入诊断流程：
1. 重复强调同一件事情
2. 言辞激烈

当识别到特定指标问题时，可进入自动诊断流程：
1. one-shot率不达标

## 问题根因定位（待细化）

1. 耗时问题
2. 网络异常
3. context污染
4. context 窗口内容、大小异常。
5. 错误知识库误导
6. 隐式规范未显示表达

## 其他应用场景

1. 请求的重放
2. session重建

# 节奏

先做原始数据收集和埋点，问题发现和根因定位同步进行，但稍滞后。
先组内试用，原始数据收集和埋点基本跑通后提供测试版本。

1. 数据收集和埋点
   1. 详细方案5.9前
   2. 5.14前完成开发，调试，提供组内试用版本
   3. 5.14之后，组内的试点需求都需要加上原始数据上报。
2. 问题发现与根因定位
   1. 5.22前完成特定场景的诊断详细设计：知识库使用、context变化。
   2. 5.22前完成第一次数据回收和分析
   3. 5.29前完成通用问题发现的详细方案设计
   4. 6.5前完成通用问题根因定位的详细方案设计

开发记录
1. ❌补充export和import功能. 赶快做。按用户区分。区分yuanxi流程和普通流程。
   1. 一天100MB的请求响应日志。压缩率大概50%。
2. ❌skill作用域解析与展示。yuanxi用skill触发的hook，触发时报上一个skill。
3. ✅补全Cluade本地日志类型，基本补全了，解析规则见 Claude日志清洗.md。
4. ✅开发原始请求响应展示的页面
5. ✅优化界面展示：（1）main-agent和sugagent关联关系。（2）message之间的关联。（4）skill的展示（5）tool的展示
6. ❌原始请求message的增量解析（1）解析和展示context内容、大小、变化。（2）降低存储大小。
7. ✅命令行扩展，支持mc --code 以外的其他参数。
8. ❓sessionId选择的时候展示名字。
9.  ✅发布方案。先打whl，公司，[python包发布还得申请服务](http://km.sankuai.com/collabpage/2654374705)
10. ✅用了open-spec，superpowers未用
11. ❌结合元析流程 看上层知识库的作业应该展示成什么样子。[元析2.0-试点过程](https://km.sankuai.com/collabpage/2754745692)
   1. 元析已经完全在使用Git仓库知识库，知识item按规则+自增id编码；原来租户后端那种已经废弃
   2. ❓和淑军对下现在生成过程诊断是怎么在搞的。


开发问题记录：
- 使用openspec+cc生成代码。需求理解有误，实现的代码只代理了cc的域名。
- 使用Claude自带的`/context`命令时，请求`/v1/messages/count_tokens`接口404
- 数据解析倾向前端完成。
- 使用命令行启动mitmproxy，不从python脚本import mitmproxy库启动，这个方案对Python版本兼容性太差。

---
工具调研
1. ❓https://github.com/joemccann/claude-trace 看着有这么个项目，但是star不多。
2. ✅和其他 AI 可观测性的异同？[MDP-AI 可观测性用户指南](https://km.sankuai.com/collabpage/2720246955)、[Agent 可观测性：Trace、日志与异常链路的全链路监控](https://km.sankuai.com/collabpage/2752305277)
  - 异：观测的是其他AI服务链路，没有focus在AI Coding场景。
  - 同：都强烈依赖原始数据的上报和清洗
3. ✅[Escaping the Dumbzone, Part 1: Why Your AI Gets Stupider the More You Talk to It](https://dev.to/diggidydale/escaping-the-dumbzone-part-1-why-your-ai-gets-stupider-the-more-you-talk-to-it-4d8k) 引用paper里面的实验方案。
   1. 多文档问答任务：给模型提供 k 篇文档（其中恰好一篇包含答案，其余为干扰文档），通过调整答案文档的位置（开头、中间、结尾）和文档总数（10、20、30篇）来观察性能变化。
   2. 键值检索任务：给模型一个 JSON 对象（包含随机 UUID 键值对），要求模型根据指定键返回对应值。这是一个更纯粹的检索能力测试，排除了语义理解的干扰。


CC内部机制：
1. ✅skill触发和卸载动作识别
   1. 触发有日志记录，将skill的全文加载进context
   2. 直到compact的时候才会被截断或移除。整体skill内容保持在 25k（未确认）左右。
2. ✅agent、subagent机制
   1. subagent不能spawnsubagent, 可以使用skill
   2. `/agents` 可以创建agent定义，看哪些agent正在跑。
   3. `~/.claud/projects/{sessionId}/subagents` 目录保存了子agent的日志。
3. ❓cc的[team agents](https://code.claude.com/docs/en/agent-teams)
   1. team agents内的agents能相互交互；subagent只能和main agent交互。
4. cc的压缩机制
   1. ✅auto compact 和manual compact原理。
   2. ❓auto compact 和manual compact 底层的区别？
   3. ❓auto compact的分层机制
5. ❓cc的auto memory机制
6. ✅cc预定义的三类agent（explore、plan、general）有何差别？定义的可用tool、skill不一样
7. ❓SSE协议格式。哪些是标准的，哪些是自行定义的
8. ✅CC日志格式和解析规则



yuanxi通过skill的触发拆分环节。上报status内的内容关联session和需求。
auto compact可能可以通过compact的http请求、subtype为compact_boundary的日志切分。