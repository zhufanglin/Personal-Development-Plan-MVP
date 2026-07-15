# Development Log — Course Learning Planner Agent

| Field | Value |
|-------|-------|
| Started | 2026-07-11 |
| Plan | `plans/course-learning-agent.plan.md` |

---

## Milestone 1: Project Scaffolding & Data Models

### Task 1.1 ✅ — Create Python package structure

**Date:** 2026-07-11
**Action:** Created 6 `__init__.py` files across `src/` subpackages and `tests/`.
**Result:** All packages importable. `python -c "import src; import src.models; ..."` succeeds.

### Task 1.2 ✅ — Define Pydantic data models

**Date:** 2026-07-11
**Action:** Created `course.py`, `learning_path.py`, `feasibility.py` with 12 Pydantic v2 models.
**Design Decision:** Zero aliases. Field names match `courses.json` exactly (`hours` not `estimated_total_hours`; `prerequisite` singular). Business exceptions extracted to `src/exceptions.py`.
**Result:** All 9 acceptance tests pass. 10 courses parsed from JSON directly.

### Task 1.3 ✅ — Course data (Pre-existing)

**Date:** 2026-07-11
**Action:** Skipped re-development. `data/courses.json` (10 courses) and `data/prerequisites.json` already exist and passed Pydantic v2 validation (10/10) during Task 1.2 verification.
**Reason:** Data files were pre-populated during the design phase and validated during model verification.

### Task 1.4 ✅ — Unit tests for data models

**Date:** 2026-07-11
**Action:** Created `tests/test_models.py` with 66 test cases across 8 test classes.
**Coverage:** 100% on `src/models/` (78/78 statements), 100% on `src/exceptions.py` (20/20), 100% overall `src/` (99/99).
**Test Categories:**
- Topic 模型: 7 tests (创建/默认值/负值/零序/缺失字段/序列化/可选标记)
- Course 模型: 8 tests (创建/默认先修/非法id/空名/非法难度/空模块/序列化/字段一致性)
- LearningPath 模型: 8 tests (Module/LearningPath/DayEntry/DailyPlan/非法类型/默认标志/负学时/零日)
- Feasibility 模型: 8 tests (可行/不可行/三种调整方案/先修满足/先修不满足/默认值/负可用时间)
- JSON 加载: 8 tests (全量/有效id/有模块/有效难度/顺序排序/学时一致性/多先修/先修有效)
- 业务异常: 10 tests (7种异常error_code/继承链/isinstance/details默认值)
- 边界测试: 6 tests (零学时/最大名称/超长名称/所有难度/零学时topic/空计划)
- 非法输入: 6 tests (hours类型/prerequisite类型/required类型/day类型/参数化约束)
- 序列化: 5 tests (model_dump_json/FeasibilityResult/PrerequisiteCheck)

---

## Milestone 2: Tool Implementation

### Task 2.1 ✅ — Data loader utility

**Date:** 2026-07-11
**Action:** Created `src/tools/data_loader.py` with `load_courses()` and `load_prerequisite_map()`.
**Design Decision:** No caching for MVP (per user instruction). Interface supports future caching/DB via adapter pattern.
**Result:** 10 courses loaded and Pydantic-validated. 10 prerequisite entries validated. FileNotFoundError and DataCorruptionError tested.
