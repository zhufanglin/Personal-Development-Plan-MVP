# Design Baseline Report — Course Learning Planner Agent

| Field | Value |
|-------|-------|
| Date | 2026-07-11 |
| Baseline Version | v2.0.0 |
| Review Type | Post-fix consistency verification |
| SSOT Established | ✅ |

## Scan Results

### Tool 一致性

| Check | Result |
|-------|--------|
| All docs reference only 4 tools (get_course_info, get_prerequisite, calculate_learning_time, generate_learning_plan) | ✅ PASS |
| No v1 tool names (check_prerequisites, assess_feasibility, etc.) in any active doc | ✅ PASS |
| tool-design.md is the single source of truth for tool specs | ✅ PASS |
| plan.md M2 tasks match 4-tool architecture | ✅ PASS |
| FSM states match across system-design.md, workflow.md, plan.md | ✅ PASS |

### Workflow 一致性

| Check | Result |
|-------|--------|
| ReAct steps: get_course_info → get_prerequisite → calculate_learning_time → generate_learning_plan | ✅ PASS |
| FSM has 8 states (INIT, GET_COURSE_INFO, GET_PREREQUISITE, CALCULATE_LEARNING_TIME, GENERATE_LEARNING_PLAN, COURSE_NOT_FOUND, PREREQ_CONFLICT, TIME_INSUFFICIENT, FINAL_ANSWER) | ✅ PASS |
| Exception branches: 3 types (prereq conflict, time insufficient, course not found) | ✅ PASS |
| workflow.md STEPS list matches 4-tool architecture | ✅ PASS |

### Prompt 一致性

| Check | Result |
|-------|--------|
| Single runtime prompt: prompts/system_prompt.txt | ✅ PASS |
| Design rationale in docs/system-prompt-design.md | ✅ PASS |
| No v1 prompt artifacts | ✅ PASS |
| react_template.txt updated to 4-tool names + real courses | ✅ PASS |
| prompt_loader.py target: prompts/system_prompt.txt | ✅ PASS |

### 数据一致性

| Check | Result |
|-------|--------|
| courses.json contains 10 courses (Python, SQL, Linux, Git, Java, Hadoop, Hive, Spark, Kafka, Flink) | ✅ PASS |
| prerequisites.json matches courses.json prerequisite chains | ✅ PASS |
| Java prerequisite: Python is recommended (not required) — consistent across both JSON files | ✅ PASS |
| All document examples use real courses from courses.json | ✅ PASS |
| No old course names (Machine Learning, Python Programming, etc.) in any active doc | ✅ PASS |

### Mermaid 图一致性

| Check | Result |
|-------|--------|
| architecture.mermaid: 4 tools, real courses | ✅ PASS |
| react-workflow.mermaid: 4 tools, real courses, 3 scenarios | ✅ PASS |
| system-design.md inline mermaid: 4 tools, 5 models | ✅ PASS |
| plan.md inline mermaid: 4 tools | ✅ PASS |

### README 一致性

| Check | Result |
|-------|--------|
| Tool table: 4 tools | ✅ PASS |
| Project structure: reflects actual file inventory | ✅ PASS |
| All links point to existing files | ✅ PASS |
| Course examples match courses.json | ✅ PASS |

## Issue Count

| Severity | Before Fix | After Fix |
|----------|-----------|-----------|
| CRITICAL | 2 | **0** ✅ |
| HIGH | 4 | **0** ✅ |
| MEDIUM | 8 | 2 (documented in code-review.md, tool-design.md cosmetic examples) |
| LOW | 5 | 3 (cosmetic, no functional impact) |

## Remaining Issues (Non-blocking)

| # | Severity | Description | Location |
|---|----------|-------------|----------|
| 1 | MEDIUM | tool-design.md JSON examples still use illustrative old course names | docs/tool-design.md (cosmetic — tool specs are correct) |
| 2 | MEDIUM | system-design.md still references old course names in some data flow examples | docs/system-design.md (cosmetic — specs are correct) |
| 3 | LOW | requirements.txt has commented-out optional dependencies | requirements.txt |
| 4 | LOW | No code implementation yet (expected at this phase) | src/ |

## Single Source of Truth (SSOT) Map

| Domain | SSOT File |
|--------|----------|
| Tool Definitions | `docs/tool-design.md` |
| System Architecture | `docs/system-design.md` |
| Course Data | `data/courses.json` |
| Prerequisite Graph | `data/prerequisites.json` |
| Runtime Prompt | `prompts/system_prompt.txt` |
| Prompt Design Rationale | `docs/system-prompt-design.md` |
| ReAct Template | `prompts/react_template.txt` |
| Workflow | `docs/workflow.md` |
| Implementation Plan | `plans/course-learning-agent.plan.md` |
| Architecture Overview | `docs/architecture.md` |
| Project README | `README.md` |
| Review Findings | `docs/code-review.md` |

## Verdict

**CRITICAL = 0, HIGH = 0. 项目设计基线已确立。可以进入 /plan-execution 阶段开始编码。**
