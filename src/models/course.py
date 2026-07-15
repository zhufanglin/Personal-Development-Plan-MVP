"""
课程与主题数据模型。

字段命名与 data/courses.json 保持一致，确保全链路一致性：
  JSON → Pydantic Model → Tool → API
"""

from typing import Literal

from pydantic import BaseModel, Field


# ── ResourceType ───────────────────────────────────────────

ResourceType = Literal["video", "book", "article", "course", "tutorial", "documentation"]


# ── 难度等级 ──────────────────────────────────────────────

Difficulty = Literal["beginner", "intermediate", "advanced"]


# ── Topic ─────────────────────────────────────────────────

class Topic(BaseModel):
    """课程中的单个学习主题。

    对应 courses.json 中 topics[] 的每个元素。
    """

    name: str = Field(
        min_length=1,
        max_length=100,
        description="主题名称，如 '变量与数据类型'",
    )
    hours: float = Field(ge=0, description="该主题的预估学时")
    order: int = Field(ge=1, description="学习顺序（1-based）")
    required: bool = Field(description="是否为必修模块")
    description: str = Field(
        default="",
        description="该主题的简要说明",
    )


# ── Course ────────────────────────────────────────────────

class Course(BaseModel):
    """课程完整元数据。

    对应 courses.json 中 courses[] 的每个元素。
    字段名与 JSON 完全一致，无 alias。
    """

    id: str = Field(
        description="课程唯一编号，如 'COURSE-PY-001'",
        pattern=r"^COURSE-[A-Z]+-\d{3}$",
    )
    name: str = Field(
        min_length=1,
        max_length=100,
        description="课程名称，如 'Python'",
    )
    hours: float = Field(
        ge=0,
        description="课程预估总学时（含必修和可选模块）",
    )
    difficulty: Difficulty = Field(
        description="难度等级: beginner / intermediate / advanced",
    )
    prerequisite: list[str] = Field(
        default_factory=list,
        description="必须先修的课程名称列表（硬性要求）",
    )
    description: str = Field(
        min_length=1,
        description="课程概述（1-3 句话）",
    )
    category: str = Field(
        default="",
        description="课程分类，如 'programming' / 'big-data' / 'database'",
    )
    topics: list[Topic] = Field(
        min_length=1,
        description="按 order 升序排列的学习主题列表",
    )


# ── Resource ───────────────────────────────────────────────

class Resource(BaseModel):
    """学习资源。

    由 generate_learning_plan Tool 的 resources 列表返回。
    """

    title: str = Field(min_length=1, description="资源标题")
    type: ResourceType = Field(description="资源类型")
    url: str | None = Field(default=None, description="资源链接")
    topic: str = Field(description="关联的主题名称")
    estimated_hours: float | None = Field(
        default=None,
        ge=0,
        description="预计耗时（小时）",
    )
    free: bool = Field(default=True, description="是否免费")
    difficulty: Difficulty = Field(description="难度等级")
