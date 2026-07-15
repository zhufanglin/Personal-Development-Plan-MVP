"""
get_course_info Tool。

职责: 根据课程名称查询课程目录，返回完整元数据。
严格遵循 docs/tool-design.md §3 规范。

单一职责: 输入 → 查询 → 返回结果。
不参与 Agent 决策、Workflow、多 Tool 调度或推理。
"""

from src.models import Course
from src.tools.data_loader import load_courses


def get_course_info(course_name: str) -> dict:
    """查询课程元数据。

    大小写不敏感精确匹配课程名称，返回完整的课程信息。

    Args:
        course_name: 课程名称，大小写不敏感，如 "python" 可匹配 "Python"

    Returns:
        成功: Course 对象的 model_dump() 字典
        失败: {"error": {"code": str, "message": str, "details": dict, "tool_name": str}}

    Raises:
        无 — 所有异常作为 error dict 返回，不向上抛出
    """
    # ── 输入验证 ──────────────────────────────────────
    if not course_name or not isinstance(course_name, str):
        return _error(
            code="VALIDATION_ERROR",
            message="course_name 必须是非空字符串。",
            details={"field": "course_name", "received": str(course_name)},
        )

    if len(course_name) > 100:
        return _error(
            code="VALIDATION_ERROR",
            message="course_name 长度不能超过 100 字符。",
            details={"field": "course_name", "constraint": "max_length=100"},
        )

    # ── 数据加载 ──────────────────────────────────────
    try:
        courses: list[Course] = load_courses()
    except Exception as exc:
        return _error(
            code="INTERNAL_ERROR",
            message=f"课程数据加载失败: {exc}",
            details={"exception": str(exc)},
        )

    # ── 课程查找（大小写不敏感） ───────────────────────
    query_lower: str = course_name.strip().lower()
    available_names: list[str] = [c.name for c in courses]

    for course in courses:
        if course.name.lower() == query_lower:
            return _success(course)

    # ── 未找到 ────────────────────────────────────────
    return _error(
        code="COURSE_NOT_FOUND",
        message=(
            f"课程 '{course_name}' 不在目录中。"
            f"可用课程: {', '.join(available_names)}"
        ),
        details={
            "query": course_name,
            "available_courses": available_names,
        },
    )


# ── 内部辅助函数 ────────────────────────────────────────

def _success(data: Course) -> dict:
    """构建统一的成功响应。

    所有 Tool 使用相同格式: {"success": true, "data": ...}
    """
    return {"success": True, "data": data.model_dump()}


def _error(code: str, message: str, details: dict | None = None) -> dict:
    """构建统一的 ErrorResponse。

    所有 Tool 使用相同格式:
    {"success": false, "error": {"code": str, "message": str, "details": dict, "tool_name": str}}
    """
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "tool_name": "get_course_info",
        },
    }
