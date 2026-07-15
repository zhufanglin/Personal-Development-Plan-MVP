"""
学习路径与每日计划数据模型。

LearningPath = 有序模块列表
DailyPlan   = 按天分配的学习安排
"""

from typing import Literal

from pydantic import BaseModel, Field


# ── DayType ───────────────────────────────────────────────

DayType = Literal["study", "review", "assessment"]


# ── Module ────────────────────────────────────────────────

class Module(BaseModel):
    """学习路径中的一个模块。

    由 Course.topics 转换而来，增加 estimated_days 等计算字段。
    """

    name: str = Field(description="模块名称")
    topic: str = Field(description="关联的主题名称")
    hours: float = Field(ge=0, description="该模块的预估学时")
    order: int = Field(ge=1, description="学习顺序（1-based）")
    required: bool = Field(description="是否为必修模块")
    estimated_days: float = Field(
        ge=0,
        description="完成该模块的预估天数 = hours / daily_hours",
    )


# ── LearningPath ──────────────────────────────────────────

class LearningPath(BaseModel):
    """由有序模块组成的学习路径。"""

    course_name: str = Field(description="课程名称")
    modules: list[Module] = Field(description="按 order 排序的模块列表")
    total_modules: int = Field(ge=0, description="模块总数")
    required_modules: int = Field(ge=0, description="必修模块数")
    optional_modules: int = Field(ge=0, description="可选模块数")
    total_hours: float = Field(ge=0, description="所有模块的总学时")


# ── DayEntry ──────────────────────────────────────────────

class DayEntry(BaseModel):
    """每日学习安排中的一个条目。"""

    day: int = Field(ge=1, description="第几天（1-based）")
    topics: list[str] = Field(description="当天学习的主题名称列表")
    hours: float = Field(ge=0, description="当天学习总学时")
    type: DayType = Field(description="日程类型: study / review / assessment")


# ── DailyPlan ─────────────────────────────────────────────

class DailyPlan(BaseModel):
    """按天分配的学习计划。"""

    days: list[DayEntry] = Field(description="每日学习条目列表")
    total_days: int = Field(ge=0, description="计划总天数")
    total_hours: float = Field(ge=0, description="计划总学时")
    includes_review_days: bool = Field(
        default=False,
        description="是否包含复习日",
    )
    includes_assessments: bool = Field(
        default=False,
        description="是否包含评估日",
    )
