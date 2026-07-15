# Agent Runner Architecture Design — Task 3.3

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-07-11 |
| Status | Draft — awaiting confirmation |

---

## 1. Runner 职责边界

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Runner                           │
│                                                             │
│  Runner 是一只"薄胶水层"。它不包含任何业务逻辑，             │
│  只负责将各组件连接在一起并协调生命周期。                    │
│                                                             │
│  ✅ 负责:                                                   │
│  ────────                                                   │
│  • 创建和组装 Agent 依赖（Registry / PromptLoader / Agent） │
│  • 加载 System Prompt（通过 PromptLoader）                   │
│  • 接收用户请求 → 委托给 Agent.run() → 返回结果             │
│  • 格式化最终输出（文本 / JSON）                             │
│  • 管理 Agent 的初始化/关闭生命周期                          │
│                                                             │
│  ❌ 不负责:                                                 │
│  ──────────                                                 │
│  • Tool 逻辑（课程查询/先修检查/时间计算/计划生成 ）         │
│  • FSM 状态转换（那是 ReActAgent 的职责）                    │
│  • Reasoning / Thought 生成（那是 FSM/LLM 的职责）           │
│  • 输入验证（那是 CLI 层的职责）                              │
│  • 数据加载（那是 DataLoader 的职责）                        │
│  • 业务异常处理（Agent 通过 ReActResult 返回，Runner 只传递）│
│                                                             │
│  测试原则: Runner 可以被完全 mock，不依赖任何外部资源。      │
└─────────────────────────────────────────────────────────────┘
```

**Runner vs Agent vs CLI 的分工:**

| 职责 | CLI | Runner | Agent |
|------|-----|--------|-------|
| 解析命令行参数 | ✅ | ❌ | ❌ |
| 输入验证 (范围/类型) | ✅ | ❌ | ❌ |
| 组装依赖 (Registry/Prompt) | ❌ | ✅ | ❌ |
| 加载 System Prompt | ❌ | ✅ | ❌ |
| 创建 Agent 实例 | ❌ | ✅ | ❌ |
| 执行 ReAct 循环 | ❌ | ❌ | ✅ |
| Tool 调度 | ❌ | ❌ | ✅ |
| 阻断检查 | ❌ | ❌ | ✅ |
| 格式化输出 | ❌ | ✅ | ❌ |
| 打印到控制台 | ✅ | ❌ | ❌ |

---

## 2. 调用链

```
┌─────────────────────────────────────────────────────────────┐
│                      完整调用链                              │
│                                                             │
│  CLI / API (未来)                                           │
│      │                                                      │
│      │  1. parse_args() → course_name, daily_hours,        │
│      │                    duration_days, user_knowledge     │
│      ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Runner.run(course_name, daily_hours, duration_days, │  │
│  │             user_knowledge)                          │  │
│  │                                                      │  │
│  │  内部步骤:                                           │  │
│  │                                                      │  │
│  │  2. prompt = self.prompt_loader.load(registry,       │  │
│  │                                      workflow)       │  │
│  │     → 注入 {{tool_list}} {{workflow}} {{date}}       │  │
│  │                                                      │  │
│  │  3. prompt = self.prompt_loader.format_with_input(   │  │
│  │         prompt, course_name, hours, days, knowledge) │  │
│  │     → 注入 {{user_input}}                            │  │
│  │                                                      │  │
│  │  4. result = self.agent.run(course_name, hours,      │  │
│  │                              days, knowledge)        │  │
│  │     → ReActResult(success, data/error, trace)        │  │
│  │                                                      │  │
│  │  5. output = self.formatter.format(result)           │  │
│  │     → str (文本) 或 dict (JSON)                       │  │
│  │                                                      │  │
│  │  6. return output                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│      │                                                      │
│      ▼                                                      │
│  CLI: print(output)                                         │
│                                                             │
│  ── 层间依赖 ───────────────────────────────────────────    │
│                                                             │
│  CLI ──▶ Runner ──▶ PromptLoader ──▶ System Prompt         │
│                │                          │                 │
│                ├──▶ ReActAgent ──▶ ToolRegistry ──▶ Tools  │
│                │        │                                    │
│                │        └──▶ Trace (记录过程)                │
│                │                                             │
│                └──▶ Formatter ──▶ Output (text/json)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 组件依赖图

