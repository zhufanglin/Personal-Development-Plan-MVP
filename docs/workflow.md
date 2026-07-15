# ReAct Workflow — Course Learning Planner Agent

## Overview

The agent uses the **ReAct (Reasoning + Acting)** pattern with 4 tools. MVP: rule-based FSM. Future: LLM-driven ReAct.

## ReAct Loop Pseudocode

```python
def react_loop(course_name, daily_hours, duration_days, user_knowledge=None):
    """ReAct loop: Thought → Action → Observation → repeat → Final Answer"""
    context = ReActState(course_name, daily_hours, duration_days, user_knowledge)
    trace = []

    for step in STEPS:
        thought = step.thought
        action = step.tool_name
        action_input = step.build_params(context)
        observation = execute_tool(action, **action_input)

        trace.append({"thought": thought, "action": action, "observation": observation})
        context.update(observation)

        if observation.get("satisfied") is False:
            return format_prereq_conflict(observation, trace)
        if observation.get("feasible") is False:
            return format_time_insufficient(observation, trace)
        if "error" in observation:
            return format_error(observation, trace)

    return format_final_answer(context, trace)
```

## MVP ReAct STEPS (Rule-Based, 4 Tools)

```python
STEPS = [
    Step(
        thought="首先我需要查询课程信息，确认课程存在并获取学时和先修要求。",
        tool="get_course_info",
        params=lambda ctx: {"course_name": ctx.course_name}
    ),
    Step(
        thought="现在检查用户是否满足先修条件。",
        tool="get_prerequisite",
        params=lambda ctx: {
            "course_name": ctx.course_name,
            "user_knowledge": ctx.user_knowledge or []
        }
    ),
    # Branch: if satisfied=false → PREREQ_CONFLICT (terminal)
    Step(
        thought="先修条件满足。接下来评估时间是否充足。",
        tool="calculate_learning_time",
        params=lambda ctx: {
            "course_name": ctx.course_name,
            "daily_hours": ctx.daily_hours,
            "duration_days": ctx.duration_days
        }
    ),
    # Branch: if feasible=false → TIME_INSUFFICIENT (terminal)
    Step(
        thought="时间充足。现在生成完整的学习计划（路径+每日计划+资源）。",
        tool="generate_learning_plan",
        params=lambda ctx: {
            "course_name": ctx.course_name,
            "daily_hours": ctx.daily_hours,
            "duration_days": ctx.duration_days,
            "skip_optional": False,
            "start_date": None
        }
    ),
]
```

## FSM State Machine (8 States)

```
INIT → GET_COURSE_INFO → GET_PREREQUISITE → CALCULATE_LEARNING_TIME → GENERATE_LEARNING_PLAN → FINAL_ANSWER
                              │                       │
                              ├─ PREREQ_CONFLICT      ├─ TIME_INSUFFICIENT
                              │   (Terminal)          │   (Terminal)
                              │                       │
                              └───────────────────────┘
                           GET_COURSE_INFO
                              │
                              └─ COURSE_NOT_FOUND (Terminal)
```

## Complete Flow — Happy Path

1. Input: `course="Python"`, `daily_hours=3`, `duration_days=12`
2. `get_course_info("Python")` → 24h, beginner, 7 modules, 无先修
3. `get_prerequisite("Python", [])` → satisfied=true, 无缺失
4. `calculate_learning_time("Python", 3, 12)` → feasible=true, available=36h, needed=24h, buffer=12h
5. `generate_learning_plan("Python", 3, 12, False, None)` → 完整学习计划
6. Final Answer ✅

## Complete Flow — Prerequisites Conflict

1. Input: `course="Spark"`, `daily_hours=2`, `duration_days=30`, `knowledge=[]`
2. `get_course_info("Spark")` → 40h, advanced, prereq=[Python, Hadoop]
3. `get_prerequisite("Spark", [])` → satisfied=false, missing=[Python(24h), Hadoop(36h)]
   - Hadoop展开: 还需要 Linux(20h) + Java(32h)
   - 总先修: Python(24h) + Linux(20h) + Java(32h) + Hadoop(36h) = 112h
4. PREREQ_CONFLICT → 终止 ⚠️
5. Agent输出: 缺失先修课列表 + 建议学习路径 + 预估先修周期(56天)

## Complete Flow — Time Insufficient

1. Input: `course="Flink"`, `daily_hours=1`, `duration_days=10`, `knowledge=["Python","Linux","Java","Spark"]`
2. `get_course_info("Flink")` → 36h, advanced, 8 modules
3. `get_prerequisite("Flink", ["Python","Linux","Java","Spark"])` → satisfied=true ✅
4. `calculate_learning_time("Flink", 1, 10)` → feasible=false, available=10h, needed=36h, deficit=26h
5. TIME_INSUFFICIENT → 终止 ⚠️
6. Agent输出: 3种调整方案
   - A: 延长至36天 (1h/天)
   - B: 增加到3.6h/天 (保持10天)
   - C: 缩减至31h (跳过CEP可选模块) — 仍不可行(10h < 31h)

## Complete Flow — Course Not Found

1. Input: `course="量子计算"`, `daily_hours=2`, `duration_days=30`
2. `get_course_info("量子计算")` → error: COURSE_NOT_FOUND
3. COURSE_NOT_FOUND → 终止 ⚠️
4. Agent输出: 可用课程列表 (Python, SQL, Linux, Git, Java, Hadoop, Hive, Spark, Kafka, Flink)

## Exception Branching Diagram

```
get_prerequisite()
    │
    ├─ satisfied=true  → calculate_learning_time()
    │                        │
    │                        ├─ feasible=true  → generate_learning_plan()
    │                        │                        │
    │                        │                        └─ ✅ FINAL_ANSWER
    │                        │
    │                        └─ feasible=false → ⚠️ TIME_INSUFFICIENT
    │                                             (3 options)
    │
    └─ satisfied=false → ⚠️ PREREQ_CONFLICT
                          (missing prereqs + estimated hours)

get_course_info()
    └─ error → ⚠️ COURSE_NOT_FOUND
                (available courses)
```
