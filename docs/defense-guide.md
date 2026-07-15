# MVP Defense — Course Learning Planner Agent

## 10 分钟演示脚本

### [0:00-1:00] 开场

```
大家好。我今天展示的是一个 AI Agent MVP:
Course Learning Planner Agent。

核心问题: 传统 Chatbot 会编造课程信息。
解决方案: Agent 必须通过 Tool 获取信息，禁止幻觉。
```

### [1:00-3:00] 离线 Demo: 课程规划

```bash
python demo.py --course Python --hours 3 --days 12
```

展示:
- RuleBasedReActAgent 自动调用 4 个 Tool
- 输出: 7 个模块 / 10 天计划 / 9 条资源 / 13 步 Trace
- 重点: **Agent 没有硬编码课程信息 — 所有数据来自 Tool**

### [3:00-5:00] 离线 Demo: 先修冲突

```bash
python demo.py --prereq
```

展示:
- Spark 需要 Python + Hadoop, Hadoop 需要 Linux + Java
- Agent 在第 2 步检测到 `satisfied=false` → 立即终止
- **不浪费后续 calculate_learning_time 和 generate_learning_plan 调用**
- 输出: 4 门缺失先修课 / 112h 总先修学时

### [5:00-7:00] LLM Demo: Tool Calling

```bash
export DEEPSEEK_API_KEY="sk-..."
python demo.py --llm --calculator
```

展示:
- LLM 自主决定调用 calculator tool
- 不是 hardcoded — LLM 通过 System Prompt 理解 tools schema
- `234 * 567 = 132678`

### [7:00-9:00] 架构讲解

```
User → AgentRunner → LLMReActAgent → DeepSeek API
                         │
                    ToolRegistry
                         │
                    ┌────┴────┐
                    │ 6 Tools │
                    └─────────┘

关键设计:
1. Agent 不 import Tool — 通过 ToolRegistry 解耦
2. Provider 抽象 — DeepSeek 可替换为 OpenAI/Claude
3. ReAct 循环 — Thought → Action → Observation
4. Trace — 每一步可审计 (13 步完整记录)
```

### [9:00-10:00] 总结

```
三个核心能力:
1. 工具调用 — Agent 的信息来源是 Tool，不是模型记忆
2. 动态推理 — LLM 自主选择调用哪个 Tool
3. 多步编排 — 4 步课程规划流程，自动阻断异常

技术栈: Python 3.12 / Pydantic v2 / DeepSeek API / pytest
测试: 162 tests / ~90% coverage
代码: ~800 lines src/ + ~500 lines tests/
```

## Demo 命令速查

| 场景 | 命令 |
|------|------|
| 课程规划 | `python demo.py --course Python --hours 3 --days 12` |
| 先修冲突 | `python demo.py --prereq` |
| LLM 计算器 | `python demo.py --llm --calculator` |
| LLM 天气 | `python demo.py --llm --weather` |
| 全部测试 | `pytest tests/ -v` |
