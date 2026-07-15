# 本科毕业设计答辩讲稿

**项目名称:** 基于 ReAct 与 Tool Calling 的课程学习规划 Agent 系统设计与实现
**时长:** 10 分钟
**风格:** 自然口语化，面向计算机/AI 方向导师

---

## 【第1页 项目介绍】

**PPT展示内容:**
封面页 — 项目标题、核心技术路线 (ReAct + Tool Calling)、关键工程指标 (26文件/162测试/90%覆盖率)

**我的讲稿 (约60秒):**

> 各位老师好。我的毕业设计题目是: 基于 ReAct 与 Tool Calling 的课程学习规划 Agent。
>
> 先说一下为什么选这个题。现在大模型很火，ChatGPT、Claude 这些大家每天都在用。但你有没有遇到过这种情况——你问它"学 Python 要多久"，它说"大概两到三个月"。这个回答从哪里来的? 模型训练数据。没法验证, 可能是错的, 这就是我们说的"幻觉问题"。
>
> 我的课题核心思路很简单: 不要让模型直接回答。让它在回答之前, 先去查数据。
>
> 具体怎么做呢? 我设计了一个 Agent。用户问"学 Python 要多久", Agent 不会直接回答, 而是调用一个叫 `get_course_info` 的工具去查课程数据库, 拿到真实数据——"Python 24 小时, 7 个模块"。然后它还要检查你有没有先修课程的基础, 计算你每天学 3 小时、学 12 天是否可行, 最后生成一个完整的学习计划。
>
> 这就是 Agent 和 Chatbot 的本质区别: Chatbot 靠记忆, Agent 靠工具。

**本页重点:**
- Agent ≠ Chatbot。Agent 的信息来源是 Tool 输出, 不是模型记忆。
- 核心创新: 强制 Tool Calling + ReAct 推理 + 多步工作流编排。

**可能追问:**
> "你这个系统和大模型 Function Calling 有什么区别?"

**回答思路:**
> Function Calling 是 LLM 的一个功能, 本系统是在此之上构建了完整的 Agent 框架——包括 ToolRegistry 注册中心、ReAct 状态机、Trace 审计追踪、异常阻断机制。Function Calling 只是调用工具, 我的系统还包括工具注册、动态调度、执行追踪、安全约束。

---

## 【第2页 系统整体架构】

**PPT展示内容:**
四层架构图 — providers/ → agent/ → tools/ → models/。各层职责卡片。工程指标条。

**我的讲稿 (约60秒):**

> 这张图是系统的整体架构。我采用了四层分离的设计——这是从软件工程的角度考虑的, 不是把代码堆在一起。
>
> 最上面是 Provider 层——这一层封装了大模型的 API 调用。当前接的是 DeepSeek, 但抽象成了 LLMProvider 接口, 以后换 OpenAI 或 Claude 不需要改 Agent 代码。
>
> 第二层是 Agent 核心层——包含三个关键组件: AgentRunner 是总入口, 负责把用户输入、Prompt、Registry 串起来; LLMReActAgent 是大脑, 负责 ReAct 推理循环——思考、调用工具、观察结果、继续推理; ToolRegistry 是工具注册中心, 所有工具在这里统一管理。
>
> 第三层是 Tools 层——目前有 6 个工具, 4 个是课程规划相关的, 2 个是演示用的计算器和天气查询。
>
> 最底层是 Pydantic 数据模型——10 个模型, 字段名和 JSON 数据完全一致, 中间不需要任何转换。
>
> 关键设计原则是: 依赖方向严格向下, 上层可以依赖下层, 下层绝对不依赖上层。整个项目零循环导入。

**本页重点:**
- 四层分离架构, 依赖单向。26 源文件, 零循环导入。
- AgentRunner 是薄胶水层, LLMReActAgent 是核心循环, ToolRegistry 是 O(1) 调度中心。

**可能追问:**
> "为什么要分四层? 两层不够吗?"

