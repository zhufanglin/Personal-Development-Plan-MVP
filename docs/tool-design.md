# Tool API Design — Course Learning Planner Agent

| Field | Value |
|-------|-------|
| Version | 2.0.0 |
| Created | 2026-07-11 |
| Protocol | Python Function Call (internal Tool API) |
| Pattern | Request/Response with structured error handling |
| Skill | api-architecture |

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Tool Overview](#2-tool-overview)
3. [Tool 1: get_course_info()](#3-tool-1-get_course_info)
4. [Tool 2: get_prerequisite()](#4-tool-2-get_prerequisite)
5. [Tool 3: calculate_learning_time()](#5-tool-3-calculate_learning_time)
6. [Tool 4: generate_learning_plan()](#6-tool-4-generate_learning_plan)
7. [Error Handling Standard](#7-error-handling-standard)
8. [Tool Dependency Graph](#8-tool-dependency-graph)

---

## 1. Design Principles

Applying api-architecture core patterns to Tool API design:

| Principle | Application |
|-----------|-------------|
| **Single Responsibility** | Each tool does exactly one thing. No tool overlaps another's domain. |
| **Explicit Contracts** | Input/Output schemas are defined before implementation. Every field has a type and description. |
| **Fail Fast** | Input validation at the boundary. Invalid inputs rejected before any processing. |
| **Structured Errors** | All errors follow a uniform `ErrorResponse` schema. No bare strings or generic exceptions. |
| **Idempotency** | Read-only tools (`get_course_info`, `get_prerequisite`) are cacheable and side-effect-free. Write tools (`calculate_learning_time`, `generate_learning_plan`) are pure functions of their inputs. |
| **Backward Compatibility** | New fields added as optional. Existing fields never removed or retyped without a version bump. |

### Universal Error Response Schema

All tools return errors in this uniform structure:

```
{
  "error": {
    "code": str,           # Machine-readable error code (e.g. "COURSE_NOT_FOUND")
    "message": str,        # Human-readable description
    "details": dict | None, # Contextual debugging info
    "tool_name": str       # Which tool produced the error
  }
}
```

| Error Code | HTTP Analog | Meaning |
|-----------|-------------|---------|
| `COURSE_NOT_FOUND` | 404 | Course not in catalog |
| `VALIDATION_ERROR` | 400 | Input failed schema validation |
| `PREREQUISITE_CONFLICT` | 409 | User lacks required prerequisites |
| `TIME_INSUFFICIENT` | 422 | Study time budget too small |
| `INTERNAL_ERROR` | 500 | Unexpected data-layer failure |

---

## 2. Tool Overview

| # | Tool | Type | Responsibility | Calls |
|---|------|------|---------------|-------|
| 1 | `get_course_info` | Read | Retrieve course metadata | Data layer |
| 2 | `get_prerequisite` | Read | Compute prerequisite tree | Data layer → `get_course_info` |
| 3 | `calculate_learning_time` | Compute | Assess time feasibility | `get_course_info` |
| 4 | `generate_learning_plan` | Orchestrate | Build full learning plan | `get_course_info` → `get_prerequisite` → `calculate_learning_time` |

### Tool Call Flow

```
User Input
    │
    ▼
┌─────────────────────┐
│ 1. get_course_info  │  ← Always first: validate course exists
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 2. get_prerequisite │  ← Check prerequisites (calls get_course_info internally)
└────────┬────────────┘
         │
    ┌────┴────┐
    │ Passed? │──NO──▶ STOP: PrerequisiteConflictError
    └────┬────┘
         │ YES
         ▼
┌──────────────────────────┐
│ 3. calculate_learning_   │  ← Assess time feasibility
│    time()                │
└────────┬─────────────────┘
         │
    ┌────┴────┐
    │Feasible?│──NO──▶ STOP: TimeInsufficientError
    └────┬────┘
         │ YES
         ▼
┌──────────────────────────┐
│ 4. generate_learning_    │  ← Build the complete plan
│    plan()                │
└────────┬─────────────────┘
         │
         ▼
    Final Output
```

---

## 3. Tool 1: get_course_info()

### 功能

查询课程目录，返回指定课程的完整元数据，包括课程描述、难度等级、预估总学时、先修课程列表、以及按顺序排列的主题模块。这是 Agent 调用的第一个 Tool，用于验证课程是否存在并获取后续所有计算所需的基础数据。

**业务规则:**
- 课程名称匹配为**大小写不敏感模糊匹配**（如 "python" 可匹配 "Python Programming"）
- 返回的 topics 按 `order` 字段升序排列
- `estimated_total_hours` 为完成所有必学模块的最短时间估算（不含复习和缓冲）

### 输入

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `course_name` | `str` | ✅ | 长度 1-100，非空 | 课程名称。支持模糊匹配。 |

**输入示例:**
```json
{
    "course_name": "Machine Learning"
}
```

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `course_name` | `str` | 课程的正式名称（规范化后） |
| `description` | `str` | 课程概述（1-3 句话） |
| `difficulty` | `Literal["beginner", "intermediate", "advanced"]` | 难度等级 |
| `estimated_total_hours` | `float` | 完成所有必学模块的最少学时 |
| `prerequisites` | `list[str]` | 必须先修完的课程名称列表 |
| `topics` | `list[Topic]` | 按 `order` 升序排列的主题模块列表 |

**Topic 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 主题名称 |
| `hours` | `float` | 该主题的预估学时 |
| `order` | `int` | 学习顺序（1-based） |
| `required` | `bool` | 是否为必修模块（False 表示可选，时间不足时可跳过） |
| `description` | `str` | 该主题的简要说明 |

### 异常处理

| 条件 | 错误码 | 错误信息示例 |
|------|--------|-------------|
| 课程不存在 | `COURSE_NOT_FOUND` | `"Course '量子计算' not found. Available: Python Programming, Machine Learning, ..."` |
| 课程名为空 | `VALIDATION_ERROR` | `"course_name must be a non-empty string"` |
| 数据文件损坏 | `INTERNAL_ERROR` | `"Failed to load course catalog: JSON parse error at line 15"` |

**异常时的 Agent 行为:**
- `COURSE_NOT_FOUND` → Agent 列出可用课程，请用户重新输入。**不继续执行后续 Tool。**
- `VALIDATION_ERROR` → Agent 提示正确的输入格式。
- `INTERNAL_ERROR` → Agent 报告系统错误并终止。

### Python 函数签名

```
get_course_info(course_name: str) -> dict
```

**输入类型展开:**
```
get_course_info(
    course_name: str         # 课程名称，大小写不敏感
)
```

**返回类型:**
```
-> dict    # 成功时返回 CourseInfoResponse
           # 失败时返回 ErrorResponse
```

### 返回示例

**成功 (200 OK):**
```json
{
    "course_name": "Machine Learning",
    "description": "Introduction to machine learning: supervised/unsupervised learning, model evaluation, and practical projects using scikit-learn.",
    "difficulty": "intermediate",
    "estimated_total_hours": 50.0,
    "prerequisites": [
        "Python Programming",
        "Mathematics for ML"
    ],
    "topics": [
        {
            "name": "Introduction to ML Concepts",
            "hours": 4.0,
            "order": 1,
            "required": true,
            "description": "ML taxonomy, overfitting, bias-variance tradeoff"
        },
        {
            "name": "Data Preprocessing",
            "hours": 5.0,
            "order": 2,
            "required": true,
            "description": "Cleaning, normalization, feature encoding, train-test split"
        },
        {
            "name": "Supervised Learning — Regression",
            "hours": 6.0,
            "order": 3,
            "required": true,
            "description": "Linear regression, polynomial, regularization (Ridge/Lasso)"
        },
        {
            "name": "Supervised Learning — Classification",
            "hours": 6.0,
            "order": 4,
            "required": true,
            "description": "Logistic regression, SVM, k-NN, decision trees"
        },
        {
            "name": "Unsupervised Learning — Clustering",
            "hours": 5.0,
            "order": 5,
            "required": true,
            "description": "K-means, DBSCAN, hierarchical clustering, PCA"
        },
        {
            "name": "Model Evaluation and Validation",
            "hours": 5.0,
            "order": 6,
            "required": true,
            "description": "Cross-validation, confusion matrix, ROC/AUC, F1-score"
        },
        {
            "name": "Feature Engineering",
            "hours": 4.0,
            "order": 7,
            "required": false,
            "description": "Feature selection, extraction, interaction features (optional)"
        },
        {
            "name": "ML Project: End-to-End Pipeline",
            "hours": 8.0,
            "order": 8,
            "required": true,
            "description": "Capstone project integrating all learned techniques"
        },
        {
            "name": "Introduction to Deep Learning",
            "hours": 7.0,
            "order": 9,
            "required": false,
            "description": "Neural network basics, TensorFlow/Keras intro (optional)"
        }
    ]
}
```

**失败 (404 Not Found):**
```json
{
    "error": {
        "code": "COURSE_NOT_FOUND",
        "message": "Course '量子计算' not found in catalog.",
        "details": {
            "query": "量子计算",
            "available_courses": [
                "Python Programming",
                "Machine Learning",
                "Mathematics for ML",
                "Data Structures and Algorithms",
                "Web Development with React",
                "JavaScript Fundamentals"
            ]
        },
        "tool_name": "get_course_info"
    }
}
```

**失败 (400 Validation Error):**
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input: course_name must be a non-empty string.",
        "details": {
            "field": "course_name",
            "received": "",
            "constraint": "length >= 1"
        },
        "tool_name": "get_course_info"
    }
}
```

---

## 4. Tool 2: get_prerequisite()

### 功能

查询指定课程的完整先修课程树（Prerequisite Tree），包括直接先修和间接先修（递归展开），并标注每个先修课程的学时和难度。Agent 使用此 Tool 判断用户是否满足学习该课程的前置条件。

**业务规则:**
- 先修关系从 `data/prerequisites.json` 加载，包含 `required` 和 `recommended` 两个类别
- **`required`** 先修为硬性要求：不满足则 Agent 必须终止并提示用户先修
- **`recommended`** 先修为软性建议：不满足则 Agent 提醒但不阻止
- 递归展开：如果先修课程本身也有先修课，继续展开到无先修课为止（最大递归深度 5 层，防止循环依赖）
- 返回 `total_prerequisite_hours`：完成全部 required 先修课所需的最少学时

### 输入

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `course_name` | `str` | ✅ | 长度 1-100，非空 | 目标课程名称 |
| `user_knowledge` | `list[str]` | ✅ | 每个元素长度 1-100 | 用户已完成的课程名称列表。可为空列表 `[]`。 |

**输入示例:**
```json
{
    "course_name": "Machine Learning",
    "user_knowledge": ["Python Programming"]
}
```

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `course_name` | `str` | 目标课程名称 |
| `satisfied` | `bool` | 是否满足全部 required 先修条件 |
| `prerequisite_tree` | `list[PrerequisiteNode]` | 先修课程树（递归展开） |
| `required_prerequisites` | `list[str]` | 所有 required 先修课程名称（扁平列表） |
| `recommended_prerequisites` | `list[str]` | 所有 recommended 先修课程名称 |
| `missing` | `list[str]` | `required` 中用户尚未完成的课程 |
| `completed` | `list[str]` | `required` 中用户已完成的课程 |
| `total_prerequisite_hours` | `float` | 完成所有 missing 先修课所需的最少学时 |
| `recommendation` | `str` | 人类可读的建议文本 |

**PrerequisiteNode 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `course_name` | `str` | 先修课程名称 |
| `type` | `Literal["required", "recommended"]` | 先修类型 |
| `estimated_hours` | `float` | 该先修课的学时 |
| `difficulty` | `str` | 难度等级 |
| `children` | `list[PrerequisiteNode]` | 该课程自身的先修课（递归） |
| `is_completed` | `bool` | 用户是否已完成此课程 |

### 异常处理

| 条件 | 错误码 | 错误信息示例 |
|------|--------|-------------|
| 课程不存在 | `COURSE_NOT_FOUND` | `"Course '深度强化学习' not found in catalog."` |
| 循环依赖检测 | `INTERNAL_ERROR` | `"Circular prerequisite detected: A → B → A"` |
| 递归深度超限 | `INTERNAL_ERROR` | `"Prerequisite tree exceeds max depth of 5 for course 'X'"` |
| user_knowledge 格式错误 | `VALIDATION_ERROR` | `"user_knowledge must be a list of strings"` |

**异常时的 Agent 行为:**
- `satisfied = false` → **这不是异常**，而是正常的业务结果。Agent 检查 `missing` 列表，向用户展示缺失的先修课及预估时间，**不继续调用 `calculate_learning_time` 和 `generate_learning_plan`**。

### Python 函数签名

```
get_prerequisite(course_name: str, user_knowledge: list[str]) -> dict
```

**输入类型展开:**
```
get_prerequisite(
    course_name: str,          # 目标课程名称
    user_knowledge: list[str]  # 用户已完成的课程列表，如 ["Python Programming", "Calculus"]
)
```

**返回类型:**
```
-> dict    # 成功时返回 PrerequisiteResponse
           # 失败时返回 ErrorResponse
```

### 返回示例

**成功 — 先修条件已满足:**
```json
{
    "course_name": "Machine Learning",
    "satisfied": true,
    "prerequisite_tree": [
        {
            "course_name": "Python Programming",
            "type": "required",
            "estimated_hours": 20.0,
            "difficulty": "beginner",
            "children": [],
            "is_completed": true
        },
        {
            "course_name": "Mathematics for ML",
            "type": "required",
            "estimated_hours": 30.0,
            "difficulty": "intermediate",
            "children": [],
            "is_completed": true
        }
    ],
    "required_prerequisites": [
        "Python Programming",
        "Mathematics for ML"
    ],
    "recommended_prerequisites": [],
    "missing": [],
    "completed": [
        "Python Programming",
        "Mathematics for ML"
    ],
    "total_prerequisite_hours": 0.0,
    "recommendation": "All prerequisites are satisfied. You are ready to start this course."
}
```

**成功 — 先修条件不满足（业务终止）:**
```json
{
    "course_name": "Machine Learning",
    "satisfied": false,
    "prerequisite_tree": [
        {
            "course_name": "Python Programming",
            "type": "required",
            "estimated_hours": 20.0,
            "difficulty": "beginner",
            "children": [],
            "is_completed": false
        },
        {
            "course_name": "Mathematics for ML",
            "type": "required",
            "estimated_hours": 30.0,
            "difficulty": "intermediate",
            "children": [],
            "is_completed": false
        }
    ],
    "required_prerequisites": [
        "Python Programming",
        "Mathematics for ML"
    ],
    "recommended_prerequisites": [],
    "missing": [
        "Python Programming",
        "Mathematics for ML"
    ],
    "completed": [],
    "total_prerequisite_hours": 50.0,
    "recommendation": "You are missing 2 prerequisites (total 50.0 hours). Complete 'Python Programming' (20.0h) and 'Mathematics for ML' (30.0h) before starting 'Machine Learning'. Estimated prerequisite study time: 25 days at 2h/day."
}
```

**成功 — 递归先修树 (Deep Learning 的先修链):**
```json
{
    "course_name": "Deep Learning",
    "satisfied": false,
    "prerequisite_tree": [
        {
            "course_name": "Machine Learning",
            "type": "required",
            "estimated_hours": 50.0,
            "difficulty": "intermediate",
            "children": [
                {
                    "course_name": "Python Programming",
                    "type": "required",
                    "estimated_hours": 20.0,
                    "difficulty": "beginner",
                    "children": [],
                    "is_completed": false
                },
                {
                    "course_name": "Mathematics for ML",
                    "type": "required",
                    "estimated_hours": 30.0,
                    "difficulty": "intermediate",
                    "children": [],
                    "is_completed": false
                }
            ],
            "is_completed": false
        }
    ],
    "required_prerequisites": [
        "Machine Learning",
        "Python Programming",
        "Mathematics for ML"
    ],
    "recommended_prerequisites": [
        "Data Structures and Algorithms"
    ],
    "missing": [
        "Machine Learning",
        "Python Programming",
        "Mathematics for ML"
    ],
    "completed": [],
    "total_prerequisite_hours": 100.0,
    "recommendation": "You are missing 3 prerequisites (total 100.0 hours). Suggested order: 1) Python Programming (20.0h), 2) Mathematics for ML (30.0h), 3) Machine Learning (50.0h). Estimated total prerequisite study time: 50 days at 2h/day."
}
```

---

## 5. Tool 3: calculate_learning_time()

### 功能

根据课程总学时和用户每日可用学习时间，计算该学习目标是否可行。输出可行性判断、时间缓冲量、以及不可行时的调整建议。此 Tool 是纯计算函数，不产生学习计划本身。

**业务规则:**
- `available_hours = daily_hours × duration_days`
- `buffer_hours = available_hours - course_total_hours`（负数表示不足）
- 如果 `buffer_hours >= 0`，学习目标可行
- 如果 `buffer_hours < 0`，输出三种调整方案（见 `adjustment_options`）
- 建议 buffer 至少保留 20% 余量用于复习和消化（`recommended_buffer_ratio = 0.2`）

### 输入

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `course_name` | `str` | ✅ | 长度 1-100 | 目标课程名称 |
| `daily_hours` | `float` | ✅ | 0.5 ≤ daily_hours ≤ 16 | 每天可用于学习的小时数 |
| `duration_days` | `int` | ✅ | 1 ≤ duration_days ≤ 365 | 计划学习的天数 |

**输入示例:**
```json
{
    "course_name": "Machine Learning",
    "daily_hours": 2.0,
    "duration_days": 20
}
```

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `feasible` | `bool` | 学习目标是否可行 |
| `course_name` | `str` | 课程名称 |
| `course_total_hours` | `float` | 课程的必学模块总学时 |
| `daily_hours` | `float` | 每日学习小时数（回显） |
| `duration_days` | `int` | 学习天数（回显） |
| `available_hours` | `float` | 总可用时间 = `daily_hours × duration_days` |
| `buffer_hours` | `float` | 时间缓冲 = `available_hours - course_total_hours` |
| `buffer_ratio` | `float` | 缓冲比例 = `buffer_hours / course_total_hours` |
| `recommended_buffer` | `float` | 建议缓冲量 = `course_total_hours × 0.2` |
| `buffer_sufficient` | `bool` | 缓冲是否达到建议的 20% |
| `minimum_days_needed` | `float` | 最少需要的天数 = `ceil(course_total_hours / daily_hours)` |
| `minimum_hours_per_day` | `float` | 最少需要的每日小时数 = `ceil(course_total_hours / duration_days * 10) / 10` |
| `adjustment_options` | `list[AdjustmentOption]` | 不可行时的调整方案（可行时为空列表） |
| `recommendation` | `str` | 人类可读的评估文本 |

**AdjustmentOption 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `strategy` | `Literal["extend_duration", "increase_hours", "reduce_scope"]` | 调整策略 |
| `label` | `str` | 方案标题（中文） |
| `description` | `str` | 方案详细说明 |
| `new_daily_hours` | `float \| None` | 调整后的每日小时数 |
| `new_duration_days` | `int \| None` | 调整后的学习天数 |
| `reduced_hours` | `float \| None` | 缩减范围后的学时（仅 reduce_scope） |

### 异常处理

| 条件 | 错误码 | 错误信息示例 |
|------|--------|-------------|
| 课程不存在 | `COURSE_NOT_FOUND` | `"Course 'X' not found in catalog."` |
| daily_hours 超出范围 | `VALIDATION_ERROR` | `"daily_hours must be between 0.5 and 16, got 20.0"` |
| duration_days 超出范围 | `VALIDATION_ERROR` | `"duration_days must be between 1 and 365, got 0"` |
| 课程无 topics 数据 | `INTERNAL_ERROR` | `"Course 'X' has no topics defined"` |

**异常时的 Agent 行为:**
- `feasible = false` → **这不是异常**。Agent 展示 `adjustment_options` 中的三种方案，请用户选择或重新输入参数。**不继续调用 `generate_learning_plan`。**

### Python 函数签名

```
calculate_learning_time(course_name: str, daily_hours: float, duration_days: int) -> dict
```

**输入类型展开:**
```
calculate_learning_time(
    course_name: str,      # 课程名称
    daily_hours: float,    # 每日学习小时数 (0.5 ~ 16)
    duration_days: int     # 计划学习天数 (1 ~ 365)
)
```

**返回类型:**
```
-> dict    # 成功时返回 FeasibilityResponse
           # 失败时返回 ErrorResponse
```

### 返回示例

**成功 — 时间充足 (有足够缓冲):**
```json
{
    "feasible": true,
    "course_name": "Machine Learning",
    "course_total_hours": 50.0,
    "daily_hours": 4.0,
    "duration_days": 20,
    "available_hours": 80.0,
    "buffer_hours": 30.0,
    "buffer_ratio": 0.6,
    "recommended_buffer": 10.0,
    "buffer_sufficient": true,
    "minimum_days_needed": 13,
    "minimum_hours_per_day": 2.5,
    "adjustment_options": [],
    "recommendation": "Feasible with comfortable buffer. You have 80.0 hours available vs 50.0 hours needed. The 30.0h buffer (60%) allows ample time for review and practice."
}
```

**成功 — 时间刚好/紧张 (可行但缓冲不足):**
```json
{
    "feasible": true,
    "course_name": "Python Programming",
    "course_total_hours": 20.0,
    "daily_hours": 2.0,
    "duration_days": 10,
    "available_hours": 20.0,
    "buffer_hours": 0.0,
    "buffer_ratio": 0.0,
    "recommended_buffer": 4.0,
    "buffer_sufficient": false,
    "minimum_days_needed": 10,
    "minimum_hours_per_day": 2.0,
    "adjustment_options": [],
    "recommendation": "Feasible but tight. You have exactly 20.0 hours with no buffer. Consider adding 2 more days for review to reach the recommended 20% buffer (4.0h)."
}
```

**成功 — 时间不足 (不可行，返回三种调整方案):**
```json
{
    "feasible": false,
    "course_name": "Machine Learning",
    "course_total_hours": 50.0,
    "daily_hours": 1.0,
    "duration_days": 20,
    "available_hours": 20.0,
    "buffer_hours": -30.0,
    "buffer_ratio": -0.6,
    "recommended_buffer": 10.0,
    "buffer_sufficient": false,
    "minimum_days_needed": 50,
    "minimum_hours_per_day": 2.5,
    "adjustment_options": [
        {
            "strategy": "extend_duration",
            "label": "方案 A: 延长学习周期",
            "description": "保持每天学习 1.0 小时，将学习周期从 20 天延长至 50 天。",
            "new_daily_hours": null,
            "new_duration_days": 50,
            "reduced_hours": null
        },
        {
            "strategy": "increase_hours",
            "label": "方案 B: 增加每日学习时间",
            "description": "保持 20 天的学习周期，将每日学习时间从 1.0 小时增加到 2.5 小时。",
            "new_daily_hours": 2.5,
            "new_duration_days": null,
            "reduced_hours": null
        },
        {
            "strategy": "reduce_scope",
            "label": "方案 C: 缩减学习范围",
            "description": "跳过 2 个可选模块（Feature Engineering 4.0h + Deep Learning Intro 7.0h），必学模块降至 39.0 小时。",
            "new_daily_hours": null,
            "new_duration_days": null,
            "reduced_hours": 39.0
        }
    ],
    "recommendation": "Not feasible. You need 50.0 hours but only have 20.0 hours available. Deficit: 30.0 hours. Review the 3 adjustment options above and retry with new parameters."
}
```

**失败 (400 Validation Error):**
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input: daily_hours must be between 0.5 and 16.",
        "details": {
            "field": "daily_hours",
            "received": 20.0,
            "constraint": "0.5 <= daily_hours <= 16"
        },
        "tool_name": "calculate_learning_time"
    }
}
```

---

## 6. Tool 4: generate_learning_plan()

### 功能

生成完整的个性化学习计划，包括按依赖关系排序的学习路径、每日学习时间表、以及推荐的学习资源。这是 Agent 流程的最终输出 Tool——仅在通过先修检查和可行性评估后调用。

**业务规则:**
- 模块按 `order` 字段排序（拓扑排序保证先修依赖）
- 每日分配：贪心算法将模块分配到每天，每天最多 `daily_hours` 小时
- 每 5 个学习日插入 1 个复习日（review day）
- 最后一个模块完成后插入 1 个综合评估日（assessment day）
- 可选模块（`required=false`）在时间不足时自动跳过
- 如果 `skip_optional=true`，所有可选模块被排除
- `start_date` 为 `null` 时，计划以 "Day 1" 标注，不关联真实日期

### 输入

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| `course_name` | `str` | ✅ | 长度 1-100 | 目标课程名称 |
| `daily_hours` | `float` | ✅ | 0.5 ≤ daily_hours ≤ 16 | 每日学习小时数 |
| `duration_days` | `int` | ✅ | 1 ≤ duration_days ≤ 365 | 计划天数 |
| `skip_optional` | `bool` | ❌ | 默认 `false` | 是否跳过所有可选模块 |
| `start_date` | `str \| None` | ❌ | 格式 `YYYY-MM-DD`，默认 `null` | 计划开始日期 |

**输入示例:**
```json
{
    "course_name": "Python Programming",
    "daily_hours": 2.0,
    "duration_days": 15,
    "skip_optional": false,
    "start_date": null
}
```

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `plan_id` | `str` | 计划唯一标识（UUID v4） |
| `course_name` | `str` | 课程名称 |
| `generated_at` | `str` | 生成时间戳（ISO 8601） |
| `parameters` | `PlanParameters` | 回显输入参数 |
| `summary` | `PlanSummary` | 计划摘要统计 |
| `learning_path` | `list[LearningModule]` | 按顺序排列的学习模块 |
| `daily_schedule` | `list[DaySchedule]` | 每日学习安排 |
| `resources` | `list[Resource]` | 推荐学习资源 |
| `warnings` | `list[str]` | 警告信息（如缓冲不足） |

**PlanParameters 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `daily_hours` | `float` | 每日学习小时数 |
| `duration_days` | `int` | 计划天数 |
| `skip_optional` | `bool` | 是否跳过可选模块 |
| `start_date` | `str \| None` | 开始日期 |

**PlanSummary 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_modules` | `int` | 模块总数 |
| `required_modules` | `int` | 必修模块数 |
| `optional_modules` | `int` | 可选模块数（含自动跳过的） |
| `skipped_modules` | `int` | 被跳过的可选模块数 |
| `total_learning_hours` | `float` | 学习总学时 |
| `study_days` | `int` | 纯学习天数 |
| `review_days` | `int` | 复习天数 |
| `assessment_days` | `int` | 评估天数 |
| `total_days` | `int` | 计划总天数 |
| `completion_percentage` | `float` | 课程完成度（0.0 - 1.0） |

**LearningModule 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `module_id` | `str` | 模块唯一标识 |
| `name` | `str` | 模块名称 |
| `order` | `int` | 学习顺序 |
| `hours` | `float` | 该模块所需学时 |
| `required` | `bool` | 是否为必修 |
| `included` | `bool` | 是否包含在当前计划中（跳过的可选模块为 false） |
| `topics` | `list[str]` | 该模块涵盖的子主题 |

**DaySchedule 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `day` | `int` | 第几天（1-based） |
| `date` | `str \| None` | 真实日期（ISO 格式），无 start_date 时为 null |
| `type` | `Literal["study", "review", "assessment"]` | 日程类型 |
| `modules` | `list[DayModule]` | 当天学习的模块及分配时间 |
| `total_hours` | `float` | 当天总学时 |
| `notes` | `str` | 当天备注 |

**DayModule 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `module_name` | `str` | 模块名称 |
| `hours_allocated` | `float` | 当天分配到该模块的小时数 |
| `is_continuation` | `bool` | 是否为上一日模块的延续（模块跨天时为 true） |
| `progress` | `float` | 该模块的当天完成进度（0.0 - 1.0） |

**Resource 子结构:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | `str` | 资源标题 |
| `type` | `Literal["video", "book", "article", "course", "tutorial", "documentation"]` | 资源类型 |
| `url` | `str \| None` | 资源链接 |
| `topic` | `str` | 关联的主题名称 |
| `estimated_hours` | `float \| None` | 预计耗时 |
| `free` | `bool` | 是否免费 |
| `difficulty` | `str` | 难度等级 |

### 异常处理

| 条件 | 错误码 | 错误信息示例 |
|------|--------|-------------|
| 课程不存在 | `COURSE_NOT_FOUND` | `"Course 'X' not found."` |
| 输入参数无效 | `VALIDATION_ERROR` | `"daily_hours must be between 0.5 and 16"` |
| 先修条件不满足 | `PREREQUISITE_CONFLICT` | `"Cannot generate plan: prerequisites not met. Missing: Python Programming."` |
| 时间不足 | `TIME_INSUFFICIENT` | `"Cannot generate plan: 50.0h needed but only 20.0h available."` |
| 数据异常 | `INTERNAL_ERROR` | `"Course data inconsistent: topic hours sum exceeds course total"` |

**异常时的 Agent 行为:**
- `PREREQUISITE_CONFLICT` → Agent 应**先调用 `get_prerequisite`** 获取缺失的先修课详情，然后向用户展示先修计划
- `TIME_INSUFFICIENT` → Agent 应**先调用 `calculate_learning_time`** 获取三种调整方案，然后展示给用户
- `VALIDATION_ERROR` → 提示正确输入格式

### Python 函数签名

```
generate_learning_plan(
    course_name: str,
    daily_hours: float,
    duration_days: int,
    skip_optional: bool = False,
    start_date: str | None = None
) -> dict
```

**输入类型展开:**
```
generate_learning_plan(
    course_name: str,           # 课程名称
    daily_hours: float,         # 每日学习小时数 (0.5 ~ 16)
    duration_days: int,         # 计划学习天数 (1 ~ 365)
    skip_optional: bool = False, # 是否跳过可选模块
    start_date: str | None = None # 开始日期 "YYYY-MM-DD" 或 None
)
```

**返回类型:**
```
-> dict    # 成功时返回 LearningPlanResponse
           # 失败时返回 ErrorResponse
```

### 返回示例

**成功 (完整学习计划):**
```json
{
    "plan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "course_name": "Python Programming",
    "generated_at": "2026-07-11T15:30:00Z",
    "parameters": {
        "daily_hours": 2.0,
        "duration_days": 15,
        "skip_optional": false,
        "start_date": null
    },
    "summary": {
        "total_modules": 5,
        "required_modules": 5,
        "optional_modules": 0,
        "skipped_modules": 0,
        "total_learning_hours": 20.0,
        "study_days": 10,
        "review_days": 2,
        "assessment_days": 1,
        "total_days": 13,
        "completion_percentage": 1.0
    },
    "learning_path": [
        {
            "module_id": "mod_01",
            "name": "Variables and Data Types",
            "order": 1,
            "hours": 3.0,
            "required": true,
            "included": true,
            "topics": ["integers", "floats", "strings", "booleans", "type conversion"]
        },
        {
            "module_id": "mod_02",
            "name": "Control Flow",
            "order": 2,
            "hours": 4.0,
            "required": true,
            "included": true,
            "topics": ["if/elif/else", "for loops", "while loops", "break/continue"]
        },
        {
            "module_id": "mod_03",
            "name": "Functions and Scope",
            "order": 3,
            "hours": 4.0,
            "required": true,
            "included": true,
            "topics": ["defining functions", "arguments/parameters", "return values", "scope rules", "lambda"]
        },
        {
            "module_id": "mod_04",
            "name": "Object-Oriented Programming",
            "order": 4,
            "hours": 5.0,
            "required": true,
            "included": true,
            "topics": ["classes", "objects", "inheritance", "encapsulation", "polymorphism"]
        },
        {
            "module_id": "mod_05",
            "name": "Working with Libraries",
            "order": 5,
            "hours": 4.0,
            "required": true,
            "included": true,
            "topics": ["import", "stdlib overview", "os/path", "datetime", "json"]
        }
    ],
    "daily_schedule": [
        {
            "day": 1,
            "date": null,
            "type": "study",
            "modules": [
                {
                    "module_name": "Variables and Data Types",
                    "hours_allocated": 2.0,
                    "is_continuation": false,
                    "progress": 0.67
                }
            ],
            "total_hours": 2.0,
            "notes": "Focus on hands-on practice with each data type."
        },
        {
            "day": 2,
            "date": null,
            "type": "study",
            "modules": [
                {
                    "module_name": "Variables and Data Types",
                    "hours_allocated": 1.0,
                    "is_continuation": true,
                    "progress": 1.0
                },
                {
                    "module_name": "Control Flow",
                    "hours_allocated": 1.0,
                    "is_continuation": false,
                    "progress": 0.25
                }
            ],
            "total_hours": 2.0,
            "notes": "Complete data types module before moving to control flow."
        },
        {
            "day": 3,
            "date": null,
            "type": "study",
            "modules": [
                {
                    "module_name": "Control Flow",
                    "hours_allocated": 2.0,
                    "is_continuation": true,
                    "progress": 0.75
                }
            ],
            "total_hours": 2.0,
            "notes": ""
        },
        {
            "day": 4,
            "date": null,
            "type": "study",
            "modules": [
                {
                    "module_name": "Control Flow",
                    "hours_allocated": 1.0,
                    "is_continuation": true,
                    "progress": 1.0
                },
                {
                    "module_name": "Functions and Scope",
                    "hours_allocated": 1.0,
                    "is_continuation": false,
                    "progress": 0.25
                }
            ],
            "total_hours": 2.0,
            "notes": ""
        },
        {
            "day": 5,
            "date": null,
            "type": "review",
            "modules": [],
            "total_hours": 2.0,
            "notes": "Review Day: Revisit Variables, Control Flow, and Functions. Practice exercises on all 3 topics covered so far."
        }
    ],
    "resources": [
        {
            "title": "Python Official Tutorial",
            "type": "documentation",
            "url": "https://docs.python.org/3/tutorial/",
            "topic": "Variables and Data Types",
            "estimated_hours": null,
            "free": true,
            "difficulty": "beginner"
        },
        {
            "title": "Automate the Boring Stuff with Python",
            "type": "book",
            "url": "https://automatetheboringstuff.com/",
            "topic": "Control Flow",
            "estimated_hours": 15.0,
            "free": true,
            "difficulty": "beginner"
        },
        {
            "title": "Real Python — OOP Tutorial",
            "type": "tutorial",
            "url": "https://realpython.com/python3-object-oriented-programming/",
            "topic": "Object-Oriented Programming",
            "estimated_hours": 2.0,
            "free": true,
            "difficulty": "intermediate"
        }
    ],
    "warnings": [
        "Buffer is below 20% recommended. Consider adding 2 more days for extra review time."
    ]
}
```

**失败 (409 Prerequisite Conflict):**
```json
{
    "error": {
        "code": "PREREQUISITE_CONFLICT",
        "message": "Cannot generate plan for 'Machine Learning': prerequisites not satisfied.",
        "details": {
            "course_name": "Machine Learning",
            "missing_prerequisites": ["Python Programming", "Mathematics for ML"],
            "suggestion": "Call get_prerequisite() to see the full prerequisite tree and estimated completion times."
        },
        "tool_name": "generate_learning_plan"
    }
}
```

**失败 (422 Time Insufficient):**
```json
{
    "error": {
        "code": "TIME_INSUFFICIENT",
        "message": "Cannot generate plan: 50.0 hours needed but only 20.0 hours available (deficit: 30.0h).",
        "details": {
            "course_total_hours": 50.0,
            "available_hours": 20.0,
            "deficit_hours": 30.0,
            "suggestion": "Call calculate_learning_time() to see 3 adjustment options."
        },
        "tool_name": "generate_learning_plan"
    }
}
```

---

## 7. Error Handling Standard

### 7.1 Error Response Contract

所有 Tool 在任何失败情况下返回统一结构：

```
{
    "error": {
        "code": str,          # 见下方错误码表
        "message": str,       # 面向用户的描述
        "details": dict|null, # 面向开发者的调试信息
        "tool_name": str      # 产生错误的 Tool 名称
    }
}
```

### 7.2 Error Code Registry

| 错误码 | HTTP 类比 | 触发条件 | 是否可恢复 |
|--------|----------|---------|-----------|
| `COURSE_NOT_FOUND` | 404 | 课程不在目录中 | ✅ 用户可重新输入 |
| `VALIDATION_ERROR` | 400 | 输入参数不符合约束 | ✅ 用户可修正输入 |
| `PREREQUISITE_CONFLICT` | 409 | 用户缺少先修课程 | ✅ 用户可先修后再来 |
| `TIME_INSUFFICIENT` | 422 | 学习时间不足 | ✅ 用户可调整参数 |
| `CIRCULAR_DEPENDENCY` | 500 | 先修课程存在循环依赖 | ❌ 需修复数据 |
| `MAX_RECURSION_DEPTH` | 500 | 先修树深度超限 | ❌ 需修复数据 |
| `DATA_CORRUPTION` | 500 | JSON 文件损坏或格式错误 | ❌ 需修复数据 |
| `INTERNAL_ERROR` | 500 | 未预期的内部错误 | ❌ 需排查 |

### 7.3 Agent Exception Handling Flow

```
Tool returns dict
    │
    ▼
┌──────────────────┐
│ Has "error" key? │────YES──▶ Extract error.code
└────────┬─────────┘
         │ NO                          ┌──────────────────────────────┐
         ▼                             ▼                              │
    ┌──────────┐              ┌──────────────────┐                    │
    │ Process  │              │ Recoverable?     │                    │
    │ normally │              │ (4xx codes)      │                    │
    └──────────┘              └────┬─────────┬───┘                    │
                             YES   │         │  NO (5xx)              │
                                   ▼         ▼                        │
                          ┌──────────────┐ ┌──────────────────┐       │
                          │Agent formats │ │Agent reports     │       │
                          │user-friendly │ │system error and  │       │
                          │error message │ │terminates session│       │
                          │with next     │ └──────────────────┘       │
                          │steps         │                            │
                          └──────────────┘                            │
                                                                      │
              Recoverable handling per code:                          │
              ┌──────────────────┬──────────────────────────────┐    │
              │ COURSE_NOT_FOUND │ List available courses,       │    │
              │                  │ ask user to retry             │    │
              ├──────────────────┼──────────────────────────────┤    │
              │ VALIDATION_ERROR │ Show constraint,              │    │
              │                  │ show valid input example      │    │
              ├──────────────────┼──────────────────────────────┤    │
              │PREREQUISITE_     │ Call get_prerequisite(),      │    │
              │CONFLICT          │ show missing prereqs + hours  │    │
              ├──────────────────┼──────────────────────────────┤    │
              │TIME_INSUFFICIENT │ Call calculate_learning_time()│    │
              │                  │ show 3 adjustment options     │    │
              └──────────────────┴──────────────────────────────┘    │
```

---

## 8. Tool Dependency Graph

```
                    ┌──────────────────┐
                    │   Data Layer     │
                    │ data/courses.json│
                    │ data/prereqs.json│
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              │
    ┌─────────────────┐  ┌─────────────────┐
    │ get_course_info │  │ get_prerequisite│
    │                 │◀─│ (reads prereqs) │
    │ (reads courses) │  │                 │
    └────────┬────────┘  └────────┬────────┘
             │                    │
             │         ┌──────────┘
             │         │
             ▼         ▼
    ┌─────────────────────────┐
    │ calculate_learning_time │
    │ (pure compute, reads    │
    │  course via get_        │
    │  course_info internally)│
    └────────────┬────────────┘
                 │
                 │  (only if feasible=true AND prereqs satisfied)
                 │
                 ▼
    ┌─────────────────────────┐
    │ generate_learning_plan  │
    │ (orchestrates all 3     │
    │  tools internally,      │
    │  builds full plan)      │
    └─────────────────────────┘

    Internal call chain of generate_learning_plan():
    ┌────────────────────────────────────────────────────┐
    │ 1. get_course_info(course_name) → course data     │
    │ 2. get_prerequisite(course_name, []) → prereq check│
    │ 3. calculate_learning_time(...) → feasibility      │
    │ 4. IF all passed → build path + schedule + resources│
    │ 5. IF any failed → return structured error         │
    └────────────────────────────────────────────────────┘
```

---

## Appendix: Schema Registry

All output schemas defined above are registered in `src/models/schemas.py` as Pydantic v2 models:

| Schema | Model Class | Used By |
|--------|------------|---------|
| CourseInfoResponse | `CourseInfoResponse` | `get_course_info` |
| PrerequisiteResponse | `PrerequisiteResponse` | `get_prerequisite` |
| FeasibilityResponse | `FeasibilityResponse` | `calculate_learning_time` |
| LearningPlanResponse | `LearningPlanResponse` | `generate_learning_plan` |
| ErrorResponse | `ErrorResponse` | All tools (error path) |
| Topic | `Topic` | Embedded in CourseInfoResponse |
| PrerequisiteNode | `PrerequisiteNode` | Embedded in PrerequisiteResponse |
| AdjustmentOption | `AdjustmentOption` | Embedded in FeasibilityResponse |
| LearningModule | `LearningModule` | Embedded in LearningPlanResponse |
| DaySchedule | `DaySchedule` | Embedded in LearningPlanResponse |
| Resource | `Resource` | Embedded in LearningPlanResponse |
