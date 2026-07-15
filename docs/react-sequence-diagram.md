# ReAct Sequence Diagrams — Task 3.2

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-07-11 |
| Parent | `docs/react-fsm-design.md` |

---

## 1. Sequence Diagram: 成功流程

```mermaid
sequenceDiagram
    actor User
    participant Runner
    participant Agent as ReActAgent
    participant Registry as ToolRegistry
    participant Tool

    User->>Runner: run_agent("Python", 3, 12, [])
    Runner->>Agent: run(course_name, daily_hours, duration_days, user_knowledge)

    Note over Agent: State: IDLE
    Agent->>Agent: init ReActState(course, hours, days, knowledge)
    Agent->>Agent: init trace = []

    Note over Agent: State: IDLE → THINKING

    rect rgb(255, 248, 220)
        Note over Agent: ★ Trace #1: THINKING
        Agent->>Agent: thought = "查询'Python'课程信息，获取学时和先修要求。"
        Agent->>Agent: trace.append(step=1, state=THINKING, thought=...)
    end

    Note over Agent: State: THINKING → TOOL_SELECTION → TOOL_EXECUTION

    Agent->>Registry: invoke("get_course_info", course_name="Python")

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace #2: TOOL_EXECUTION (input)
    end

    Registry->>Tool: get_course_info("Python")
    Tool-->>Registry: {"success": true, "data": {"name": "Python", "hours": 24, ...}}

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace #3: TOOL_EXECUTION (output)
    end

    Registry-->>Agent: tool_result

    Note over Agent: State: TOOL_EXECUTION → OBSERVATION

    Agent->>Agent: result["success"] == true ✅
    Agent->>Agent: state.course_data = result["data"]
    Agent->>Agent: blocker_check() → None (continue)

    Note over Agent: State: OBSERVATION → THINKING (loop)

    rect rgb(255, 248, 220)
        Note over Agent: ★ Trace #4: THINKING
        Agent->>Agent: thought = "检查用户是否满足'Python'的先修条件。"
        Agent->>Agent: trace.append(step=4, state=THINKING, thought=...)
    end

    Agent->>Registry: invoke("get_prerequisite", course_name="Python", user_knowledge=[])

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace #5-6: TOOL_EXECUTION
    end

    Registry->>Tool: get_prerequisite("Python", [])
    Tool-->>Registry: {"success": true, "data": {"satisfied": true, "missing": [], ...}}
    Registry-->>Agent: tool_result

    Note over Agent: State: OBSERVATION

    Agent->>Agent: result["data"]["satisfied"] == true ✅
    Agent->>Agent: blocker_check() → None (continue)

    Note over Agent: State: OBSERVATION → THINKING (loop)

    rect rgb(255, 248, 220)
        Note over Agent: ★ Trace #7: THINKING
        Agent->>Agent: thought = "评估时间可行性: 3h/天 × 12天。"
    end

    Agent->>Registry: invoke("calculate_learning_time", course_name="Python", daily_hours=3, duration_days=12)

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace #8-9: TOOL_EXECUTION
    end

    Registry->>Tool: calculate_learning_time("Python", 3, 12)
    Tool-->>Registry: {"success": true, "data": {"feasible": true, "buffer_hours": 12, ...}}
    Registry-->>Agent: tool_result

    Note over Agent: State: OBSERVATION

    Agent->>Agent: result["data"]["feasible"] == true ✅
    Agent->>Agent: blocker_check() → None (continue)

    Note over Agent: State: OBSERVATION → THINKING (loop)

    rect rgb(255, 248, 220)
        Note over Agent: ★ Trace #10: THINKING
        Agent->>Agent: thought = "生成完整学习计划。"
    end

    Agent->>Registry: invoke("generate_learning_plan", course_name="Python", daily_hours=3, duration_days=12, user_knowledge=[])

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace #11-12: TOOL_EXECUTION
    end

    Registry->>Tool: generate_learning_plan("Python", 3, 12, False, None, [])
    Tool-->>Registry: {"success": true, "data": {"plan_id": "...", "learning_path": [...], ...}}
    Registry-->>Agent: tool_result

    Note over Agent: State: OBSERVATION

    Agent->>Agent: result["success"] == true ✅
    Agent->>Agent: EXECUTION_PLAN exhausted → all done

    Note over Agent: State: OBSERVATION → RESPONSE

    rect rgb(255, 240, 240)
        Note over Agent: ★ Trace #13: RESPONSE
        Agent->>Agent: ReActResult(success=true, data=state, trace=trace)
    end

    Note over Agent: State: RESPONSE → FINISHED

    Agent-->>Runner: ReActResult(success=true, data=plan, trace=13 entries)
    Runner-->>User: ✅ 完整学习计划输出
```

