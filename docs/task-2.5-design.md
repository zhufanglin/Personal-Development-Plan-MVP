# Task 2.5 Design — `generate_learning_plan` Orchestrator

| Field | Value |
|-------|-------|
| Status | Draft — awaiting confirmation |
| Tool Type | Orchestrator（编排器） |
| Dependencies | get_course_info, get_prerequisite, calculate_learning_time |

---

## 1. Orchestrator 定位

```
┌─────────────────────────────────────────────────────────────┐
│                  generate_learning_plan                     │
│                    (Orchestrator)                           │
│                                                             │
│  职责:                                                      │
│  ✓ Tool 编排（调用已有 Tool，按顺序组合）                    │
│  ✓ 结果整合（组装 LearningPath + DailyPlan + Resources）    │
│  ✓ 错误传播（上游 Tool 返回错误时，包装后向上传递）          │
│                                                             │
│  不负责:                                                    │
│  ✗ 课程查询 → 调用 get_course_info                         │
│  ✗ 先修检查 → 调用 get_prerequisite                       │
│  ✗ 时间计算 → 调用 calculate_learning_time                 │
│  ✗ Agent 决策 / Workflow / Prompt                          │
└─────────────────────────────────────────────────────────────┘
```

## 2. 调用流程

```
generate_learning_plan(course_name, daily_hours, duration_days, skip_optional, start_date)
    │
    │  ═══ Step 1: 课程查询 ═══
    ├── get_course_info(course_name)
    │       Input:  {"course_name": "Python"}
    │       Output: {"success": true, "data": {Course}}
    │       Error:  COURSE_NOT_FOUND → return error (课程不存在)
    │
    │  ═══ Step 2: 先修检查 ═══
    ├── get_prerequisite(course_name, user_knowledge)
    │       Input:  {"course_name": "Python", "user_knowledge": [...]}
    │       Output: {"success": true, "data": {PrerequisiteCheck}}
    │       Branch: satisfied=false → return PREREQUISITE_CONFLICT
    │
    │  ═══ Step 3: 可行性评估 ═══
    ├── calculate_learning_time(course_name, daily_hours, duration_days)
    │       Input:  {"course_name": "Python", "daily_hours": 3, "duration_days": 12}
    │       Output: {"success": true, "data": {FeasibilityResult}}
    │       Branch: feasible=false → return TIME_INSUFFICIENT
    │               ↓ (附带 adjustment_options 给 Agent 参考)
    │
    │  ═══ Step 4: 构建 LearningPath ═══
    ├── _build_learning_path(course, daily_hours, skip_optional)
    │       Input:  Course.topics, daily_hours, skip_optional
    │       Output: LearningPath dict
    │
    │  ═══ Step 5: 构建 DailyPlan ═══
    ├── _build_daily_plan(modules, daily_hours, duration_days, start_date)
    │       Input:  list[Module], daily_hours, duration_days, start_date
    │       Output: DailyPlan dict
    │
    │  ═══ Step 6: 收集 Resources ═══
    ├── _collect_resources(course, modules)
    │       Input:  Course.topics, Course.difficulty
    │       Output: list[Resource dict]
    │
    │  ═══ 组装最终响应 ═══
    └── return {
            "success": true,
            "data": {
                "plan_id": "<uuid>",
                "course_name": "...",
                "generated_at": "<ISO8601>",
                "parameters": {...},
                "summary": {...},
                "learning_path": [...],
                "daily_schedule": [...],
                "resources": [...],
                "warnings": [...]
            }
        }
```

## 3. 每一步的输入输出

### Step 1: get_course_info

| 方向 | 字段 | 值 |
|------|------|-----|
| → 输入 | `course_name` | `"Python"` |
| ← 输出 | `data.name` | `"Python"` |
| ← 输出 | `data.hours` | `24.0` |
| ← 输出 | `data.topics` | `[{name, hours, order, required}, ...]` (7 items) |
| ← 错误 | `COURSE_NOT_FOUND` | 直接返回，附带 available_courses |

### Step 2: get_prerequisite

| 方向 | 字段 | 值 |
|------|------|-----|
| → 输入 | `course_name` + `user_knowledge` | `"Spark"`, `["Python"]` |
| ← 输出 | `data.satisfied` | `false` |
| ← 输出 | `data.missing` | `["Hadoop", "Linux", "Java"]` |
| ← 输出 | `data.total_prerequisite_hours` | `88.0` |
| ← 分支 | `satisfied=false` | 返回 PREREQUISITE_CONFLICT error，附带 missing 列表 |