```
                    ┌──────────┐
                    │   CLI    │
                    └────┬─────┘
                         │ import
                         ▼
                    ┌──────────┐
                    │  Runner  │
                    └────┬─────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
     ┌────────────┐ ┌──────────┐ ┌──────────┐
     │PromptLoader│ │ReActAgent│ │Formatter │
     └────────────┘ └────┬─────┘ └──────────┘
                         │
                         ▼
                   ┌────────────┐
                   │ToolRegistry│
                   └─────┬──────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
              ┌─────────┐ ┌─────────┐
              │ 4 Tools │ │  Data   │
              └─────────┘ └─────────┘
```

---

## 3. 生命周期

```
┌─────────────────────────────────────────────────────────────┐
│                    RUNNER LIFECYCLE                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. initialize()                                       │  │
│  │    ├── 创建 ToolRegistry（或接收注入的实例）           │  │
│  │    ├── 注册全部 4 个 Tool                             │  │
│  │    ├── 创建 PromptLoader                             │  │
│  │    ├── 创建 RuleBasedReActAgent(registry)            │  │
│  │    └── 状态: READY                                   │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 2. prepare_context(course_name, hours, days, knowledge)│  │
│  │    ├── load_system_prompt(registry, workflow)         │  │
│  │    ├── format_prompt_with_input(...)                   │  │
│  │    └── 返回: 完整的运行上下文 (prompt + params)       │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 3. run(course_name, hours, days, knowledge)           │  │
│  │    ├── prepare_context(...)                           │  │
│  │    ├── agent.run(...) → ReActResult                  │  │
│  │    └── 返回: ReActResult                             │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 4. format_response(result, mode="text")               │  │
│  │    ├── mode="text": 格式化为可读文本                  │  │
│  │    ├── mode="json": json.dumps(result)                │  │
│  │    └── 返回: str                                      │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 5. shutdown() (可选)                                  │  │
│  │    ├── 清理临时资源                                  │  │
│  │    ├── 关闭日志/连接                                 │  │
│  │    └── 状态: TERMINATED                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  典型使用 (CLI 模式):                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ runner = AgentRunner()          # initialize()        │  │
│  │ result = runner.run("Python", 3, 12)                 │  │
│  │ print(runner.format_response(result, mode="text"))   │  │
│  │ # CLI 进程退出 → 隐式 shutdown()                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 依赖注入设计

### 4.1 默认构造函数 vs 注入构造函数

```python
class AgentRunner:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        agent: RuleBasedReActAgent | None = None,
        prompt_loader: PromptLoader | None = None,
    ):
        # 未提供 → 使用生产默认值
        self.registry = registry or create_default_registry()
        self.agent = agent or RuleBasedReActAgent(self.registry)
        self.prompt_loader = prompt_loader or DefaultPromptLoader()
```

### 4.2 测试场景的依赖注入

```python
# 场景 1: 集成测试 — 使用真实 Registry 和 Agent
runner = AgentRunner()
result = runner.run("Python", 3, 12)

# 场景 2: Agent 单元测试 — 注入 Mock Registry
mock_registry = MockToolRegistry()
mock_registry.register(ToolEntry(
    name="get_course_info",
    function=lambda **kw: {"success": True, "data": {"name": "Python", "hours": 24}},
))
agent = RuleBasedReActAgent(mock_registry)
result = agent.run("Python", 3, 12)

# 场景 3: Runner 单元测试 — 注入 Mock Agent
mock_agent = MockReActAgent()
mock_agent.set_return_value(ReActResult(success=True, data={}))
runner = AgentRunner(agent=mock_agent)
output = runner.run("Python", 3, 12)
# → 不触发真实 Tool 调用