**回答思路:**
> 分层是为了隔离变化。举个例子: 我想把 DeepSeek 换成 Claude, 只需要在 Provider 层新增一个 ClaudeProvider 类, Agent 层一行代码不用改。如果 Provider 和 Agent 耦合在一起, 换模型就要改核心逻辑。同样的道理, 新增一个 Tool 只需要在 Tools 层注册, Agent 层完全不变。

---

## 【第3页 ReAct执行机制】

**PPT展示内容:**
ReAct 序列图 (Thought → Action → Observation 循环)。Trace 执行追踪时间线 (13 步)。TraceEntry 数据结构。

**我的讲稿 (约60秒):**

> 这一页讲 Agent 是怎么"思考"的。ReAct 是一种推理范式, 全称是 Reasoning + Acting。
>
> 具体流程是这样的: Agent 收到用户请求后, 先进入 Thinking 状态——"我需要查询 Python 的课程信息"。然后进入 Action 状态——通过 ToolRegistry 调用 `get_course_info` 工具。工具返回结果后进入 Observation 状态——拿到课程数据, 检查是否有阻断条件。
>
> 每做一步, 都会产生一条 Trace 记录。一条 Trace 包含 8 个字段: 步骤序号、Agent 状态、思考内容、选择的工具、输入参数、输出摘要、时间戳、耗时。
>
> 图中的这个例子是成功路径——共产生 13 条 Trace 记录, 对应 4 轮思考 + 4 次工具执行 + 4 次结果观察 + 1 次最终响应。如果先修条件不满足, 在第 2 个工具处就会阻断, 只产生 7 条 Trace, 不会浪费后续调用。

**本页重点:**
- ReAct = 思考 → 执行 → 观察 → 循环。不是一次性调用, 是分步推理。
- Trace 是 Agent 的决策审计记录, 每一步可追溯。

**可能追问:**
> "这个 ReAct 和 LangChain 的 Agent 有什么区别?"

**回答思路:**
> LangChain 是一个通用框架, Agent 的行为被封装在框架内部, 调试困难。我这个是自己实现的——你可以看到每一行代码, 每一条 Trace 记录, 完全透明。另外 LangChain 的 Agent 通常不是为课程规划这种多步工作流设计的, 我的系统在编排器和阻断检查方面做了专门优化。

---

## 【第4页 Tool Registry 设计】

**PPT展示内容:**
左侧: if/elif 反模式 vs Registry 模式对比。右侧: 四个操作 (注册/注销/查询/执行) 卡片。底部: 已注册 6 个 Tool 的名称条。

**我的讲稿 (约60秒):**

> 这一页展示了一个我认为比较重要的设计决策——Tool Registry。
>
> 大家想想, 如果要实现工具调用, 最直接的做法是什么? 写一个大的 if/elif 链: if 工具名等于"get_course_info", 就调用 get_course_info 函数; elif 等于"get_prerequisite", 就调用另一个。这确实能工作, 但每加一个新工具, 就要改这个函数——违反了开闭原则。
>
> 我的方案是用 Python 的字典来实现。`ToolRegistry` 内部维护一个 `_tools` 字典, key 是工具名, value 是一个 `ToolEntry` 对象。`ToolEntry` 包含工具的元数据——名称、描述、输入输出 Schema、以及函数引用。调用工具时就是 `self._tools.get(name)`, O(1) 的字典查找, 没有任何条件分支。
>
> 这个设计带来的好处是: 加一个新工具只需一行 `registry.register(ToolEntry(...))`, Agent 代码完全不变。而且 `list_tools()` 方法可以直接把 Registry 里的工具列表转换为 LLM Function Calling 的 Schema——这是后来接 LLM 时用到的一个关键能力。

**本页重点:**
- 用 Dict 替代 if/elif。O(1) 查找, 零分支。
- 扩展性: 添加 Tool 不改 Agent 代码。这是开闭原则的体现。

**可能追问:**
> "ToolEntry 里的 input_schema 是怎么定义的? 是你自己手写的吗?"

**回答思路:**
> 对, 目前是手写的 JSON Schema, 和 OpenAI Function Calling 的格式兼容。未来可以自动从 Pydantic 模型的 `model_json_schema()` 方法生成, 已经在 plan 里了。

---

## 【第5页 LLM Provider 抽象】