---

## 2. Sequence Diagram: PREREQUISITE_CONFLICT 失败流程

```mermaid
sequenceDiagram
    actor User
    participant Runner
    participant Agent as ReActAgent
    participant Registry as ToolRegistry
    participant Tool

    User->>Runner: run_agent("Spark", 2, 30, [])
    Runner->>Agent: run("Spark", 2, 30, knowledge=[])

    Note over Agent: IDLE → THINKING → TOOL_EXECUTION

    Agent->>Registry: invoke("get_course_info", course_name="Spark")

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace: THINKING + TOOL_EXECUTION × 2
    end

    Registry->>Tool: get_course_info("Spark")
    Tool-->>Registry: {"success": true, "data": {"name": "Spark", "hours": 40, ...}}
    Registry-->>Agent: tool_result

    Note over Agent: OBSERVATION

    Agent->>Agent: success=true, state.course_data = result["data"]
    Agent->>Agent: blocker_check() → None (continue)

    Note over Agent: THINKING (loop) → TOOL_EXECUTION

    Agent->>Registry: invoke("get_prerequisite", course_name="Spark", user_knowledge=[])

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace: THINKING + TOOL_EXECUTION × 2
    end

    Registry->>Tool: get_prerequisite("Spark", [])
    Tool-->>Registry: {"success": true, "data": {"satisfied": false, "missing": ["Python","Hadoop","Linux","Java"], "total_prerequisite_hours": 112, ...}}
    Registry-->>Agent: tool_result

    Note over Agent: OBSERVATION

    Agent->>Agent: result["success"] == true ✅
    Agent->>Agent: result["data"]["satisfied"] == false ⚠️
    Agent->>Agent: blocker_check() → "PREREQ_CONFLICT"

    rect rgb(255, 200, 200)
        Note over Agent: ⚠️ BLOCKER DETECTED
        Agent->>Agent: 不继续 calculate_learning_time
        Agent->>Agent: 不继续 generate_learning_plan
    end

    Note over Agent: OBSERVATION → RESPONSE (terminal)

    rect rgb(255, 240, 240)
        Note over Agent: ★ Trace: RESPONSE
        Agent->>Agent: ReActResult(
        Agent->>Agent:   success=false,
        Agent->>Agent:   error={"code": "PREREQUISITE_CONFLICT",
        Agent->>Agent:          "details": {"missing": [...], "total_hours": 112}},
        Agent->>Agent:   trace=[...])
    end

    Note over Agent: RESPONSE → FINISHED

    Agent-->>Runner: ReActResult(success=false, error=PREREQ_CONFLICT, trace)
    Runner-->>User: ⚠️ 先修条件不满足<br/>缺失: Python(24h) + Linux(20h) + Java(32h) + Hadoop(36h)<br/>总先修学时: 112h
```

---

## 3. Sequence Diagram: TIME_INSUFFICIENT 失败流程

