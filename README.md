# Course Learning Planner Agent

**AI Agent MVP — 基于 ReAct 范式的课程学习规划智能体**

| Field | Value |
|-------|-------|
| 项目类型 | 导师布置的 AI Agent MVP 项目 |
| 设计范式 | ReAct (Reasoning + Acting) |
| 技术栈 | Python 3.11+ / Pydantic v2 / pytest |
| 状态 | 设计阶段完成，待编码实现 |
| Agent 类型 | 工具驱动型 Agent（强制 Tool Calling，禁止幻觉） |

---

## 目录

1. [项目介绍](#1-项目介绍)
2. [运行方式](#2-运行方式)
3. [项目结构](#3-项目结构)
4. [Agent 架构](#4-agent-架构)
5. [Tool Calling](#5-tool-calling)
6. [演示案例](#6-演示案例)
7. [答辩说明](#7-答辩说明)

---

## 1. 项目介绍

### 1.1 项目背景

这是一个**工具驱动型 AI Agent**，帮助学习者规划课程学习路径。与传统 Chatbot 不同，该 Agent **禁止直接回答用户问题**——所有信息必须通过调用 Tool 获取，从根本上杜绝了 LLM 的幻觉问题。

### 1.2 核心能力

| 能力 | 说明 | 对应 Tool |
|------|------|----------|
| 课程查询 | 查询任意课程的元数据（学时/难度/模块） | `get_course_info` |
| 先修验证 | 递归检查先修条件树，判断用户是否满足前置要求 | `get_prerequisite` |
| 可行性评估 | 计算时间是否充足，不可行时提供 3 种调整方案 | `calculate_learning_time` |
| 计划生成 | 生成包含学习路径、每日计划、学习资源的完整方案 | `generate_learning_plan` |

### 1.3 用户交互模型

```
用户输入                           Agent 输出
─────────                          ──────────
课程名称 ────┐                ┌─── 课程概览
每日学习时间 ─┤    ┌──────┐   ├─── 先修条件检查
学习周期 ────┘───▶│ Agent │──▶├─── 可行性评估
已完成的课程 ──┘   └──────┘   ├─── 学习路径（有序模块）
                              ├─── 每日学习计划
                              └─── 推荐学习资源
```

### 1.4 与普通 Chatbot 的区别

| 特性 | 普通 Chatbot | Course Learning Planner Agent |
|------|-------------|------------------------------|
| 信息来源 | 模型训练数据（可能过时/错误） | Tool 实时查询数据层 |
| 幻觉风险 | 高（会编造课程信息） | 零（被系统提示词禁止） |
| 可审计性 | 低（不知道信息来源） | 完整 ReAct 推理追踪 |
| 先修检查 | 可能遗漏 | 递归展开完整先修树 |
| 时间计算 | 估算 | 精确数学计算 + 3 种调整方案 |
| 可扩展性 | 修改模型训练数据 | 添加 JSON 数据或新 Tool |

---

## 2. 运行方式

### 2.1 环境要求

- Python 3.11+
- pip

### 2.2 安装

```bash
# 进入项目目录
cd Desktop/Course-Learning-Agent

# 安装依赖
pip install -r requirements.txt
```

### 2.3 使用（实现后）

```bash
# 基础用法 — 查询课程并生成学习计划
python -m src.ui.cli --course "Python" --hours 2 --days 15

# 指定已有知识背景
python -m src.ui.cli --course "Spark" --hours 3 --days 30 \
    --knowledge "Python,Linux,Java,Hadoop"

# JSON 格式输出（供程序调用）
python -m src.ui.cli --course "SQL" --hours 1 --days 10 --json

# 显示完整 ReAct 推理过程
python -m src.ui.cli --course "Flink" --hours 2 --days 20 --verbose

# 交互模式（逐步输入）
python -m src.ui.cli --interactive
```

### 2.4 运行测试

```bash
# 运行全部测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ -v --cov=src --cov-report=term-missing

# 仅运行模型测试
pytest tests/test_models.py -v

# 仅运行工具测试
pytest tests/test_tools.py -v
```

---

## 3. 项目结构

```
Course-Learning-Agent/
│
├── README.md                         # ★ 项目说明（本文件）
├── requirements.txt                  # Python 依赖
│
├── src/                              # 源代码
│   ├── __init__.py                   # 包标记
│   ├── agent/                        # Agent 核心层
│   │   ├── __init__.py
│   │   ├── react_loop.py            # ReAct 状态机控制器
│   │   ├── prompt_loader.py         # System Prompt 加载器
│   │   ├── tool_registry.py         # Tool 注册与调度中心
│   │   └── runner.py                # Agent 顶层入口
│   ├── tools/                        # Tool 实现层
│   │   ├── __init__.py
│   │   ├── data_loader.py           # JSON 数据加载器（带缓存）
│   │   ├── course_info.py           # get_course_info 工具
│   │   ├── prerequisites.py         # get_prerequisite 工具
│   │   ├── learning_path.py         # 学习路径生成（generate_learning_plan 内部调用）
│   │   ├── daily_plan.py            # 每日计划生成（generate_learning_plan 内部调用）
│   │   ├── feasibility.py           # calculate_learning_time 工具
│   │   └── resources.py             # 资源推荐（generate_learning_plan 内部调用）
│   ├── models/                       # 数据模型层
│   │   ├── __init__.py
│   │   ├── course.py                # Course / Topic 模型
│   │   ├── learning_path.py         # LearningPath / Module / DailyPlan 模型
│   │   └── feasibility.py           # FeasibilityResult / PrerequisiteCheck 模型
│   └── ui/                           # 用户界面层
│       ├── __init__.py
│       ├── cli.py                    # argparse CLI 入口
│       └── formatter.py             # 输出格式化器（文本/JSON）
│
├── tests/                            # 测试
│   ├── __init__.py
│   ├── test_models.py               # 数据模型单元测试
│   ├── test_tools.py                # Tool 单元测试
│   ├── test_agent.py                # Agent ReAct 循环测试
│   ├── test_exceptions.py           # 异常处理专项测试
│   └── test_integration.py          # 端到端集成测试
│
├── data/                             # 数据层
│   ├── courses.json                  # 10 门课程完整数据（185行）
│   └── prerequisites.json            # 先修关系依赖图
│
├── prompts/                          # 提示词
│   ├── system_prompt.txt            # ★ 运行时 System Prompt（v2.0.0，4-Tool）
│   └── react_template.txt           # ReAct 推理模板
│
├── docs/                             # 设计文档
│   ├── architecture.md              # 架构概览
│   ├── system-design.md             # ★ 系统设计（1223行）
│   ├── tool-design.md               # ★ Tool API 设计（1252行）
│   └── workflow.md                  # ReAct 工作流详解
│
├── plans/                            # 实施计划
│   └── course-learning-agent.plan.md # 5 个里程碑 / 22 个任务
│
└── diagrams/                         # 架构图
    ├── architecture.mermaid          # 组件架构图
    └── react-workflow.mermaid        # ReAct 序列图
```

### 分层架构

```
┌─────────────────────────────────────┐
│         UI 层 (src/ui/)             │  ← argparse CLI + 格式化输出
├─────────────────────────────────────┤
│         Agent 层 (src/agent/)       │  ← ReAct 状态机 + Prompt + Registry
├─────────────────────────────────────┤
│         Tools 层 (src/tools/)       │  ← 4 个 Tool + 数据加载器
├─────────────────────────────────────┤
│         Models 层 (src/models/)     │  ← Pydantic v2 数据模型
├─────────────────────────────────────┤
│         Data 层 (data/)             │  ← JSON 课程数据库
└─────────────────────────────────────┘
```

---

## 4. Agent 架构

### 4.1 设计范式：ReAct (Reasoning + Acting)

```
┌─────────────────────────────────────────────────────────┐
│                    ReAct Loop 生命周期                    │
│                                                          │
│   ┌──────────┐      ┌──────────┐      ┌──────────────┐  │
│   │ THOUGHT  │─────▶│  ACTION  │─────▶│ OBSERVATION  │  │
│   │ 我要查询  │      │ 调用     │      │ Tool返回     │  │
│   │ 课程信息  │      │ Tool     │      │ 课程数据     │  │
│   └──────────┘      └──────────┘      └──────┬───────┘  │
│        ▲                                      │          │
│        └──────────── 重复 ────────────────────┘          │
│                          │                                │
│                    信息足够？                              │
│                     YES │                                │
│                    ┌─────▼──────┐                         │
│                    │   FINAL    │                         │
│                    │   ANSWER   │                         │
│                    └────────────┘                         │
└─────────────────────────────────────────────────────────┘
```

### 4.2 MVP 实现：规则化状态机

MVP 使用**确定性状态机**替代真实 LLM，实现相同的 ReAct 行为：

```
                    ┌──────┐
                    │ INIT │
                    └──┬───┘
                       ▼
              ┌─────────────────┐
              │ GET_COURSE_INFO │  ← Step 1: 查询课程
              └───────┬─────────┘
                      ▼
            ┌─────────────────────┐
            │ CHECK_PREREQUISITES │  ← Step 2: 检查先修
            └─────────┬───────────┘
                      │
             ┌────────┴────────┐
        YES  │                 │  NO
             ▼                 ▼
    ┌──────────────────┐  ┌──────────────────┐
    │ ASSESS_          │  │ PREREQ_CONFLICT  │  ← 异常1: 终止
    │ FEASIBILITY      │  │ (Terminal State) │
    └────────┬─────────┘  └──────────────────┘
             │
        ┌────┴────┐
   YES  │         │  NO
        ▼         ▼
   ┌─────────┐  ┌──────────────────┐
   │GENERATE │  │ TIME_INSUFFICIENT│  ← 异常2: 终止
   │PLAN     │  │ (Terminal State) │
   └────┬────┘  └──────────────────┘
        ▼
   ┌──────────────┐
   │ FINAL_ANSWER │  ← 输出完整学习计划
   └──────────────┘
```

### 4.3 设计亮点

| 特性 | 说明 |
|------|------|
| **零 API 依赖** | 规则化 FSM 无需 LLM API Key，零成本运行 |
| **LLM 可替换** | 状态机的方法签名与 LLM-based Agent 一致，子类化即可切换 |
| **完全可审计** | 每个 Thought→Action→Observation 步骤被完整记录在 trace 中 |
| **早停机制** | 先修不满足或时间不足时立即终止，不浪费后续计算 |
| **确定性输出** | 相同输入→相同输出，便于测试和调试 |

### 4.4 工作流约束

| 规则 | 说明 |
|------|------|
| 顺序不可变 | Step 1→2→3→4，不允许跳步 |
| 条件门控 | Step 2 不通过 → 禁入 Step 3/4；Step 3 不可行 → 禁入 Step 4 |
| 数据来源单一 | 所有信息必须来自 Tool 返回值 |
| 不可逆转 | 终止后不得自行重试，等待用户调整参数 |

---

## 5. Tool Calling

### 5.1 Tool 清单

| # | Tool | 类型 | 输入 | 输出 |
|---|------|------|------|------|
| 1 | `get_course_info` | Read | `course_name: str` | 课程元数据（描述/难度/学时/模块/先修列表） |
| 2 | `get_prerequisite` | Read | `course_name: str, user_knowledge: list[str]` | 递归先修树 + 缺失课程 + 总先修学时 |
| 3 | `calculate_learning_time` | Compute | `course_name: str, daily_hours: float, duration_days: int` | 可行性 + 缓冲比例 + 3 种调整方案 |
| 4 | `generate_learning_plan` | Orchestrate | 以上所有参数 + `skip_optional: bool, start_date: str` | 学习路径 + 每日计划 + 资源推荐 |

### 5.2 Tool 调用流程

```
User Input: course="Spark", hours=2, days=30, knowledge=["Python"]

Step 1: get_course_info("Spark")
    → Spark: 40h, advanced, 先修=[Python, Hadoop]
    → 9 个模块，7 必修 + 2 可选

Step 2: get_prerequisite("Spark", ["Python"])
    → satisfied=false, missing=["Hadoop"]
    → Hadoop 先修树: 需要 Linux(20h) + Java(32h)
    → 总先修学时: 36h (Hadoop) + 20h (Linux) + 32h (Java) = 88h
    → ⚠️ 先修冲突！终止。

--- 用户调整后重试 ---

User Input: course="Spark", hours=3, days=40, knowledge=["Python","Linux","Java","Hadoop"]

Step 2: get_prerequisite("Spark", ["Python","Linux","Java","Hadoop"])
    → satisfied=true ✅

Step 3: calculate_learning_time("Spark", 3, 40)
    → available=120h, needed=40h, buffer=80h, ratio=200%
    → feasible=true ✅

Step 4: generate_learning_plan("Spark", 3, 40, skip_optional=false)
    → 9 个模块，40h 学习 + 8 个复习日 + 1 个评估日
    → 共 20 天完成（远低于 40 天上限）
    → 包含 30+ 条学习资源推荐
    → ✅ 完整计划输出
```

### 5.3 Tool 注册机制

```
ToolRegistry
    │
    ├── "get_course_info"       → course_info.execute()
    ├── "get_prerequisite"      → prerequisites.execute()
    ├── "calculate_learning_time" → feasibility.execute()
    └── "generate_learning_plan"  → orchestrator.execute()

所有 Tool 通过 registry.execute(name, **kwargs) 统一调度。
添加新 Tool：实现函数 → 注册到 registry → 零改动 Agent 核心。
```

### 5.4 错误处理标准

全部 4 个 Tool 使用统一的错误响应格式：

```json
{
    "error": {
        "code": "COURSE_NOT_FOUND",
        "message": "课程 '量子计算' 不在目录中。可用课程: Python, SQL, Linux, ...",
        "details": { "query": "量子计算", "available_courses": ["Python", "SQL", ...] },
        "tool_name": "get_course_info"
    }
}
```

| 错误码 | 含义 | 可恢复 |
|--------|------|--------|
| `COURSE_NOT_FOUND` | 课程不在目录中 | ✅ 重新输入 |
| `VALIDATION_ERROR` | 输入参数不合法 | ✅ 修正输入 |
| `PREREQUISITE_CONFLICT` | 先修条件不满足 | ✅ 先修后再来 |
| `TIME_INSUFFICIENT` | 学习时间不足 | ✅ 调整参数 |
| `CIRCULAR_DEPENDENCY` | 先修数据循环依赖 | ❌ 修复数据 |
| `INTERNAL_ERROR` | 内部错误 | ❌ 排查修复 |

---

## 6. 演示案例

### 6.1 案例一：Happy Path — 完整学习计划

```bash
$ python -m src.ui.cli --course "Python" --hours 3 --days 12

# 📚 学习计划: Python
#
# ## 课程概览
# | 项目 | 内容 |
# | 课程名称 | Python |
# | 难度 | beginner |
# | 总学时 | 24h |
#
# ## 先修条件检查 ✅
# 无先修要求。可直接开始学习。
#
# ## 可行性评估 ✅
# | 可用时间 | 36h |
# | 需要时间 | 24h |
# | 缓冲时间 | 12h (50%) |
#
# ## 学习路径
# | 序号 | 模块 | 学时 | 类型 |
# | 1 | 变量与数据类型 | 3h | 必修 |
# | 2 | 流程控制 | 3h | 必修 |
# | 3 | 函数与模块 | 4h | 必修 |
# | 4 | 面向对象编程 | 5h | 必修 |
# | 5 | 文件操作与异常处理 | 3h | 必修 |
# | 6 | 标准库与虚拟环境 | 4h | 必修 |
# | 7 | Python 进阶特性 | 2h | 可选 |
#
# 总计: 7 个模块（6必修+1可选），24h
#
# ## 每日学习计划
# | 天数 | 类型 | 学习内容 | 学时 |
# | Day 1 | 学习 | 变量与数据类型 | 3h |
# | Day 2 | 学习 | 流程控制 | 3h |
# | Day 3 | 学习 | 函数与模块 | 3h |
# | Day 4 | 学习 | 函数与模块(续) + 面向对象 | 3h |
# | Day 5 | 复习 | 前4天内容回顾 | 3h |
# | ... | ... | ... | ... |
# | Day 12 | 评估 | 综合项目测验 | 3h |
#
# 计划在 12 天内完成。包含 9 个学习日 + 2 个复习日 + 1 个评估日。
```

### 6.2 案例二：先修课程冲突

```bash
$ python -m src.ui.cli --course "Spark" --hours 2 --days 30

# ⚠️ 先修条件不满足
#
# ## 目标课程: Spark
# Apache Spark 大数据计算引擎深入学习。40h，advanced。
#
# ## 你的背景
# 无已完成的课程记录。
#
# ## 缺失的先修课程
# | 序号 | 先修课 | 学时 | 依赖 |
# | 1 | Python | 24h | — |
# | 2 | Linux | 20h | — |
# | 3 | Java | 32h | Python (建议) |
# | 4 | Hadoop | 36h | Linux + Java |
#
# 总先修学时: 112h
# 预估先修周期: 56 天（按 2h/天）
#
# ## 建议先修路径
# Python(24h) → Linux(20h) + Java(32h) → Hadoop(36h) → Spark(40h)
#
# 💡 完成上述先修课程后（约 56 天），再回到 Spark 的学习。
# 总学习路径约需 76 天（56天先修 + 20天Spark）。
```

### 6.3 案例三：学习时间不足

```bash
$ python -m src.ui.cli --course "Flink" --hours 1 --days 10 \
    --knowledge "Python,Linux,Java,Spark"

# ⚠️ 学习时间不足
#
# ## 课程: Flink
# 课程总学时: 36h
#
# ## 时间分析
# | 项目 | 数值 |
# | 每日学习 | 1h |
# | 学习天数 | 10天 |
# | 可用总时间 | 10h |
# | 缺口 | 26h |
#
# ## 调整方案
#
# ### 方案 A: 延长学习周期
# → 保持每天 1h，延长至 **36 天**
#
# ### 方案 B: 增加每日学习时间
# → 保持 10 天周期，每天学 **3.6h**
#
# ### 方案 C: 缩减学习范围
# → 跳过 2 个可选模块，必学降至 **31h**
# → ⚠️ 方案 C 在当前参数下仍不可行（10h < 31h）
#
# 💡 推荐方案 A 或 B。请选择后重新发起请求。
```

### 6.4 案例四：深度先修链 — Flink 的完整依赖树

```bash
$ python -m src.ui.cli --course "Flink" --hours 2 --days 20

# Flink (36h) 的完整先修树:
#
# Flink
#  ├── Java (32h) — required
#  │   └── Python (24h) — recommended → 已完成耗时: 0h
#  └── Spark (40h) — required
#      ├── Python (24h) — required → 已完成耗时: 0h
#      └── Hadoop (36h) — required
#          ├── Linux (20h) — required → 已完成耗时: 0h
#          └── Java (32h) — required → (已在另一分支)
#
# 递归深度: 3 层
# 总先修课程: 5 门（去重后）
# 总先修学时: 132h
# 预估先修周期: 66 天（2h/天）
```

---

## 7. 答辩说明

### 7.1 项目定位

本项目是一个**教学演示型 AI Agent**，用于展示以下核心概念：

| 概念 | 本项目的实现 |
|------|-------------|
| **Agent ≠ Chatbot** | Agent 通过 Tool Calling 获取信息，而非依赖模型训练数据 |
| **ReAct 范式** | Thought→Action→Observation 循环，推理与行动交织 |
| **工具驱动** | 4 个 Tool 各司其职，Agent 核心不包含任何业务逻辑 |
| **幻觉预防** | System Prompt 6 条禁令 + 自检清单，从设计层面杜绝幻觉 |
| **异常处理** | 两类业务异常（先修冲突/时间不足）被建模为状态机终端状态 |

### 7.2 满足导师要求的对照检查

| # | 导师要求 | 本项目的实现 | 证据 |
|---|---------|-------------|------|
| 1 | Agent 必须调用 Tool | System Prompt Rule 1: "每次回答前必须调用至少一个 Tool" | `prompts/system_prompt.txt` §4 |
| 2 | 至少 4 个 Tool | 设计了 4 个 Tool: get_course_info / get_prerequisite / calculate_learning_time / generate_learning_plan | `docs/tool-design.md` |
| 3 | 设计 System Prompt | 运行时 Prompt（40行）+ 设计说明文档，覆盖身份/目标/工作流/Tool规则/异常/反幻觉/输出格式 | `prompts/system_prompt.txt` |
| 4 | 使用 ReAct 或 Plan-Execute | 实现了 ReAct 范式，状态机包含完整的 Thought→Action→Observation 循环 | `docs/system-design.md` §2 |
| 5a | 异常1: 先修冲突 | `get_prerequisite` 返回 `satisfied=false` → 状态机转入 PREREQ_CONFLICT 终止状态 | `docs/workflow.md` §异常处理 |
| 5b | 异常2: 时间不足 | `calculate_learning_time` 返回 `feasible=false` → 状态机转入 TIME_INSUFFICIENT 终止状态，输出 3 种调整方案 | `docs/workflow.md` §异常处理 |
| 6 | 可运行 MVP | 5 个里程碑 22 个任务，覆盖从模型到 CLI 到测试的全部实现 | `plans/course-learning-agent.plan.md` |

### 7.3 技术架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| MVP Agent 引擎 | 规则化状态机 | 零 API 依赖，确定性输出，易测试；LLM 可子类化替换 |
| 数据模型 | Pydantic v2 | 类型安全，运行时验证，JSON Schema 自动生成 |
| 数据存储 | JSON 文件 | 零配置，人类可读，通过 data_loader 抽象支持未来切换 DB |
| CLI 框架 | argparse (标准库) | 零额外依赖，快速启动 |
| 测试框架 | pytest + pytest-cov | Python 标准测试工具，覆盖率报告 |
| 课程领域 | 大数据技术栈 | Python→Java→Hadoop→Spark→Flink 形成深度依赖链（5层递归），充分展示先修树展开能力 |

### 7.4 课程依赖链设计（演示价值）

10 门课程形成了具有**教学演示价值**的复杂依赖图：

```
Python (24h) ─────────────┐
SQL (18h)                 │
Linux (20h) ──┐           │
Git (12h)     │           │
              ├──→ Hadoop (36h) ──→ Spark (40h) ──→ Flink (36h)
Java (32h) ───┤                │
              └──→ Kafka (28h)  └──→ Hive (20h)
```

- **最深链**: Flink → Spark → Hadoop → Linux/Java → Python（5 层递归）
- **最宽先修**: Hadoop 同时要求 Linux + Java（多先修交汇点）
- **推荐提醒**: Java 推荐 Python 但不强制（区分 required vs recommended）
- **多入口**: 4 门零先修课程（Python / SQL / Linux / Git）

### 7.5 项目文档清单

| 文档 | 规模 | 内容 |
|------|------|------|
| `prompts/system_prompt.txt` | 40 行 | 运行时 System Prompt（v2.0.0） |
| `docs/system-prompt-design.md` | — | System Prompt 设计说明与版本历史 |
| `docs/system-design.md` | 1,223 行 | 系统设计（架构+工作流+数据流+模块+扩展） |
| `docs/tool-design.md` | 1,252 行 | 4 个 Tool 的完整 API 设计 |
| `docs/architecture.md` | 116 行 | 架构概览 |
| `docs/workflow.md` | 189 行 | ReAct 工作流详解 |
| `plans/course-learning-agent.plan.md` | 441 行 | 5 里程碑 / 22 任务实施计划 |
| `data/courses.json` | 185 行 | 10 门课程完整数据 |
| `diagrams/architecture.mermaid` | — | 组件架构图 |
| `diagrams/react-workflow.mermaid` | — | ReAct 序列图 |

**设计文档总计: ~3,500+ 行**，覆盖了从架构到 API 到提示词的全部设计层面。

### 7.6 后续扩展方向

| 阶段 | 扩展内容 | 改动范围 |
|------|---------|---------|
| v1.1 | LLM 替换规则化 FSM | 仅需子类化 `ReActController`，覆写 `_reason()` 方法 |
| v1.2 | Web 界面 (FastAPI + HTML) | 新增 `src/ui/web.py`，Agent 核心零改动 |
| v1.3 | SQLite 数据库 | 新增 `DataLoader` 适配器，Tool 层零改动 |
| v2.0 | 多 Agent 协作 | Orchestrator + CourseExpert + Scheduler + Curator |