### Step 3: calculate_learning_time

| 方向 | 字段 | 值 |
|------|------|-----|
| → 输入 | `course_name` + `daily_hours` + `duration_days` | `"Python"`, 3, 12 |
| ← 输出 | `data.feasible` | `true` |
| ← 输出 | `data.buffer_hours` | `12.0` |
| ← 分支 | `feasible=false` | 返回 TIME_INSUFFICIENT error，附带 adjustment_options |

### Step 4: _build_learning_path

| 方向 | 字段 | 说明 |
|------|------|------|
| → 输入 | `course.topics` | `[{name, hours, order, required}, ...]` |
| → 输入 | `daily_hours` | 用于计算 estimated_days |
| → 输入 | `skip_optional` | True 时排除 required=false 的 topic |
| ← 输出 | `modules` | `[{name, topic, hours, order, required, estimated_days}, ...]` |
| ← 输出 | `total_modules` | 模块总数 |
| ← 输出 | `required_modules` | 必修模块数 |
| ← 输出 | `optional_modules` | 可选模块数 |
| ← 输出 | `total_hours` | 包含模块的总学时 |

### Step 5: _build_daily_plan

**贪心打包算法:**

```
剩余模块队列 = modules (按 order 排序)
current_day = 1
day_entries = []

while 队列非空:
    当日剩余小时 = daily_hours
    当日模块列表 = []

    while 当日剩余小时 > 0 且 队列非空:
        取队首模块 m
        可分配小时 = min(当日剩余小时, m.remaining_hours())
        当日模块列表.append({module: m.name, hours: 可分配小时, continuation: ...})
        当日剩余小时 -= 可分配小时
        m.remaining_hours -= 可分配小时
        if m.remaining_hours == 0: 出队

    day_entries.append(DayEntry(day=current_day, topics=[...], hours=..., type="study"))
    current_day += 1

    # 每 5 个学习日插入 1 个复习日
    if current_day % 6 == 0:
        day_entries.append(DayEntry(day=current_day, topics=[], hours=daily_hours, type="review"))
        current_day += 1

# 最后插入 1 个评估日
day_entries.append(DayEntry(day=current_day, topics=[], hours=daily_hours, type="assessment"))
```

| 方向 | 字段 | 说明 |
|------|------|------|
| → 输入 | `modules` | LearningPath.modules |
| → 输入 | `daily_hours` | 每日可用小时 |
| → 输入 | `duration_days` | 用户计划天数 |
| ← 输出 | `days` | `[{day, topics, hours, type}, ...]` |
| ← 输出 | `total_days` | 计划实际天数 |
| ← 输出 | `total_hours` | 计划总学时 |
| ← 输出 | `includes_review_days` | 是否含复习日 |
| ← 输出 | `includes_assessments` | 是否含评估日 |

**边界情况:**
- 如果 total_days > duration_days → 发出 warning（时间紧张）
- 如果 total_days < duration_days → 正常（有缓冲，剩余天数用户自行安排）

### Step 6: _collect_resources

| 方向 | 字段 | 说明 |
|------|------|------|
| → 输入 | `topics` | Course.topics |
| → 输入 | `difficulty` | Course.difficulty |
| ← 输出 | `resources` | `[{title, type, url, topic, estimated_hours, free, difficulty}, ...]` |

MVP 方案: 内置硬编码资源映射表（按 topic 名称关键词匹配），每 topic 返回 1-2 条。后续可扩展为 `data/resources.json`。

## 4. 错误传播策略

```
上游 Tool 返回错误 → generate_learning_plan 包装后向上传递

get_course_info error:
    → generate_learning_plan 直接返回 (不改变 error 结构)

get_prerequisite error / satisfied=false:
    → PREREQUISITE_CONFLICT
    → error.details 中附带: course_name, missing_prerequisites, total_hours

calculate_learning_time error / feasible=false:
    → TIME_INSUFFICIENT
    → error.details 中附带: course_total_hours, available_hours, deficit, adjustment_options

内部错误 (_build_*):
    → INTERNAL_ERROR
```

**关键原则:** Orchestrator 自己不生成错误码，只传递或包装上游错误。唯一的例外是 `INTERNAL_ERROR`（内部异常）。

