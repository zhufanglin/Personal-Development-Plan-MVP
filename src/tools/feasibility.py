"""
calculate_learning_time Tool。

职责: 评估学习目标的时间可行性，不可行时提供三种调整方案。
严格遵循 docs/tool-design.md §5 规范。

单一职责: 输入 → 计算 → 返回评估结果。
不生成学习计划、不参与 Agent 决策。
"""

import math

from src.models import AdjustmentOption
from src.tools.course_info import get_course_info

# ── 常量配置 ──────────────────────────────────────────────

RECOMMENDED_BUFFER_RATIO: float = 0.2
MIN_DAILY_HOURS: float = 0.5
MAX_DAILY_HOURS: float = 16.0
MIN_DURATION_DAYS: int = 1
MAX_DURATION_DAYS: int = 365


# ── 公开接口 ──────────────────────────────────────────────

def calculate_learning_time(
    course_name: str,
    daily_hours: float,
    duration_days: int,
) -> dict:
    """评估课程学习时间可行性。

    Args:
        course_name: 课程名称，大小写不敏感
        daily_hours: 每日学习小时数 (0.5 ~ 16)
        duration_days: 计划学习天数 (1 ~ 365)

    Returns:
        {"success": true, "data": {...FeasibilityResult 字段...}}
        {"success": false, "error": {...}}
    """
    # ── 输入验证 ──────────────────────────────────────
    if not course_name or not isinstance(course_name, str):
        return _error("VALIDATION_ERROR", "course_name 必须是非空字符串。", {"field": "course_name"})
    course_name = course_name.strip()

    if not isinstance(daily_hours, (int, float)) or daily_hours < MIN_DAILY_HOURS or daily_hours > MAX_DAILY_HOURS:
        return _error(
            "VALIDATION_ERROR",
            f"daily_hours 必须在 {MIN_DAILY_HOURS} ~ {MAX_DAILY_HOURS} 之间，收到 {daily_hours}。",
            {"field": "daily_hours", "constraint": f"{MIN_DAILY_HOURS} <= daily_hours <= {MAX_DAILY_HOURS}"},
        )

    if not isinstance(duration_days, int) or duration_days < MIN_DURATION_DAYS or duration_days > MAX_DURATION_DAYS:
        return _error(
            "VALIDATION_ERROR",
            f"duration_days 必须在 {MIN_DURATION_DAYS} ~ {MAX_DURATION_DAYS} 之间，收到 {duration_days}。",
            {"field": "duration_days", "constraint": f"{MIN_DURATION_DAYS} <= duration_days <= {MAX_DURATION_DAYS}"},
        )

    # ── 获取课程数据 ──────────────────────────────────
    result = get_course_info(course_name)
    if not result["success"]:
        return _error(
            result["error"]["code"],
            result["error"]["message"],
            result["error"]["details"],
        )

    course: dict = result["data"]
    course_total_hours: float = course["hours"]

    # ── 核心计算 ──────────────────────────────────────
    available_hours: float = daily_hours * duration_days
    buffer_hours: float = available_hours - course_total_hours
    buffer_ratio: float = buffer_hours / course_total_hours if course_total_hours > 0 else 0.0
    recommended_buffer: float = course_total_hours * RECOMMENDED_BUFFER_RATIO
    buffer_sufficient: bool = buffer_hours >= recommended_buffer
    minimum_days_needed: float = math.ceil(course_total_hours / daily_hours) if daily_hours > 0 else float("inf")
    minimum_hours_per_day: float = round(course_total_hours / duration_days, 1) if duration_days > 0 else float("inf")

    feasible: bool = buffer_hours >= 0

    # ── 调整方案（仅不可行时生成） ────────────────────
    adjustment_options: list[dict] = []
    if not feasible:
        adjustment_options = _build_adjustment_options(
            course=course,
            daily_hours=daily_hours,
            duration_days=duration_days,
            course_total_hours=course_total_hours,
        )

    # ── 概要描述 ──────────────────────────────────────
    if feasible:
        if buffer_sufficient:
            recommendation: str = (
                f"学习目标可行。可用 {available_hours:.0f}h，需要 {course_total_hours:.0f}h，"
                f"缓冲 {buffer_hours:.0f}h ({buffer_ratio:.0%})。"
            )
        else:
            recommendation = (
                f"学习目标可行但时间较紧。可用 {available_hours:.0f}h，需要 {course_total_hours:.0f}h，"
                f"缓冲仅 {buffer_hours:.0f}h，低于建议的 {recommended_buffer:.0f}h (20%)。"
                f"建议预留额外复习时间。"
            )
    else:
        recommendation = (
            f"学习目标不可行。需要 {course_total_hours:.0f}h，"
            f"但仅有 {available_hours:.0f}h 可用，缺口 {abs(buffer_hours):.0f}h。"
            f"请查看 adjustment_options 获取调整方案。"
        )

    return _success({
        "feasible": feasible,
        "course_name": course["name"],
        "course_total_hours": course_total_hours,
        "daily_hours": daily_hours,
        "duration_days": duration_days,
        "available_hours": available_hours,
        "buffer_hours": buffer_hours,
        "buffer_ratio": buffer_ratio,
        "recommended_buffer": recommended_buffer,
        "buffer_sufficient": buffer_sufficient,
        "minimum_days_needed": minimum_days_needed,
        "minimum_hours_per_day": minimum_hours_per_day,
        "adjustment_options": adjustment_options,
        "recommendation": recommendation,
    })


# ── 内部函数 ──────────────────────────────────────────────

def _build_adjustment_options(
    course: dict,
    daily_hours: float,
    duration_days: int,
    course_total_hours: float,
) -> list[dict]:
    """构建三种调整方案。

    Args:
        course: 课程数据字典
        daily_hours: 当前每日小时数
        duration_days: 当前学习天数
        course_total_hours: 课程总学时

    Returns:
        list[dict]: 三种 AdjustmentOption 的字典列表
    """
    options: list[dict] = []

    # 方案 A: 延长学习周期
    new_days: int = math.ceil(course_total_hours / daily_hours)
    options.append(
        AdjustmentOption(
            strategy="extend_duration",
            label="方案 A: 延长学习周期",
            description=(
                f"保持每天学习 {daily_hours} 小时，"
                f"将学习周期从 {duration_days} 天延长至 {new_days} 天。"
            ),
            new_duration_days=new_days,
        ).model_dump()
    )

    # 方案 B: 增加每日学习时间
    new_hours: float = math.ceil(course_total_hours / duration_days * 10) / 10
    options.append(
        AdjustmentOption(
            strategy="increase_hours",
            label="方案 B: 增加每日学习时间",
            description=(
                f"保持 {duration_days} 天的学习周期，"
                f"将每日学习时间从 {daily_hours} 小时增加到 {new_hours} 小时。"
            ),
            new_daily_hours=new_hours,
        ).model_dump()
    )

    # 方案 C: 缩减学习范围（仅保留必修模块）
    required_hours: float = sum(
        t["hours"] for t in course.get("topics", []) if t.get("required", True)
    )
    options.append(
        AdjustmentOption(
            strategy="reduce_scope",
            label="方案 C: 缩减学习范围",
            description=(
                f"跳过可选模块，必学模块降至 {required_hours:.0f}h。"
                f"（原始总学时 {course_total_hours:.0f}h）"
            ),
            reduced_hours=required_hours,
        ).model_dump()
    )

    return options


# ── 内部辅助函数 ──────────────────────────────────────────

def _success(data: dict) -> dict:
    return {"success": True, "data": data}


def _error(code: str, message: str, details: dict | None = None) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "tool_name": "calculate_learning_time",
        },
    }