**PPT展示内容:**
LLMProvider 类图 (ABC + 3 个实现)。设计原则卡片。5 种异常 → 中文消息映射。

**我的讲稿 (约60秒):**

> 这一页展示 Provider 抽象层的设计。
>
> 为什么需要这一层? 因为我不想让 Agent 代码依赖任何具体的 LLM SDK。你看 PPT 右边的代码——Agent 只 import 了 `LLMProvider` 这个抽象基类, 从来没有 `import openai`。
>
> 当前实现的是 DeepSeek Provider。选择 DeepSeek 的原因是它的 API 完全兼容 OpenAI 的 chat/completions 协议——用 OpenAI 的 Python SDK, 把 base_url 指向 api.deepseek.com, 就可以调用了。对国内用户来说, 注册更方便, 也不需要海外支付。
>
> 如果以后想换成 Claude 或者 GPT, 只要实现一个新的 Provider 类, 覆写 `chat()` 方法。Agent 代码一行不改——因为 Agent 只依赖 `LLMProvider` 这个接口, 不依赖具体实现。这就是依赖倒置原则的体现。
>
> 另外, `chat()` 方法里做了完整的异常处理——认证失败、速率限制、超时、API 错误、未知错误五种情况都映射成了中文错误消息。

**本页重点:**
- Agent 不依赖具体 SDK。Provider 抽象 = 模型可替换。
- DeepSeek 兼容 OpenAI 协议, 对国内用户友好。

**可能追问:**
> "DeepSeek 和 GPT-4 在 Tool Calling 上有什么区别?"

**回答思路:**
> 就 Tool Calling 而言, 它们都遵循 OpenAI 的 function calling 规范, 行为几乎一致。实际测试中 DeepSeek-chat 在 Tool Calling 上的表现和 GPT-4o-mini 接近。主要区别是 DeepSeek 的 rate limit 相对宽松, 价格也更友好。

---

## 【第6页 Tool Calling 流程】

**PPT展示内容:**
Tool Calling 数据流图 (User → LLM → ToolCall → Registry → Tool → Observation → LLM → Final Answer)。LLMReActAgent 核心循环代码。

**我的讲稿 (约60秒):**

> 这一页详细展示 Tool Calling 的完整数据流。
>
> 关键设计是职责分离: LLM 做决策, Agent 做执行。
>
> 具体流程: 用户说"帮我计算 234 乘以 567"。Agent 首先通过 ToolAdapter 把 ToolRegistry 里的工具列表转换成 OpenAI Function Calling 的 Schema 格式——这一步只有 20 行代码。然后把 Schema 和用户消息一起发给 DeepSeek。
>
> LLM 分析后决定: 我需要调用 calculator 工具, 参数 expression 是"234*567"。LLM 返回的是一个 tool_calls 列表, 不是最终答案。
>
> Agent 拿到 tool_calls, 通过 `registry.invoke("calculator", expression="234*567")` 执行, 得到结果 132678。这个结果被追加到对话历史中, 角色标记为 "tool"。
>
> LLM 看到工具返回的结果后, 再次推理, 这次它认为任务完成了, 返回最终回答——"234 乘以 567 等于 132678"。
>
> 这就是 LLM 和 Agent 的分工: LLM 决定做什么, Agent 负责怎么做。

**本页重点:**
- LLM 决策 (调用哪个 Tool?) vs Agent 执行 (怎么调用?)。
- 工具调用结果作为 Observation 反馈给 LLM, 形成闭环。

**可能追问:**
> "如果 LLM 选错了工具怎么办? 有容错机制吗?"

**回答思路:**
> 目前有两层保护: 一是 MAX_TOOL_ROUNDS=10 的设置, 防止 LLM 陷入无限循环; 二是 ToolRegistry.invoke() 内部有 try/except, 工具执行异常会被捕获为 INTERNAL_ERROR 返回给 LLM, LLM 可以根据错误信息调整策略。更完善的容错 (比如 tool_calls 参数校验) 在后续计划中。

---

## 【第7页 课程规划 Workflow】

