"""
数据模型层。

Pydantic v2 BaseModel 类，提供类型安全、运行时验证和序列化。
所有字段命名与 data/courses.json 保持一致。
"""

from src.models.course import Course, Difficulty, Resource, ResourceType, Topic
from src.models.feasibility import (
    AdjustmentOption,
    FeasibilityResult,
    PrerequisiteCheck,
)
from src.models.learning_path import (
    DayEntry,
    DayType,
    DailyPlan,
    LearningPath,
    Module,
)

__all__ = [
    # course
    "Topic",
    "Course",
    "Difficulty",
    "Resource",
    "ResourceType",
    # learning_path
    "Module",
    "LearningPath",
    "DayEntry",
    "DailyPlan",
    "DayType",
    # feasibility
    "FeasibilityResult",
    "AdjustmentOption",
    "PrerequisiteCheck",
]
