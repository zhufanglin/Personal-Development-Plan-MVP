"""
generate_learning_plan Tool (Orchestrator)。

职责: 编排已有 Tool，组装完整学习计划。
纯编排 — 不重新实现课程查询、先修检查、时间计算。

内部组件:
- Scheduler: 每日计划调度 (src/tools/scheduler.py)
- ResourceProvider: 学习资源提供 (src/tools/resource_provider.py)
"""

import time
import uuid
from datetime import datetime, timezone

from src.models import Module
from src.tools.course_info import get_course_info
from src.tools.feasibility import calculate_learning_time
from src.tools.prerequisites import get_prerequisite
from src.tools.resource_provider import HardCodedResourceProvider
from src.tools.scheduler import Scheduler


def generate_learning_plan(
    course_name: str,
    daily_hours: float,
    duration_days: int,
    skip_optional: bool = False,
    start_date: str | None = None,
    user_knowledge: list[str] | None = None,
) -> dict:
    """编排完整学习计划生成流程。

    调用顺序: get_course_info → get_prerequisite → calculate_learning_time
    → _build_learning_path → Scheduler.schedule → ResourceProvider.get_resources

    Args:
        course_name: 课程名称
        daily_hours: 每日学习小时数 (0.5 ~ 16)
        duration_days: 计划学习天数 (1 ~ 365)
        skip_optional: 是否跳过可选模块
        start_date: 开始日期（ISO 格式，可选）
        user_knowledge: 用户已完成的课程列表

    Returns:
        {"success": true, "data": {plan_id, parameters, summary, learning_path,
                                   daily_schedule, resources, warnings, trace}}
        {"success": false, "error": {...}}
    """
    trace: list[dict] = []
    knowledge: list[str] = user_knowledge or []

    # ═══ Step 1: 课程查询 ══════════════════════════════
    t0 = time.perf_counter()
    result = get_course_info(course_name)
    trace.append(_trace_entry(1, "get_course_info", "ok" if result["success"] else "error", t0))
    if not result["success"]:
        return _propagate_error(result["error"], trace)

    course: dict = result["data"]

    # ═══ Step 2: 先修检查 ══════════════════════════════
    t0 = time.perf_counter()
    result = get_prerequisite(course["name"], knowledge)
    trace.append(_trace_entry(2, "get_prerequisite", "ok" if result["success"] else "error", t0))
    if not result["success"]:
        return _propagate_error(result["error"], trace)

    prereq_data: dict = result["data"]
    if not prereq_data["satisfied"]:
        return _error(
            "PREREQUISITE_CONFLICT",
            f"先修条件不满足: 缺少 {len(prereq_data['missing'])} 门先修课。",
            details={
                "course_name": prereq_data["course_name"],
                "missing": prereq_data["missing"],
                "total_prerequisite_hours": prereq_data["total_prerequisite_hours"],
            },
            trace=trace,
        )

    # ═══ Step 3: 可行性评估 ════════════════════════════
    t0 = time.perf_counter()
    result = calculate_learning_time(course["name"], daily_hours, duration_days)
    trace.append(_trace_entry(3, "calculate_learning_time", "ok" if result["success"] else "error", t0))
    if not result["success"]:
        return _propagate_error(result["error"], trace)

    feasibility: dict = result["data"]
    if not feasibility["feasible"]:
        return _error(
            "TIME_INSUFFICIENT",
            f"学习时间不足: 需要 {feasibility['course_total_hours']:.0f}h，"
            f"可用 {feasibility['available_hours']:.0f}h。",
            details={
                "course_total_hours": feasibility["course_total_hours"],
                "available_hours": feasibility["available_hours"],
                "deficit_hours": abs(feasibility["buffer_hours"]),
                "adjustment_options": feasibility["adjustment_options"],
            },
            trace=trace,
        )

    # ═══ Step 4: 构建 LearningPath ═════════════════════
    t0 = time.perf_counter()
    modules, path_summary = _build_learning_path(course, daily_hours, skip_optional)
    trace.append(_trace_entry(4, "_build_learning_path", "ok", t0))

    # ═══ Step 5: Scheduler → DailyPlan ════════════════
    t0 = time.perf_counter()
    scheduler = Scheduler()
    daily_plan: dict = scheduler.schedule(modules, daily_hours, duration_days)
    trace.append(_trace_entry(5, "scheduler.schedule", "ok", t0))

    # ═══ Step 6: ResourceProvider → Resources ═════════
    t0 = time.perf_counter()
    provider = HardCodedResourceProvider()
    resources: list[dict] = []
    for topic in course.get("topics", []):
        resources.extend(provider.get_resources(topic["name"], course["difficulty"]))
    if not resources:
        resources.extend(provider.get_resources("通用", course["difficulty"]))
    trace.append(_trace_entry(6, "resource_provider.get_resources", "ok", t0))

    # ═══ 组装最终响应 ══════════════════════════════════
    warnings: list[str] = _build_warnings(daily_plan, duration_days, feasibility)

    return {
        "success": True,
        "data": {
            "plan_id": str(uuid.uuid4()),
            "course_name": course["name"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "parameters": {
                "daily_hours": daily_hours,
                "duration_days": duration_days,
                "skip_optional": skip_optional,
                "start_date": start_date,
            },
            "summary": {
                "total_modules": path_summary["total"],
                "required_modules": path_summary["required"],
                "optional_modules": path_summary["optional"],
                "skipped_modules": path_summary["skipped"],
                "total_learning_hours": path_summary["total_hours"],
                "study_days": sum(1 for d in daily_plan["days"] if d["type"] == "study"),
                "review_days": sum(1 for d in daily_plan["days"] if d["type"] == "review"),
                "assessment_days": sum(1 for d in daily_plan["days"] if d["type"] == "assessment"),
                "total_days": daily_plan["total_days"],
            },
            "learning_path": modules,
            "daily_schedule": daily_plan["days"],
            "resources": resources,
            "warnings": warnings,
            "trace": trace,
        },
    }


# ── LearningPath 构建 ─────────────────────────────────────

def _build_learning_path(
    course: dict,
    daily_hours: float,
    skip_optional: bool,
) -> tuple[list[dict], dict]:
    """将 Course.topics 转换为 LearningPath。

    纯数据转换 — 不涉及业务逻辑。

    Returns:
        (modules_dicts, summary_dict)
    """
    topics: list[dict] = course.get("topics", [])
    modules: list[dict] = []
    required_count: int = 0
    optional_count: int = 0
    skipped_count: int = 0

    for t in topics:
        is_required: bool = t.get("required", True)

        if not is_required and skip_optional:
            skipped_count += 1
            continue

        if is_required:
            required_count += 1
        else:
            optional_count += 1

        m = Module(
            name=t["name"],
            topic=t["name"],
            hours=t["hours"],
            order=t["order"],
            required=is_required,
            estimated_days=t["hours"] / daily_hours if daily_hours > 0 else 0,
        )
        modules.append(m.model_dump())

    summary = {
        "total": len(modules),
        "required": required_count,
        "optional": optional_count,
        "skipped": skipped_count,
        "total_hours": sum(m["hours"] for m in modules),
    }
    return modules, summary


# ── Warnings ───────────────────────────────────────────────

def _build_warnings(
    daily_plan: dict,
    duration_days: int,
    feasibility: dict,
) -> list[str]:
    """根据计划情况生成警告列表。"""
    warnings: list[str] = []

    if daily_plan["total_days"] > duration_days:
        warnings.append(
            f"计划需要 {daily_plan['total_days']} 天，超过预算的 {duration_days} 天。"
            f"建议延长周期或增加每日学习时间。"
        )

    if not feasibility["buffer_sufficient"]:
        warnings.append(
            f"缓冲时间不足建议的 20%。"
            f"建议预留额外复习时间。"
        )

    return warnings


# ── 辅助函数 ───────────────────────────────────────────────

def _trace_entry(step: int, tool: str, status: str, t0: float) -> dict:
    """构建一条 trace 记录。"""
    elapsed_ms: int = round((time.perf_counter() - t0) * 1000)
    return {"step": step, "tool": tool, "status": status, "elapsed_ms": elapsed_ms}


def _propagate_error(error: dict, trace: list[dict]) -> dict:
    """传播上游 Tool 的错误。"""
    error["trace"] = trace
    return {"success": False, "error": error}


def _error(code: str, message: str, details: dict | None = None, trace: list[dict] | None = None) -> dict:
    """构建 Orchestrator 自己的错误响应。"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "tool_name": "generate_learning_plan",
        },
        **({"trace": trace} if trace else {}),
    }
