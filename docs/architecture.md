# Architecture Overview — Course Learning Planner Agent

## 1. High-Level Architecture

```
User CLI ──▶ ReAct Agent Core ──▶ Tool Registry ──▶ 4 Tools ──▶ Data Layer
              │                                        │
              ├── System Prompt                        ├── get_course_info
              ├── ReAct FSM (8 states)                 ├── get_prerequisite
              └── Exception Branches                   ├── calculate_learning_time
                                                       └── generate_learning_plan
                                                           (orchestrator)
```

## 2. Component Descriptions

### 2.1 User Interface (`src/ui/`)
- **cli.py** — Command-line interface using `argparse`
- Accepts: `--course`, `--hours`, `--days`, `--knowledge`, `--json`, `--verbose`

### 2.2 Agent Core (`src/agent/`)
- **react_loop.py** — Implements the ReAct (Reasoning + Acting) loop as a rule-based FSM
- **prompt_loader.py** — Loads and formats `prompts/system_prompt.txt`
- **tool_registry.py** — Registers 4 tools and dispatches tool calls

### 2.3 Tools (`src/tools/`)
- 4 tools, each a standalone function with defined input/output schema
- Tools read from `data/` directory for course information
- See [tool-design.md](tool-design.md) for full specifications

### 2.4 Data Models (`src/models/`)
- Pydantic v2 models for type safety and validation
- `Course`, `Topic`, `LearningPath`, `DailyPlan`, `FeasibilityResult`, `PrerequisiteCheck`

### 2.5 Data Layer (`data/`)
- `courses.json` — 10 courses (Python, SQL, Linux, Git, Java, Hadoop, Hive, Spark, Kafka, Flink)
- `prerequisites.json` — Prerequisite dependency graph (required + recommended)

## 3. ReAct Workflow (4-Tool v2.0.0)

```
Step 1: get_course_info("Python")
    → Course: 24h, beginner, 无先修

Step 2: get_prerequisite("Python", user_knowledge=[])
    → satisfied=true ✅

Step 3: calculate_learning_time("Python", daily_hours=3, duration_days=12)
    → available=36h, needed=24h, buffer=12h, feasible=true ✅

Step 4: generate_learning_plan("Python", 3, 12, skip_optional=false)
    → 学习路径 + 每日计划 + 资源推荐
    → ✅ Final Answer
```

## 4. Exception Handling Flow

### Prerequisites Conflict:
```
get_prerequisite("Spark", user_knowledge=[])
  → satisfied=false, missing=["Python","Hadoop"]
  → Hadoop展开: 还需要 Linux(20h) + Java(32h)
  → 总先修学时: 112h
  → ⚠️ 终止。建议先修路径: Python→Linux→Java→Hadoop→Spark
```

### Time Insufficient:
```
calculate_learning_time("Flink", daily_hours=1, duration_days=10)
  → available=10h, needed=36h, deficit=26h, feasible=false
  → 方案A: 延长至36天
  → 方案B: 增加到3.6h/天
  → 方案C: 缩减至31h(必学)
  → ⚠️ 终止。请选择方案后重新输入参数。
```

### Course Not Found:
```
get_course_info("量子计算")
  → COURSE_NOT_FOUND
  → 列出可用课程: Python, SQL, Linux, Git, Java, Hadoop, Hive, Spark, Kafka, Flink
  → ⚠️ 终止。
```

## 5. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.11+ | Mentor requirement, rapid prototyping |
| Data Models | Pydantic v2 | Type safety, validation, serialization |
| CLI | argparse (stdlib) | Zero dependencies for MVP |
| Testing | pytest | Standard, fixtures, parametrize |
| Data Storage | JSON files | Simple, human-readable, no DB needed |
| Agent Engine | Rule-based FSM (MVP) | Zero API dependency; LLM-ready via subclass |