```mermaid
sequenceDiagram
    actor User
    participant Runner
    participant Agent as ReActAgent
    participant Registry as ToolRegistry
    participant Tool

    User->>Runner: run_agent("Flink", 1, 10, ["Python","Linux","Java","Spark"])
    Runner->>Agent: run("Flink", 1, 10, knowledge=["Python","Linux","Java","Spark"])

    Note over Agent: IDLE → THINKING → TOOL_EXECUTION

    Agent->>Registry: invoke("get_course_info", course_name="Flink")

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace: THINKING + TOOL_EXECUTION × 2
    end

    Registry->>Tool: get_course_info("Flink")
    Tool-->>Registry: {"success": true, "data": {"name": "Flink", "hours": 36, ...}}
    Registry-->>Agent: tool_result

    Note over Agent: OBSERVATION → THINKING (loop)

    Agent->>Agent: success=true, blocker=None → continue

    Agent->>Registry: invoke("get_prerequisite", course_name="Flink", user_knowledge=["Python","Linux","Java","Spark"])

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace: THINKING + TOOL_EXECUTION × 2
    end

    Registry->>Tool: get_prerequisite("Flink", ["Python","Linux","Java","Spark"])
    Tool-->>Registry: {"success": true, "data": {"satisfied": true, "missing": [], ...}}
    Registry-->>Agent: tool_result

    Note over Agent: OBSERVATION

    Agent->>Agent: result["data"]["satisfied"] == true ✅
    Agent->>Agent: blocker_check() → None (continue)

    Note over Agent: THINKING (loop) → TOOL_EXECUTION

    Agent->>Registry: invoke("calculate_learning_time", course_name="Flink", daily_hours=1, duration_days=10)

    rect rgb(240, 255, 240)
        Note over Registry: ★ Trace: THINKING + TOOL_EXECUTION × 2
    end

    Registry->>Tool: calculate_learning_time("Flink", 1, 10)
    Tool-->>Registry: {"success": true, "data": {"feasible": false, "available_hours": 10, "course_total_hours": 36, "adjustment_options": [...]}}
    Registry-->>Agent: tool_result

    Note over Agent: OBSERVATION

    Agent->>Agent: result["success"] == true ✅
    Agent->>Agent: result["data"]["feasible"] == false ⚠️
    Agent->>Agent: blocker_check() → "TIME_INSUFFICIENT"

    rect rgb(255, 200, 200)
        Note over Agent: ⚠️ BLOCKER DETECTED
        Agent->>Agent: 不继续 generate_learning_plan
        Agent->>Agent: 但保留 adjustment_options 供用户参考
    end

    Note over Agent: OBSERVATION → RESPONSE (terminal)

    rect rgb(255, 240, 240)
        Note over Agent: ★ Trace: RESPONSE
        Agent->>Agent: ReActResult(
        Agent->>Agent:   success=false,
        Agent->>Agent:   error={"code": "TIME_INSUFFICIENT",
        Agent->>Agent:          "details": {"course_total_hours": 36,
        Agent->>Agent:                      "available_hours": 10,
        Agent->>Agent:                      "deficit_hours": 26,
        Agent->>Agent:                      "adjustment_options": [...]}},
        Agent->>Agent:   trace=[...])
    end

    Note over Agent: RESPONSE → FINISHED

    Agent-->>Runner: ReActResult(success=false, error=TIME_INSUFFICIENT, trace)
    Runner-->>User: ⚠️ 学习时间不足<br/>需要: 36h / 可用: 10h / 缺口: 26h<br/>方案A: 延长至36天<br/>方案B: 增加至3.6h/天<br/>方案C: 缩减至31h(必学)
```

---

## 4. Trace 记录位置汇总

| Trace # | 状态 | 记录内容 | FSM 阶段 |
|---------|------|---------|---------|
| 1 | THINKING | `thought` = 推理文本 | THINKING 开始 |
| 2 | TOOL_EXECUTION | `selected_tool` + `tool_input` | TOOL_SELECTION → TOOL_EXECUTION |
| 3 | TOOL_EXECUTION | `tool_output` = Tool 返回结果 | TOOL_EXECUTION 返回 |
| 4 | THINKING | `thought` = 推理文本（下一轮） | THINKING 开始（循环） |
| ... | ... | ... | ... |
| N | RESPONSE | 无 tool 信息 | RESPONSE 组装完成 |

**Trace 在 3 个时机记录:**

```
1. THINKING 开始时 → 记录 thought
2. TOOL_EXECUTION 开始前 → 记录 selected_tool + tool_input
3. OBSERVATION 进入时 → 记录 tool_output

Trace 在 3 种路径结束:
1. 成功: 所有 ToolStep 完成 → RESPONSE → FINISHED
2. 4xx 阻断: blocker_check 触发 → RESPONSE(terminal) → FINISHED
3. 异常: Tool 抛异常 → ERROR → RESPONSE → FINISHED
```

**成功路径 Trace 数量:**
- 4 个 Tool × 3 条记录 + 1 条 RESPONSE = **13 条 Trace**
- 包含: 4 THINKING + 4 TOOL_EXECUTION(input) + 4 OBSERVATION(output) + 1 RESPONSE

**阻断路径 Trace 数量（以先修冲突为例）:**
- 2 个 Tool 完成 × 3 条 + 1 条 RESPONSE = **7 条 Trace**
- 包含: 2 THINKING + 2 TOOL_EXECUTION(input) + 2 OBSERVATION(output) + 1 RESPONSE
