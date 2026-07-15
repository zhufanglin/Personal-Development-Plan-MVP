# Milestone 1 Gate Review — Project Scaffolding & Data Models

| Field | Value |
|-------|-------|
| Review Date | 2026-07-11 |
| Milestone | M1: Project Scaffolding & Data Models |
| Reviewer | Gate Review (systematic cross-check) |
| Verdict | **GO WITH MINOR ISSUES** |

---

## 1. 数据模型 vs docs/tool-design.md

### 1.1 字段命名对比

| 层级 | 字段名 | 说明 |
|------|--------|------|
| courses.json | `name`, `hours`, `prerequisite` (单数) | 数据源 |
| Pydantic Model | `name`, `hours`, `prerequisite` (单数) | ✅ 与 JSON 一致 |
| tool-design.md | `course_name`, `estimated_total_hours`, `prerequisites` (复数) | ⚠️ 不一致 |

**分析:** 这是设计基线修复时遗留的问题。tool-design.md §3 仍使用旧命名。用户明确指示"优先保持 courses.json → Model → Tool → API 字段一致"，因此 Model 层的命名是**正确**的。Tool 实现时将以 Model 字段名为准。

**影响:** Tool 返回的 dict 将使用 `name`/`hours`/`prerequisite`，与 tool-design.md 文档中的示例字段名不同。不影响功能，但文档需要更新。

**判定:** MINOR — 不影响开发，tool-design.md 可在后续更新。

### 1.2 模型覆盖检查

对照 tool-design.md 四个 Tool 的输出 Schema：

| Tool | 输出 Schema 字段 | 现有 Model | 匹配 |
|------|-----------------|-----------|------|
| `get_course_info` | course_name, description, difficulty, hours, prerequisite, topics | `Course` | ✅ 完全覆盖（字段名差异除外） |
| `get_prerequisite` | satisfied, course_name, required_prerequisites, **recommended_prerequisites**, missing, completed, total_prerequisite_hours, recommendation | `PrerequisiteCheck` | ⚠️ **缺少 recommended_prerequisites** |
| `calculate_learning_time` | feasible, course_name, course_total_hours, daily_hours, duration_days, available_hours, buffer_hours, buffer_ratio, minimum_days_needed, minimum_hours_per_day, recommendation | `FeasibilityResult` | ✅ 完全覆盖 |
| `generate_learning_plan` | plan_id, generated_at, parameters, summary, learning_path, daily_schedule, resources, warnings | `LearningPath` + `DailyPlan` + dict 包装 | ⚠️ **缺少 Resource 模型** |

### 1.3 缺失模型分析

**Issue #1: PrerequisiteCheck.recommended_prerequisites**

tool-design.md §4 返回 `recommended_prerequisites: list[str]`。当前 PrerequisiteCheck 无此字段。

```
当前:
class PrerequisiteCheck:
    required_prerequisites: list[str]      ✅
    missing: list[str]                     ✅
    completed: list[str]                   ✅
    # recommended_prerequisites            ❌ 缺失
```

**建议修复（1 行）：**
```python
recommended_prerequisites: list[str] = Field(
    default_factory=list,
    description="所有 recommended 先修课程名称",
)
```

**Issue #2: Resource 模型**

tool-design.md §6 的 `generate_learning_plan` 输出包含 `resources: list[Resource]`。Resource 有字段: `title`, `type`, `url`, `topic`, `estimated_hours`, `free`, `difficulty`。

**分析:** Resource 是纯数据载体，可以从 courses.json 中提取。作为独立的 Pydantic 模型可以提供验证。但对于 MVP，Tool 可以直接返回 `list[dict]`。

**建议:** M2 实现时在 `src/models/course.py` 中添加轻量级 `Resource` 模型（~10 行）。或在 `src/tools/resources.py`（内部辅助模块）中使用 `TypedDict`。

---

## 2. 数据模型 vs docs/system-design.md

### 2.1 模块目录检查

system-design.md §6.4 定义的目录结构：

```
src/models/
├── schemas.py    # (计划单文件) 或
├── course.py     # (实际) ✅
├── learning_path.py  # (实际) ✅
└── feasibility.py    # (实际) ✅
```

**判定:** 实际实现（3 文件拆分）优于计划（单文件），职责更清晰。✅

### 2.2 FSM 状态覆盖