# 场景 4: Prompt 测试 — 注入 Mock Registry
mock_registry = MockToolRegistry()
prompt = load_system_prompt(mock_registry, "Step 1 → Step 2 → ...")
assert "get_course_info" in prompt
```

### 4.3 可注入点汇总

| 组件 | 注入方式 | 测试替换 |
|------|---------|---------|
| `ToolRegistry` | 构造函数参数 | `MockToolRegistry` |
| `ReActAgent` | 构造函数参数 | `MockReActAgent` (返回预设 ReActResult) |
| `PromptLoader` | 构造函数参数 | `MockPromptLoader` (返回固定字符串) |
| `Formatter` | 构造函数参数 | 替换输出格式 |
| `EXECUTION_PLAN` | 子类覆写 | 替换为自定义步骤序列 |

---

## 5. 未来扩展预留

### 5.1 LLM Provider

```python
# 当前 (MVP)
agent = RuleBasedReActAgent(registry)

# 未来 (v1.1)
class LLMReActAgent(RuleBasedReActAgent):
    def __init__(self, registry, llm_provider: LLMProvider):
        super().__init__(registry)
        self.llm = llm_provider

    def _reason(self, context: str, tool_schemas: list[dict]) -> str:
        return self.llm.chat(context, system_prompt=..., tools=tool_schemas)

    def _select_tool(self, thought: str) -> tuple[str, dict]:
        return self.llm.extract_function_call(thought)

# Runner 注入
runner = AgentRunner(
    agent=LLMReActAgent(registry, llm_provider=OpenAIProvider()),
)
# Runner.run() 接口完全不变
```

**Runner 零改动** — 只是传入不同的 Agent 实现。

### 5.2 Conversation Memory

```python
# 当前 (MVP): 无状态
result = runner.run("Python", 3, 12)  # 每次独立

# 未来 (v1.1): 带 Memory
class AgentRunner:
    def __init__(self, memory: ConversationMemory | None = None):
        self.memory = memory or NoOpMemory()

    def run(self, ...) -> dict:
        # 恢复上下文
        history = self.memory.load(session_id)
        # 注入到 Agent
        self.agent.set_memory(history)
        result = self.agent.run(...)
        # 保存上下文
        self.memory.save(session_id, self.agent.get_trace())
        return result

    # 支持追问
    def continue_conversation(self, session_id: str, user_message: str):
        # 重新进入 loop，无需完整参数
        ...

# Runner 接口扩展但向后兼容
```

### 5.3 API Server

```python
# 当前 (MVP): CLI 直接调用 Runner
# 未来 (v1.2): FastAPI 包装

from fastapi import FastAPI
app = FastAPI()
runner = AgentRunner()  # 全局单例

@app.post("/api/v1/plan")
async def create_plan(request: PlanRequest):
    result = runner.run(
        course_name=request.course,
        daily_hours=request.hours,
        duration_days=request.days,
        user_knowledge=request.knowledge,
    )
    return runner.format_response(result, mode="dict")

# Runner 自身不需要任何改动
# 唯一新增: src/ui/web.py (FastAPI 路由)
```

---

## 6. 代码结构

```
src/agent/runner.py          # AgentRunner 类

结构:
    AgentRunner
    ├── __init__(registry, agent, prompt_loader)     # 依赖注入
    ├── run(course_name, hours, days, knowledge)     # 主入口
    │       └── → ReActResult
    ├── format_response(result, mode)                # 格式化输出
    │       └── → str
    ├── prepare_context(course_name, hours, ...)     # 准备 Prompt 上下文
    │       └── → str (完整 Prompt)
    └── shutdown()                                   # (可选) 清理
```

### 与 formatter.py 的关系

| 组件 | 职责 |
|------|------|
| `AgentRunner.format_response()` | 调用 formatter，提供 mode 选择（text/json） |
| `src/ui/formatter.py` | 实际格式化逻辑（Task 5.2） |

MVP 阶段 `format_response()` 可以直接在 Runner 中实现简单逻辑，M5 时提取到 `formatter.py`。
