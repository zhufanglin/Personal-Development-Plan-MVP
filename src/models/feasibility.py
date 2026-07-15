"""
可行性与先修检查结果数据模型。
"""

from pydantic import BaseModel, Field


# ── FeasibilityResult ─────────────────────────────────────

class FeasibilityResult(BaseModel):
    """时间可行性评估结果。

    由 calculate_learning_time Tool 返回。
    """

    feasible: bool = Field(description="学习目标是否可行")
    course_name: str = Field(description="课程名称")
    course_total_hours: float = Field(ge=0, description="课程总学时")
    daily_hours: float = Field(ge=0, description="每日学习小时数")
    duration_days: int = Field(ge=0, description="计划学习天数")
    available_hours: float = Field(ge=0, description="总可用时间 = daily_hours * duration_days")
    buffer_hours: float = Field(description="时间缓冲 = available_hours - course_total_hours（可为负）")
    buffer_ratio: float = Field(description="缓冲比例 = buffer_hours / course_total_hours")
    minimum_days_needed: float = Field(ge=0, description="最少需要天数 = ceil(course_total_hours / daily_hours)")
    minimum_hours_per_day: float = Field(ge=0, description="最少每日小时数 = ceil(course_total_hours / duration_days)")
    recommendation: str = Field(description="人类可读的评估建议")


# ── AdjustmentOption ──────────────────────────────────────

class AdjustmentOption(BaseModel):
    """时间不足时的调整方案。"""

    strategy: str = Field(
        description="调整策略: extend_duration / increase_hours / reduce_scope",
    )
    label: str = Field(description="方案标题（中文）")
    description: str = Field(description="方案详细说明")
    new_daily_hours: float | None = Field(
        default=None,
        description="调整后的每日小时数（仅 increase_hours 策略）",
    )
    new_duration_days: int | None = Field(
        default=None,
        description="调整后的学习天数（仅 extend_duration 策略）",
    )
    reduced_hours: float | None = Field(
        default=None,
        description="缩减后的学时（仅 reduce_scope 策略）",
    )


# ── PrerequisiteCheck ─────────────────────────────────────

class PrerequisiteCheck(BaseModel):
    """先修条件检查结果。

    由 get_prerequisite Tool 返回。
    """

    satisfied: bool = Field(description="是否满足全部 required 先修条件")
    course_name: str = Field(description="目标课程名称")
    required_prerequisites: list[str] = Field(
        default_factory=list,
        description="所有 required 先修课名称（扁平去重列表）",
    )
    recommended_prerequisites: list[str] = Field(
        default_factory=list,
        description="所有 recommended 先修课名称",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="required 中用户尚未完成的课程",
    )
    completed: list[str] = Field(
        default_factory=list,
        description="required 中用户已完成的课程",
    )
    total_prerequisite_hours: float = Field(
        default=0.0,
        ge=0,
        description="完成所有 missing 先修课所需的最少学时",
    )
    recommendation: str = Field(
        default="",
        description="人类可读的建议文本",
    )