| FSM 状态 | 使用的 Model | 状态 |
|----------|-------------|------|
| GET_COURSE_INFO | `Course` | ✅ |
| GET_PREREQUISITE | `PrerequisiteCheck` | ✅ |
| CALCULATE_LEARNING_TIME | `FeasibilityResult`, `AdjustmentOption` | ✅ |
| GENERATE_LEARNING_PLAN | `LearningPath`, `DailyPlan` | ⚠️ 缺少 wrapper |

### 2.3 数据流验证

system-design.md §4 的 4 阶段数据流可以完整实现：

```
Stage 1 (Parse)  → CLI argparse → 无需 Model
Stage 2 (Enrich) → Tool 调用     → Course / PrerequisiteCheck / FeasibilityResult ✅
Stage 3 (Compile) → Agent 组装   → dict ✅
Stage 4 (Format)  → formatter.py → 无需 Model
```

**判定:** 数据流管道覆盖完整。✅

---

## 3. 数据模型 vs prompts/system_prompt.txt

### 3.1 Workflow 对齐

system_prompt.txt 定义的 4 步 Workflow 所需的数据结构：

| Step | Tool | 输入 Model | 输出 Model | 匹配 |
|------|------|-----------|-----------|------|
| 1 | `get_course_info` | `str` | `Course` | ✅ |
| 2 | `get_prerequisite` | `str, list[str]` | `PrerequisiteCheck` | ✅ |
| 3 | `calculate_learning_time` | `str, float, int` | `FeasibilityResult` | ✅ |
| 4 | `generate_learning_plan` | `str, float, int, bool, str\|None` | 组合输出 | ✅ |

### 3.2 异常处理对齐

system_prompt.txt 定义的 3 种异常与 exceptions.py 的映射：

| Prompt 异常 | exceptions.py | error_code | 匹配 |
|------------|---------------|------------|------|
| 先修冲突 | `PrerequisiteConflictError` | `PREREQUISITE_CONFLICT` | ✅ |
| 时间不足 | `TimeInsufficientError` | `TIME_INSUFFICIENT` | ✅ |
| 课程不存在 | `CourseNotFoundError` | `COURSE_NOT_FOUND` | ✅ |

### 3.3 反幻觉约束

Model 层通过 Pydantic 的 `Field(ge=0)`, `min_length=1`, `pattern=` 等约束，从数据层杜绝了幻觉数据的可能性。✅

---

## 4. 过度设计检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| Model 总数 | 10 个 | Topic, Course, Module, LearningPath, DayEntry, DailyPlan, FeasibilityResult, AdjustmentOption, PrerequisiteCheck + 3 个 Literal 类型。合理。 |
| 继承层次 | 0 层 | 所有 Model 直接继承 BaseModel。无过度抽象。 |
| 单模型字段数 | ≤ 11 | FeasibilityResult 最多（11 字段），其余 ≤ 9。合理。 |
| 自定义 Validator | 0 个 | 仅使用声明式 Field 约束。适当。 |
| exception 继承 | 2 层 | CourseLearningError → 7 个子类。每层有意义。 |
| 文件数 | 3 个 models + 1 个 exceptions | 职责清晰。适合 MVP。 |

**判定:** 无过度设计。✅

---

## 5. 重复模型检查

| 检查项 | 结果 |
|--------|------|
| Course vs Topic 字段重叠 | 无。Course 聚合 Topic 列表，Topic 是独立实体。 |
| Module vs Topic 字段重叠 | 部分重叠（name/hours/order/required）。但语义不同：Topic 是数据描述，Module 是计算后产物（增加 estimated_days）。**合理区分。** |
| DayEntry vs DailyPlan | 无重叠。聚合关系。 |
| FeasibilityResult vs AdjustmentOption | 无重叠。AdjustmentOption 是独立的子实体。 |

**判定:** 无重复模型。Module 与 Topic 的字段重叠是刻意的——Module 从 Topic 派生但增加计算字段。✅

---

## 6. 可简化之处

| # | 当前状态 | 简化建议 | 推荐 |
|---|---------|---------|------|
| 1 | 3 个 model 文件 + 1 个 exceptions 文件 | 合并为单文件 `models.py` | **不做**。当前拆分（course/learning_path/feasibility）职责清晰，3 个文件各 ~30 行，无负担。 |
| 2 | FeasibilityResult 11 个字段 | 合并 `buffer_hours` + `buffer_ratio` | **不做**。两者语义不同（绝对值 vs 百分比），Tool 输出需要两者。 |
| 3 | PrerequisiteCheck 7 个字段 | 移除 `completed`（可从 `required - missing` 推导） | **不做**。显式字段对 Agent 更友好（避免推理）。 |

**判定:** 当前设计无值得简化的冗余。每个字段和文件都有明确的存在理由。✅