**PPT展示内容:**
6 步编排流程卡片 (3 步复用 + 3 步编排)。绿色标记复用, 橙色标记编排器逻辑。编排器代码片段。

**我的讲稿 (约60秒):**

> 这一页展示课程规划的具体 Workflow。
>
> 当你告诉 Agent "我要学 Python, 每天 3 小时, 12 天", Agent 内部不是调用一个大函数, 而是执行了 6 个步骤。
>
> 前 3 步是复用已有的工具: 第一步查课程信息——Python 24 小时, 7 个模块; 第二步检查先修条件——Python 没有先修课, 直接通过; 第三步评估时间可行性——每天 3 小时乘 12 天等于 36 小时, 需要 24 小时, 可行, 还剩 12 小时缓冲。
>
> 后 3 步是编排器的独有逻辑: 第四步将课程主题转换为学习模块; 第五步用 Scheduler 调度每日计划——贪心算法分配, 每 5 天插入一个复习日, 最后插一个评估日; 第六步用 ResourceProvider 为每个模块匹配合适的学习资源。
>
> 这里最重要的设计是: generate_learning_plan 是一个编排器, 不是第 5 个独立的工具。它前 3 步直接调用已有的工具函数, 没有任何代码重复。绿色表示复用, 橙色表示编排器独有的逻辑。

**本页重点:**
- 编排器 ≠ 大函数。前 3 步复用已有 Tool, 后 3 步是编排器独有逻辑。
- Scheduler 和 ResourceProvider 是独立的调度和资源组件。

**可能追问:**
> "为什么不把 6 步全部放在一个函数里?"

**回答思路:**
> 全部放一个函数就是"上帝函数"——测试困难, 维护困难, 复用困难。拆成 6 个独立步骤后, Scheduler 可以单独测试、单独替换; ResourceProvider 用 Provider 模式, 以后接 RAG 或数据库不需要改编排器代码。这就是单一职责原则在工程中的体现。

---

## 【第8页 可靠性设计】

**PPT展示内容:**
6 层安全约束堆叠图。实际 Demo 输出 (Spark 先修冲突)。DAG 感知 + 输入验证代码。

**我的讲稿 (约50秒):**

> 这一页讲系统的可靠性设计。
>
> 我设计了六层安全约束, 从外到内依次是: 第一层输入验证——在 Agent 启动之前就拦截非法参数; 第二层 DAG 感知递归——先修关系是一个有向无环图, 不是树, 同一个课程可能被多个路径引用。我的实现用 visited 集合处理这种共享依赖, 而不是把它误判为循环依赖。
>
> 第三层递归深度限制——最多展开 5 层, 防止无限递归。第四层 LLM 循环上限——Agent 最多调用 10 轮工具, 防止死循环。第五层 Provider 异常处理——刚才讲过的 5 种异常类型。第六层业务阻断门——如果先修条件不满足或时间不足, Agent 立即终止, 输出具体的调整建议。
>
> PPT 右边是一个实际例子: 用户想学 Spark, 但 Spark 要求先学 Python 和 Hadoop, Hadoop 又要求 Linux 和 Java——4 门先修课, 总共 112 小时。Agent 在第二步就检测到这个冲突, 立即终止, 没有浪费后续的计算。

**本页重点:**
- 6 层约束保障系统稳定。不是靠运气, 是靠设计。
- DAG 感知: 共享依赖不误报。业务阻断: 先修冲突/时间不足立即终止。

**可能追问:**
> "DAG 感知具体是怎么实现的?"

**回答思路:**
> 递归展开先修树时维护一个 visited 集合。进入一个节点时先检查 `name_lower in visited`, 如果为 True, 说明这个课程已经被另一个路径处理过了——直接 return, 不报错, 也不重复展开。这和检测循环依赖不同: 循环依赖是"正在访问的路径上出现了重复", 应该报错; 共享依赖是"不同路径汇聚到同一个节点", 应该跳过。

---

## 【第9页 Trace 与可观测性】

**PPT展示内容:**
TraceEntry 8 字段结构。成功/阻断场景的步数卡片。Trace 示例代码。

**我的讲稿 (约50秒):**