## 5. 输出 Schema (最终响应)

```json
{
    "success": true,
    "data": {
        "plan_id": "uuid-v4",
        "course_name": "Python",
        "generated_at": "2026-07-11T15:30:00Z",
        "parameters": {
            "daily_hours": 3.0,
            "duration_days": 12,
            "skip_optional": false,
            "start_date": null
        },
        "summary": {
            "total_modules": 7,
            "required_modules": 6,
            "optional_modules": 1,
            "skipped_modules": 0,
            "total_learning_hours": 24.0,
            "study_days": 9,
            "review_days": 1,
            "assessment_days": 1,
            "total_days": 11
        },
        "learning_path": [
            {"name": "变量与数据类型", "hours": 3.0, "order": 1, "required": true, "estimated_days": 1.0}
        ],
        "daily_schedule": [
            {"day": 1, "type": "study", "modules": [...], "total_hours": 3.0}
        ],
        "resources": [
            {"title": "Python 官方教程", "type": "documentation", "topic": "变量与数据类型", ...}
        ],
        "warnings": []
    }
}
```

## 6. 调用流程图

```
                    ┌──────────────────────────────┐
                    │  generate_learning_plan()    │
                    │  输入: course_name,          │
                    │        daily_hours,          │
                    │        duration_days,        │
                    │        skip_optional,        │
                    │        start_date,           │
                    │        user_knowledge        │
                    └────────────┬─────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │ Step 1: get_course_info  │
                    │ → 课程元数据              │
                    └────────────┬─────────────┘
                                 │
                          ┌──────┴──────┐
                          │ course      │
                          │ found?      │
                          └──────┬──────┘
                            YES  │  NO
                                 │
                    ┌────────────▼─────────────┐    ┌─────────────────┐
                    │ Step 2: get_prerequisite │    │ Return Error:    │
                    │ → 先修检查结果            │    │ COURSE_NOT_FOUND │
                    └────────────┬─────────────┘    └─────────────────┘
                                 │
                          ┌──────┴──────┐
                          │ satisfied?  │
                          └──────┬──────┘
                            YES  │  NO
                                 │
                    ┌────────────▼──────────────┐   ┌──────────────────────┐
                    │ Step 3: calculate_        │   │ Return Error:         │
                    │          learning_time    │   │ PREREQUISITE_CONFLICT │
                    │ → 可行性评估              │   │ + missing + hours     │
                    └────────────┬──────────────┘   └──────────────────────┘
                                 │
                          ┌──────┴──────┐
                          │ feasible?   │
                          └──────┬──────┘
                            YES  │  NO
                                 │
              ┌──────────────────┴───────────────────┐
              │                                       │
    ┌─────────▼──────────┐              ┌────────────▼──────────────┐
    │ Step 4:             │              │ Return Error:              │
    │ _build_learning_path│              │ TIME_INSUFFICIENT          │
    │ → LearningPath      │              │ + adjustment_options       │
    └─────────┬───────────┘              └────────────────────────────┘
              │
    ┌─────────▼──────────┐
    │ Step 5:             │
    │ _build_daily_plan   │
    │ → DailyPlan         │
    └─────────┬───────────┘
              │
    ┌─────────▼──────────┐
    │ Step 6:             │
    │ _collect_resources  │
    │ → list[Resource]    │
    └─────────┬───────────┘
              │
    ┌─────────▼──────────┐
    │ Assemble Response   │
    │ plan_id + summary   │
    │ + warnings          │
    └─────────┬───────────┘
              │
              ▼
    {"success": true, "data": {...完整学习计划...}}
```

## 7. 与已有 Tool 的关系

| 已有 Tool | generate_learning_plan 如何使用 |
|-----------|-------------------------------|
| `get_course_info` | 直接调用。获取 topics 用于构建 LearningPath |
| `get_prerequisite` | 直接调用。检查先修，不满足则终止 |
| `calculate_learning_time` | 直接调用。检查可行性，不可行则终止并返回调整方案 |

**不重复实现:** 所有业务逻辑（查询、先修、计算）通过调用已有 Tool 函数完成。generate_learning_plan 只负责编排和组装。

## 8. 内部组件设计

### 8.1 Scheduler（调度器）

将每日计划生成逻辑从 Orchestrator 中分离为独立的 `Scheduler` 类。