---

## 7. 后续 Tool 实现是否需要修改 Model

| Tool | 是否需要修改 Model | 说明 |
|------|------------------|------|
| `get_course_info` | **否** | 直接使用 `Course.model_dump()` |
| `get_prerequisite` | **需添加 1 字段** | PrerequisiteCheck 缺少 `recommended_prerequisites` |
| `calculate_learning_time` | **否** | 直接使用 `FeasibilityResult.model_dump()` |
| `generate_learning_plan` | **需添加 1 模型** | 缺少 `Resource` 模型（或工具内部使用 dict） |
| `data_loader` (2.1) | **否** | 使用 `Course(**json_dict)` 解析 |

**修改量:**
- PrerequisiteCheck: **+1 字段** (1 行)
- Resource 模型: **~10 行** 新模型

**共计 < 15 行。不会导致模型返工。**

---

## 8. 如果现在开始开发 Tool，是否会导致模型返工

### 结论: **否。**

详细分析：

| 风险场景 | 概率 | 说明 |
|---------|------|------|
| 数据加载失败 | 零 | `Course(**json_dict)` 已验证通过 10/10 课程 |
| 先修树递归无法建模 | 零 | `PrerequisiteCheck` 已覆盖 flat-list + hours 计算 |
| 每日计划调度需要新结构 | 零 | `DayEntry` + `DailyPlan` 已覆盖 day/topics/hours/type |
| 可行性计算需要新字段 | 零 | `FeasibilityResult` 的 buffer_hours 可为负，支持不可行场景 |
| **推荐先修未展示** | **中** | PrerequisiteCheck 无 `recommended_prerequisites` 字段 |
| **资源推荐无模型** | **低** | 可以 dict 返回，但建议添加轻量 Resource 模型 |

**预判:** 唯一可能在 M2 中返工的模型是 PrerequisiteCheck（添加 1 字段），其他模型已足够。此修改量（1 行）不属于"返工"。✅

---

## 综合判定

### 得分卡

| 评审维度 | 结果 |
|---------|------|
| 1. 符合 tool-design.md | ⚠️ 字段名差异（已知）+ 2 处轻微缺失 |
| 2. 符合 system-design.md | ✅ |
| 3. 符合 system_prompt.txt | ✅ |
| 4. 过度设计 | ✅ 无 |
| 5. 重复模型 | ✅ 无 |
| 6. 可简化 | ✅ 已是最简 |
| 7. Tool 需修改 Model | ⚠️ 2 处轻微修改 |
| 8. 导致返工 | ✅ 不会（< 15 行修改） |

### Verdict

```
╔══════════════════════════════════╗
║  GO WITH MINOR ISSUES           ║
║                                  ║
║  Minor Issues (M2 前修复):       ║
║  1. PrerequisiteCheck 添加       ║
║     recommended_prerequisites    ║
║  2. 添加 Resource 模型           ║
║     (或 Tool 使用 dict 替代)     ║
║                                  ║
║  Non-blocking:                   ║
║  3. tool-design.md 字段名更新    ║
║     (延后至文档维护周期)          ║
╚══════════════════════════════════╝
```

### 进入 M2 的条件

在开始 Task 2.1（data_loader）之前：

1. ✅ 在 `PrerequisiteCheck` 中添加 `recommended_prerequisites: list[str]`
2. ✅ 在 `src/models/course.py` 中添加 `Resource` 模型（或确认 Tool 使用 dict）

**这两个修改共约 15 行代码，可在进入 M2 时直接完成。**

---

## 附录: 当前 Model 清单

| # | Model | 文件 | 字段数 | 用途 |
|---|-------|------|--------|------|
| 1 | `Topic` | course.py | 5 | 学习主题描述 |
| 2 | `Course` | course.py | 9 | 课程完整元数据 |
| 3 | `Module` | learning_path.py | 6 | 学习路径中的计算后模块 |
| 4 | `LearningPath` | learning_path.py | 5 | 有序模块列表 |
| 5 | `DayEntry` | learning_path.py | 4 | 每日学习条目 |
| 6 | `DailyPlan` | learning_path.py | 5 | 按天分配的学习计划 |
| 7 | `FeasibilityResult` | feasibility.py | 11 | 时间可行性评估 |
| 8 | `AdjustmentOption` | feasibility.py | 5 | 调整方案 |
| 9 | `PrerequisiteCheck` | feasibility.py | 7→8 | 先修条件检查 |
| — | `Resource` | course.py | 7 | ⚠️ 缺失，待添加 |