> 这一页讲 Trace——我觉得这是 Agent 和普通 Chatbot 最本质的区别之一。
>
> 你问 Chatbot 一个问题, 它给你一个回答。如果回答是错的, 你不知道为什么错——你只能猜"可能训练数据有问题"。
>
> Agent 不一样。每一次执行都产生完整的 Trace 记录。你可以看到第 1 步 Agent 在想什么, 第 2 步调用了哪个工具, 传了什么参数, 第 3 步工具返回了什么结果, 第 5 步 Agent 为什么决定终止。每一步都有时间戳和耗时。
>
> 这对于调试和答辩来说非常重要——你可以指着任意一步解释: "你看, 这里 Agent 检测到 satisfied=false, 所以它正确地终止了, 没有继续浪费资源"。
>
> 成功路径 13 步, 先修冲突 7 步, 时间不足 10 步。每一步都可追溯、可解释、可审计。

**本页重点:**
- Agent 是可观测的, Chatbot 是黑盒。Trace 是 Agent 的决策记录, 不是日志文件。
- 13/7/10 步对应三种场景, 阻断点清晰可见。

**可能追问:**
> "Trace 会影响性能吗? 每条记录存了多少数据?"

**回答思路:**
> 每条 Trace 的 tool_output 字段做了摘要处理——只保留关键字段如 success、data_keys、satisfied、feasible, 不会存储完整的课程数据或学习计划。整个 13 步 Trace 的数据量大约是几 KB, 对性能的影响可以忽略。而且 Trace 是 Python 内存中的 dataclass, 没有磁盘 IO。

---

## 【第10页 总结与未来工作】

**PPT展示内容:**
3 个核心贡献卡片 (Agent=ToolCalling / 架构=可扩展 / 工程=可靠)。4 阶段演进路线图。感谢语。

**我的讲稿 (约30秒):**

> 最后做一个总结。
>
> 本课题完成了三件事。第一, Agent 不是 Chatbot——所有信息通过 Tool Calling 获取, 从架构层面杜绝了幻觉。第二, 架构是可扩展的——添加新工具、替换大模型, 都只需要注册或实现接口, 核心代码不动。第三, 工程质量有保障——162 个测试用例, 大约 90% 的覆盖率, 完整的 Trace 审计。
>
> 后续的演进方向: v1.1 增加 Conversation Memory, 支持多轮对话; v1.2 接入 RAG 做智能资源检索, 同时加上 Web UI; v2.0 演进为 Multi-Agent 协作编排。这些都是在当前架构基础上的自然扩展, 不需要推倒重来。
>
> 以上就是我的毕业设计答辩。请各位老师提问。

**本页重点:**
- 三个核心贡献: Agent 范式 / 可扩展架构 / 工程质量。
- 未来路线清晰, 架构已预留扩展点。

**可能追问:**
> "你提到 Multi-Agent, 现在的架构怎么支持?"

**回答思路:**
> 目前 ToolRegistry 已经支持动态注册和调度——这就是 Multi-Agent 的基础。未来每个 Sub-Agent 可以作为一个特殊的 Tool 注册到 Registry 中, Orchestrator Agent 通过 Tool Calling 将子任务委派给 Sub-Agent 执行。Provider 抽象层也支持不同 Sub-Agent 使用不同的大模型。核心架构不需要大的改动。

---

## 附录 A: 常见追问合集

### A1. 核心技术相关

**Q: Agent 和 LangChain/ AutoGPT 有什么区别?**
> 本系统是自己从零实现的, 没有依赖 Agent 框架。这样做的好处是: 每一行代码都完全可控、可解释; 不引入框架的黑盒行为; 架构更轻量——核心 Agent 循环不到 200 行代码。缺点是功能没有 LangChain 丰富, 但这对于 MVP 阶段来说是合理的取舍。

**Q: 为什么不直接用 LangGraph 做工作流编排?**
> LangGraph 确实是很好的工作流工具, 但它封装了很多内部细节。对于本科毕业设计来说, 自己实现 ReAct 循环和工作流编排, 能更清楚地展示对 Agent 原理的理解。而且我的实现已经预留了替换接口——如果后续需要更复杂的编排, 可以在不改变 ToolRegistry 和 Tool 的前提下接入 LangGraph。

