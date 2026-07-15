"""
get_prerequisite Tool。

职责: 递归展开先修课程树，验证用户是否满足先修条件。
严格遵循 docs/tool-design.md §4 规范。

单一职责: 输入 → 查询先修树 → 返回检查结果。
"""

from src.tools.course_info import get_course_info
from src.tools.data_loader import load_prerequisite_map

# ── 常量 ──────────────────────────────────────────────────

MAX_RECURSION_DEPTH: int = 5


# ── 公开接口 ──────────────────────────────────────────────

def get_prerequisite(course_name: str, user_knowledge: list[str]) -> dict:
    """检查目标课程的先修条件。

    递归展开先修树（最大深度 5 层），与用户已有知识对比，
    返回是否满足、缺失课程列表、预估先修学时等信息。

    Args:
        course_name: 目标课程名称，大小写不敏感
        user_knowledge: 用户已完成的课程名称列表

    Returns:
        {"success": true, "data": {...PrerequisiteCheck 字段...}}
        {"success": false, "error": {...}}
    """
    # ── 输入验证 ──────────────────────────────────────
    if not course_name or not isinstance(course_name, str):
        return _error(
            "VALIDATION_ERROR",
            "course_name 必须是非空字符串。",
            {"field": "course_name"},
        )
    course_name = course_name.strip()

    if not isinstance(user_knowledge, list):
        return _error(
            "VALIDATION_ERROR",
            "user_knowledge 必须是字符串列表。",
            {"field": "user_knowledge", "received": str(type(user_knowledge))},
        )
    # 清洗: strip + 统一大小写
    user_set: set[str] = {k.strip().lower() for k in user_knowledge if isinstance(k, str) and k.strip()}

    # ── 验证目标课程存在 ──────────────────────────────
    course_result = get_course_info(course_name)
    if not course_result["success"]:
        return _error(
            course_result["error"]["code"],
            course_result["error"]["message"],
            course_result["error"]["details"],
        )
    normalized_name: str = course_result["data"]["name"]

    # ── 加载先修图 ────────────────────────────────────
    try:
        prereq_map: dict = load_prerequisite_map()
    except Exception as exc:
        return _error("INTERNAL_ERROR", f"先修数据加载失败: {exc}", {"exception": str(exc)})

    # ── 递归展开先修树 ────────────────────────────────
    visited: set[str] = set()        # 检测循环依赖
    required_flat: list[str] = []    # 去重的 required 扁平列表
    recommended_flat: list[str] = [] # 去重的 recommended 扁平列表

    try:
        _expand_prerequisites(
            course_name=normalized_name,
            prereq_map=prereq_map,
            user_set=user_set,
            visited=visited,
            required_flat=required_flat,
            recommended_flat=recommended_flat,
            is_first=True,
            depth=0,
        )
    except RecursionError:
        return _error(
            "MAX_RECURSION_DEPTH",
            f"先修树深度超过最大限制 {MAX_RECURSION_DEPTH} 层。",
            {"course": normalized_name, "max_depth": MAX_RECURSION_DEPTH},
        )

    # ── 计算 missing / completed ──────────────────────
    missing: list[str] = [r for r in required_flat if r.lower() not in user_set]
    completed: list[str] = [r for r in required_flat if r.lower() in user_set]

    # ── 计算总先修学时 ────────────────────────────────
    total_hours: float = 0.0
    for name in missing:
        info = get_course_info(name)
        if info["success"]:
            total_hours += info["data"]["hours"]

    # ── 生成概要描述 ──────────────────────────────────
    # 仅陈述事实，不包含学习建议（由 Agent 根据返回数据生成）。
    satisfied: bool = len(missing) == 0
    if satisfied:
        recommendation: str = "所有先修条件已满足。"
    else:
        missing_str: str = "、".join(missing)
        recommendation = (
            f"缺少 {len(missing)} 门先修课: {missing_str}。"
            f"总先修学时: {total_hours:.0f}h。"
        )

    return _success({
        "satisfied": satisfied,
        "course_name": normalized_name,
        "required_prerequisites": required_flat,
        "recommended_prerequisites": recommended_flat,
        "missing": missing,
        "completed": completed,
        "total_prerequisite_hours": total_hours,
        "recommendation": recommendation,
    })


# ── 内部递归函数 ──────────────────────────────────────────

def _expand_prerequisites(
    course_name: str,
    prereq_map: dict,
    user_set: set[str],
    visited: set[str],
    required_flat: list[str],
    recommended_flat: list[str],
    is_first: bool,
    depth: int,
) -> None:
    """递归展开先修树。

    对首次调用的课程展开 required + recommended，
    对递归的课程仅展开 required（避免 recommended 无限扩散）。

    Args:
        course_name: 当前课程名称
        prereq_map: 先修关系图
        user_set: 用户已完成课程集合（小写）
        visited: 已访问课程（防止循环）
        required_flat: [输出] 累积 required 列表
        recommended_flat: [输出] 累积 recommended 列表
        is_first: 是否首次调用（首次展开 recommended）
        depth: 当前递归深度

    Raises:
        RecursionError: 如果检测到循环依赖
    """
    name_lower: str = course_name.lower()

    # 已访问过 → 跳过（共享依赖，非循环。如 Flink→Java 和 Flink→Spark→Hadoop→Java）
    if name_lower in visited:
        return
    if depth > MAX_RECURSION_DEPTH:
        raise RecursionError(f"达到最大递归深度: {depth}")

    visited.add(name_lower)

    # 获取先修数据
    entry: dict = prereq_map.get(course_name, prereq_map.get(name_lower, {}))
    required: list[str] = entry.get("required", [])
    recommended: list[str] = entry.get("recommended", [])

    # 累积 recommended（仅首次调用的目标课程）
    if is_first:
        for rec in recommended:
            if rec not in recommended_flat:
                recommended_flat.append(rec)

    # 递归处理 required 先修课
    for prereq_name in required:
        if prereq_name not in required_flat:
            required_flat.append(prereq_name)

        # 用户已完成此课程 → 跳过其先修的递归展开
        if prereq_name.lower() in user_set:
            continue

        _expand_prerequisites(
            course_name=prereq_name,
            prereq_map=prereq_map,
            user_set=user_set,
            visited=visited,
            required_flat=required_flat,
            recommended_flat=recommended_flat,
            is_first=False,
            depth=depth + 1,
        )


# ── 内部辅助函数 ──────────────────────────────────────────

def _success(data: dict) -> dict:
    """构建统一的成功响应。"""
    return {"success": True, "data": data}


def _error(code: str, message: str, details: dict | None = None) -> dict:
    """构建统一的 ErrorResponse。"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "tool_name": "get_prerequisite",
        },
    }