```
Scheduler
├── schedule(modules, daily_hours, duration_days, start_date) → DailyPlan
│
├── _pack_modules(modules, daily_hours) → list[DayEntry]
│      贪心打包: 每天填充至 daily_hours，跨天模块标记 continuation
│
├── _insert_review_days(days, interval=5) → list[DayEntry]
│      每 N 个学习日插入 1 个复习日
│
├── _insert_assessment_day(days) → list[DayEntry]
│      最后一个模块后插入 1 个评估日
│
└── _calculate_totals(days) → (total_days, total_hours, has_review, has_assessment)
```

**设计原则:**
- Scheduler 不知道 Course/Topic/LearningPath — 只接收 `list[Module]`
- Scheduler 不关心业务语义 — 只做数学调度
- Orchestrator 调用 `scheduler.schedule(modules, daily_hours, duration_days)` 即可

### 8.2 ResourceProvider（资源提供者）

使用 Provider 模式，为未来扩展预留接口。

```
ResourceProvider (Protocol)
├── get_resources(topic: str, difficulty: str) → list[Resource]
└── 实现:
    ├── HardCodedResourceProvider  (MVP: 内置映射表)
    ├── WebResourceProvider        (Future: 在线搜索)
    └── RAGResourceProvider        (Future: 向量检索)
```

**MVP 实现:**
- `HardCodedResourceProvider` 内部维护 `{关键词: [Resource, ...]}` 映射表
- 按 topic.name 关键词匹配（如 "变量" → Python 官方教程）
- Orchestrator 通过 `provider.get_resources(topic_name, difficulty)` 调用

### 8.3 Trace（执行追踪）

最终响应中增加 `trace` 字段，记录每个步骤的执行状态。

```json
{
    "trace": [
        {"step": 1, "tool": "get_course_info", "status": "ok", "elapsed_ms": 2},
        {"step": 2, "tool": "get_prerequisite", "status": "ok", "elapsed_ms": 5},
        {"step": 3, "tool": "calculate_learning_time", "status": "ok", "elapsed_ms": 3},
        {"step": 4, "component": "_build_learning_path", "status": "ok", "elapsed_ms": 1},
        {"step": 5, "component": "scheduler.schedule", "status": "ok", "elapsed_ms": 2},
        {"step": 6, "component": "provider.get_resources", "status": "ok", "elapsed_ms": 1}
    ]
}
```

## 9. 更新后的完整流程

```
generate_learning_plan(course_name, daily_hours, duration_days, skip_optional, start_date, user_knowledge)
    │
    ├── [trace #1] get_course_info(course_name)
    │       → Course data or COURSE_NOT_FOUND
    │
    ├── [trace #2] get_prerequisite(course_name, user_knowledge)
    │       → PrerequisiteCheck or PREREQUISITE_CONFLICT
    │
    ├── [trace #3] calculate_learning_time(course_name, daily_hours, duration_days)
    │       → FeasibilityResult or TIME_INSUFFICIENT
    │
    ├── [trace #4] _build_learning_path(course.topics, daily_hours, skip_optional)
    │       → LearningPath (纯数据转换，无业务逻辑)
    │
    ├── [trace #5] Scheduler.schedule(modules, daily_hours, duration_days, start_date)
    │       → DailyPlan (贪心打包 + 复习日 + 评估日)
    │
    ├── [trace #6] ResourceProvider.get_resources(topics, difficulty)
    │       → list[Resource] (HardCodedProvider)
    │
    └── assemble → {"success": true, "data": {..., "trace": [...]}}
```

## 10. 文件规划

| 文件 | 内容 |
|------|------|
| `src/tools/learning_plan.py` | `generate_learning_plan()` 主函数 + `_build_learning_path()` |
| `src/tools/scheduler.py` | `Scheduler` 类（贪心打包/复习日/评估日） |
| `src/tools/resource_provider.py` | `ResourceProvider` Protocol + `HardCodedResourceProvider` |

## 11. 边界情况

| 场景 | 处理 |
|------|------|
| 课程只有必修模块 | optional_modules=0, skipped_modules=0 |
| skip_optional=true 后无模块 | 不应发生（每门课至少1个必修模块）。防御: INTERNAL_ERROR |
| 每日时间不足以完成最小的单个模块 | 模块跨天（continuation=true） |
| total_days > duration_days | 发出 warning: "计划需要 N 天，超过你的 M 天预算" |
| 课程只有1个模块 | 正常处理，review/assessment days 照常插入 |