**Q: 你们的 Agent 的 "智能" 体现在哪里?**
> 两个层面。第一, LLM 层——LLM 能够理解自然语言, 自主决定调用哪个工具、传什么参数, 这是"推理智能"。第二, Agent 层——Agent 的 EXECUTION_PLAN 定义了工作流逻辑, blocker_check 定义了安全约束, 这是"工程智能"。两者结合: LLM 提供灵活性, Agent 提供可靠性。

### A2. 工程设计相关

**Q: 26 个文件, 3707 行代码, 对于一个 MVP 来说是不是太多了?**
> 3707 行包含了完整的类型注解、中文文档字符串、以及 1815 行测试代码。去掉测试, 核心代码约 1900 行, 分布在 4 个层级中, 每个模块职责单一。这个规模对于一个有 4 层架构、10 个数据模型、6 个工具、一个 ReAct 状态机的系统来说是合理的。而且代码行数多不代表复杂——很多是结构化的定义和验证逻辑。

**Q: 你们做了哪些工程实践?**
> 五个方面。第一, Pydantic v2 做数据验证, 所有数据进出都有类型保障。第二, 依赖注入——AgentRunner 的构造函数接受可选的 registry/agent/prompt_loader 参数, 方便单元测试。第三, Provider 抽象——用 ABC 定义接口, 实现依赖倒置。第四, 异常体系——8 个自定义异常类, 每种异常有明确的 error_code。第五, 162 个测试用例覆盖了模型、工具、Agent 三个层级。

**Q: 如果让你重新设计, 有哪些地方可以改进?**
> 三个地方。第一, Tool 的 input_schema 目前是手写的 JSON Schema, 应该从 Pydantic 模型自动生成, 减少重复。第二, resource_provider 的映射表目前是硬编码的, 应该抽成 JSON 配置文件。第三, Scheduler 的贪心算法比较简单, 可以引入约束求解器 (如 OR-Tools) 做更优的调度。但这些都不影响核心架构——都是局部优化。

### A3. 系统演示相关

**Q: 你的 Demo 能演示什么?**
> 三样东西。第一, 课程规划——输入"Python, 3h/day, 12天", 输出 7 个模块、10 天计划、9 条资源。第二, 先修冲突——输入"Spark", 显示 4 门缺失先修课、112 小时总先修学时, Agent 在检测到冲突后立即终止。第三, LLM Tool Calling——输入"帮我计算 234*567", Agent 通过 DeepSeek 自主调用 calculator 工具, 返回正确答案。

**Q: 系统能处理多少门课程?**
> 目前 courses.json 中有 10 门课程, 涵盖 Python 基础到大数据技术栈 (Hadoop/Spark/Flink)。这个数据量对于 MVP 演示来说足够了。系统设计上可以支持任意数量的课程——只需在 JSON 中添加数据, 零代码改动。

**Q: 为什么不直接用数据库?**
> JSON 文件对于 MVP 阶段的优势是: 零配置, 可以直接查看和修改, 不需要安装数据库。但 DataLoader 层已经做了抽象——`load_courses()` 和 `load_prerequisite_map()` 的接口是稳定的。后续替换为 SQLite 或 PostgreSQL, 只需要修改 DataLoader 的实现, Tool 层和 Agent 层完全不受影响。

---

## 附录 B: 时间检查

| Slide | 标题 | 分配时间 |
|-------|------|---------|
| 1 | 项目介绍 | 60 秒 |
| 2 | 系统架构 | 60 秒 |
| 3 | ReAct 机制 | 60 秒 |
| 4 | Tool Registry | 60 秒 |
| 5 | LLM Provider | 60 秒 |
| 6 | Tool Calling | 60 秒 |
| 7 | Workflow | 60 秒 |
| 8 | 可靠性 | 50 秒 |
| 9 | Trace | 50 秒 |
| 10 | 总结 | 30 秒 |
| **合计** | | **550 秒 ≈ 9 分 10 秒** |
| + Q&A 缓冲 | | **50 秒** |
| **总计** | | **10 分钟** |
