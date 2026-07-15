# M5 LLM Provider Layer — Architecture Design

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-07-11 |
| Status | Draft — awaiting confirmation |
| Parent | `docs/agent-core-design.md` |

---

## 目录

1. [M5 Architecture Diagram](#1-m5-architecture-diagram)
2. [Provider Interface Design](#2-provider-interface-design)
3. [LLMReActAgent 与 RuleBasedReActAgent 关系](#3-llmreactagent-与-rulebasedreactagent-关系)
4. [Tool Calling 数据流](#4-tool-calling-数据流)
5. [文件修改计划](#5-文件修改计划)
6. [最小迁移方案](#6-最小迁移方案)

---

## 1. M5 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          M5: LLM Provider Layer                         │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    config/ (NEW)                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │ provider.yaml  /  .env                                       │ │  │
│  │  │   LLM_PROVIDER=deepseek                                      │ │  │
│  │  │   DEEPSEEK_API_KEY=sk-...                                     │ │  │
│  │  │   MODEL_NAME=deepseek-chat                                    │ │  │
│  │  └─────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  src/providers/ (NEW)                              │  │
│  │                                                                    │  │
│  │  ┌──────────────┐                                                 │  │
│  │  │ LLMProvider  │  ← 抽象基类 (Protocol / ABC)                     │  │
│  │  │ (base.py)    │     chat(messages, tools) → LLMResponse         │  │
│  │  └──────┬───────┘                                                 │  │
│  │         │                                                          │  │
│  │    ┌────┴────────────┬──────────────────┐                          │  │
│  │    ▼                 ▼                  ▼                          │  │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────┐                   │  │
│  │  │ DeepSeek   │ │ OpenAI     │ │ Claude       │                   │  │
│  │  │ Provider   │ │ Provider   │ │ Provider     │                   │  │
│  │  │ (deepseek  │ │ (openai_   │ │ (claude_     │                   │  │
│  │  │ _provider) │ │ provider)  │ │ provider)    │                   │  │
│  │  └────────────┘ └────────────┘ └──────────────┘                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              src/agent/tool_adapter.py (NEW)                      │  │
│  │                                                                    │  │
│  │  ToolRegistry → to_openai_tools() → OpenAI-compatible schema     │  │
│  │                                                                    │  │
│  │  to_openai_tools(registry) → [                                    │  │
│  │      {"type": "function", "function": {"name": "...", ...}}       │  │
│  │  ]                                                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              src/agent/llm_react.py (NEW)                         │  │
│  │                                                                    │  │
│  │  LLMReActAgent(registry, provider)                                │  │
│  │      │                                                             │  │
│  │      ├── run(course_name, daily_hours, duration_days, knowledge)  │  │
│  │      │       │                                                     │  │
│  │      │       ├── while not done:                                  │  │
│  │      │       │     response = provider.chat(messages, tools)     │  │
│  │      │       │     if response.tool_calls:                        │  │
│  │      │       │         for call in tool_calls:                    │  │
│  │      │       │             result = registry.invoke(...)          │  │
│  │      │       │             messages.append(observation)           │  │
│  │      │       │             trace.append(...)                      │  │
│  │      │       │     else:                                          │  │
│  │      │       │         return final_answer                        │  │
│  │      │       │                                                   │  │
│  │      │       └── return ReActResult(success, data, trace)        │  │
│  │      │                                                             │  │
│  │      └── 与 RuleBasedReActAgent 共享相同的 run() 签名            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              (UNCHANGED — 现有组件)                                │  │
│  │                                                                    │  │
│  │  AgentRunner  ← 构造函数接受 agent: RuleBasedReActAgent | LLM... │  │
│  │  ToolRegistry ← 不变                                               │  │
│  │  4 Tools      ← 不变                                               │  │
│  │  Pydantic     ← 不变                                               │  │
│  │  TraceEntry   ← 不变                                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 新增 vs 不变

```
NEW:                                    UNCHANGED:
src/providers/base.py                   src/tools/*        (4 Tools)
src/providers/deepseek_provider.py      src/models/*       (Pydantic)
src/providers/openai_provider.py        src/agent/tool_registry.py
src/providers/claude_provider.py        src/agent/prompt_loader.py
src/agent/tool_adapter.py              src/agent/runner.py (AgentRunner)
src/agent/llm_react.py                 src/exceptions.py
config/.env.example                     tests/*            (向后兼容)
```

---

## 2. Provider Interface Design

### 2.1 抽象基类

```python
# src/providers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """LLM 返回的单个 Tool 调用请求。"""
    id: str                # 调用 ID (用于并行 tool_calls)
    name: str              # Tool 名称
    arguments: dict        # 已解析的参数 dict


@dataclass
class LLMResponse:
    """LLM 的统一响应格式。

    屏蔽不同 Provider 的 SDK 差异。
    """
    content: str | None = None              # 文本回复 (Final Answer)
    tool_calls: list[ToolCall] = field(default_factory=list)  # Tool 调用请求
    finish_reason: str = "stop"             # stop / tool_calls / length


class LLMProvider(ABC):
    """LLM Provider 抽象基类。

    所有 Provider 实现必须继承此类。
    Agent 只依赖此接口，不依赖具体 SDK。
    """

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> LLMResponse:
        """发送消息到 LLM 并返回统一格式的响应。

        Args:
            messages: 对话历史 [{"role": "system"|"user"|"assistant"|"tool", "content": ...}]
            tools: OpenAI-compatible function calling schema

        Returns:
            LLMResponse: 统一响应（文本 或 Tool 调用）
        """
        ...
```

### 2.2 具体 Provider 实现（伪代码）

```python
# src/providers/deepseek_provider.py

class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model

    def chat(self, messages, tools) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )
        return self._parse_response(response)


# src/providers/openai_provider.py

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, messages, tools) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )
        return self._parse_response(response)


# src/providers/claude_provider.py

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-fable-5"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def chat(self, messages, tools) -> LLMResponse:
        # Claude Messages API 使用不同的 tool 格式
        # Provider 内部完成格式转换
        response = self.client.messages.create(
            model=self.model,
            messages=self._convert_messages(messages),
            tools=self._convert_tools(tools),
        )
        return self._parse_response(response)
```

### 2.3 Provider Factory

```python
# src/providers/__init__.py

def create_provider(config: dict) -> LLMProvider:
    provider_name = config.get("provider", "deepseek")
    if provider_name == "deepseek":
        return DeepSeekProvider(api_key=config["api_key"], model=config.get("model", "deepseek-chat"))
    elif provider_name == "openai":
        return OpenAIProvider(api_key=config["api_key"], model=config.get("model", "gpt-4o"))
    elif provider_name == "claude":
        return ClaudeProvider(api_key=config["api_key"], model=config.get("model", "claude-fable-5"))
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
```

---

## 3. LLMReActAgent 与 RuleBasedReActAgent 关系

### 3.1 共享接口

```
                    ┌─────────────────────────┐
                    │    AgentInterface        │
                    │    (duck typing)         │
                    │                          │
                    │  run(course_name,        │
                    │      daily_hours,        │
                    │      duration_days,      │
                    │      user_knowledge)     │
                    │      → ReActResult      │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
              ▼                                   ▼
   ┌──────────────────────┐          ┌──────────────────────┐
   │ RuleBasedReActAgent  │          │   LLMReActAgent      │
   │ (MVP)                │          │   (M5)                │
   │                      │          │                       │
   │ for step in PLAN:    │          │ while not done:       │
   │   result = invoke()  │          │   resp = llm.chat()   │
   │   check blocker      │          │   if tool_calls:      │
   │   update state       │          │     result = invoke() │
   │                      │          │   else:               │
   │ 硬编码 4 步序列      │          │     return final      │
   └──────────────────────┘          └──────────────────────┘
              │                                   │
              └─────────────┬─────────────────────┘
                            │
                    都返回 ReActResult
                 (success, data/error, trace)
```

### 3.2 AgentRunner 中的使用

```python
# AgentRunner.__init__()
# 唯一的改动点: 接受 LLMReActAgent 作为 agent 参数

# MVP 模式 (默认)
runner = AgentRunner()  # → RuleBasedReActAgent

# LLM 模式
provider = create_provider(config)
llm_agent = LLMReActAgent(registry, provider, prompt_loader)
runner = AgentRunner(agent=llm_agent)

# AgentRunner.run() — 完全不变
result = runner.run("Python", 3, 12)
```

### 3.3 接口对比

| 方面 | RuleBasedReActAgent | LLMReActAgent |
|------|-------------------|---------------|
| `run()` 签名 | 相同 | 相同 |
| 返回类型 | `ReActResult` | `ReActResult` |
| Tool 调用方式 | `registry.invoke()` | `registry.invoke()` |
| Trace 结构 | `TraceEntry` | `TraceEntry` |
| 需要 Registry | ✅ | ✅ |
| 需要 PromptLoader | ❌ (可选) | ✅ |
| 需要 LLMProvider | ❌ | ✅ |
| 阻断逻辑 | `blocker_check()` | LLM 自主判断 + 手动检查 safety |

---

## 4. Tool Calling 数据流

### 4.1 完整 LLM Tool Calling 流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LLM TOOL CALLING DATA FLOW                           │
│                                                                         │
│  1. ToolRegistry ──▶ Tool Adapter ──▶ OpenAI Tools Schema               │
│     ┌──────────┐      to_openai_       [{"type":"function",...}, ...]   │
│     │ 4 Tools  │      tools()                                           │
│     └──────────┘                                                        │
│                                                                         │
│  2. System Prompt ──▶ Messages[0] = system                              │
│     ┌──────────────┐                                                    │
│     │ prompt_loader│                                                    │
│     │ .load()      │                                                    │
│     └──────────────┘                                                    │
│                                                                         │
│  3. User Input ──▶ Messages[1] = user                                   │
│                                                                         │
│  4. LLM ──▶ LLMResponse                                                 │
│     ┌────┐                                                              │
│     │ LLM│  messages + tools ──▶ response                               │
│     └────┘                                                              │
│                                                                         │
│  5. IF tool_calls:                                                      │
│     ┌──────────────┐       ┌──────────────┐                             │
│     │ ToolCall[]   │──1──▶│ ToolRegistry │──2──▶ Tool ──3──▶ result    │
│     │ [{name,args}]│       │ .invoke()    │                             │
│     └──────────────┘       └──────────────┘                             │
│                                                                         │
│     Messages.append({                                                    │
│         "role": "assistant",                                            │
│         "tool_calls": [...]                                             │
│     })                                                                   │
│     Messages.append({                                                    │
│         "role": "tool",                                                 │
│         "tool_call_id": call.id,                                        │
│         "content": json.dumps(result)                                   │
│     })                                                                   │
│                                                                         │
│     → 回到 Step 4 (LLM 处理 observation)                                │
│                                                                         │
│  6. ELSE (no tool_calls):                                               │
│     → response.content 即为 Final Answer                                │
│     → 组装 ReActResult(success=True, data=parse(response.content))      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Messages 结构演变

```python
# 初始状态
messages = [
    {"role": "system", "content": system_prompt},   # ← 来自 PromptLoader
    {"role": "user", "content": user_input},         # ← 来自 CLI
]

# LLM 决定调用 Tool
response = provider.chat(messages, tools)
# → LLMResponse(tool_calls=[ToolCall(id="call_1", name="get_course_info", arguments={...})])

# 执行 Tool
result = registry.invoke("get_course_info", course_name="Python")

# 追加到 messages
messages.extend([
    {"role": "assistant", "tool_calls": [{"id": "call_1", "function": {"name": "get_course_info", "arguments": "..."}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": json.dumps(result)},
])

# LLM 继续推理... 或返回 Final Answer
```

---

## 5. 文件修改计划

### M5.1: Provider 抽象层

| 文件 | 操作 | 内容 |
|------|------|------|
| `src/providers/__init__.py` | 新建 | `create_provider()` factory + 导出 |
| `src/providers/base.py` | 新建 | `LLMProvider`(ABC) + `LLMResponse` + `ToolCall` dataclasses |
| `src/providers/deepseek_provider.py` | 新建 | `DeepSeekProvider(LLMProvider)` |
| `src/providers/openai_provider.py` | 新建 | `OpenAIProvider(LLMProvider)` |
| `src/providers/claude_provider.py` | 新建 | `ClaudeProvider(LLMProvider)` |
| `config/.env.example` | 新建 | 环境变量模板 |
| `requirements.txt` | 修改 | 添加 `openai`, `anthropic` (optional) |

### M5.2: Tool Calling Adapter

| 文件 | 操作 | 内容 |
|------|------|------|
| `src/agent/tool_adapter.py` | 新建 | `to_openai_tools(registry) → list[dict]` |

### M5.3: LLM ReAct Agent

| 文件 | 操作 | 内容 |
|------|------|------|
| `src/agent/llm_react.py` | 新建 | `LLMReActAgent` 类 |

### M5.4: Provider 配置

| 文件 | 操作 | 内容 |
|------|------|------|
| `config/__init__.py` | 新建 | `load_config()` — 从 env 加载 |
| `config/settings.py` | 新建 | 配置 dataclass |

### 不变文件

| 文件 | 说明 |
|------|------|
| `src/tools/*` | 4 Tools 完全不变 |
| `src/models/*` | Pydantic Models 完全不变 |
| `src/agent/tool_registry.py` | ToolRegistry 完全不变 |
| `src/agent/runner.py` | AgentRunner 接口不变（仅构造函数 docstring 更新） |
| `src/agent/react_loop.py` | RuleBasedReActAgent 完全不变 |
| `src/agent/prompt_loader.py` | PromptLoader 完全不变 |
| `src/exceptions.py` | 异常类完全不变 |
| `tests/*` | 现有测试完全不变（LLM 测试另建 `tests/test_llm.py`） |

---

## 6. 最小迁移方案

### 从 Rule-based 到 LLM 的改动

```
Phase 1: MVP (current)           Phase 2: LLM (M5)
─────────────────────             ─────────────────

AgentRunner(                      AgentRunner(
    agent=RuleBasedReActAgent()       agent=LLMReActAgent(
)                                         registry=registry,
                                          provider=DeepSeekProvider(api_key),
                                          prompt_loader=PromptLoader(),
                                      )
                                  )

改动量:
- AgentRunner: 0 行 (构造函数已支持 agent 注入)
- ToolRegistry: 0 行
- 4 Tools: 0 行
- Pydantic Models: 0 行
- Trace: 0 行
- 新增: src/providers/ (4 files, ~200 lines)
- 新增: src/agent/llm_react.py (~150 lines)
- 新增: src/agent/tool_adapter.py (~40 lines)
- 新增: config/ (2 files, ~30 lines)
```

### 迁移检查清单

```
□ M5.1: Provider 抽象层 (LLMProvider ABC)
□ M5.2: Tool Calling Adapter (to_openai_tools)
□ M5.3: LLMReActAgent 实现
□ M5.4: Provider 配置 (env-based)
□ 回归测试: 162 tests still pass
□ 新增 LLM 集成测试 (tests/test_llm.py)
```

### 风险控制

| 风险 | 缓解 |
|------|------|
| LLM 幻觉（编造课程信息） | System Prompt 已有反幻觉规则；LLM 模式下更依赖 Prompt 约束 |
| LLM 不遵循 Tool 调用顺序 | System Prompt 注入 workflow 步骤；增加 safety checker |
| API Key 泄露 | 仅从环境变量读取；.env 加入 .gitignore |
| LLM 响应格式不稳定 | Provider 层统一解析为 LLMResponse；异常时 fallback 到错误响应 |
