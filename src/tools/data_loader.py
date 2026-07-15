"""
数据加载器。

负责从 data/ 目录加载 JSON 文件，并使用 Pydantic 模型进行验证。
保持简单（MVP）：不实现缓存、数据库或其他持久化逻辑。
未来可通过替换本模块接入缓存或数据库，接口保持不变。
"""

import json
from pathlib import Path
from typing import Any

from src.exceptions import DataCorruptionError
from src.models import Course

# ── 数据文件路径（相对于项目根目录） ─────────────────────────

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

COURSES_PATH = _DATA_DIR / "courses.json"
PREREQUISITES_PATH = _DATA_DIR / "prerequisites.json"


# ── 公开接口 ────────────────────────────────────────────────

def load_courses() -> list[Course]:
    """加载并验证所有课程数据。

    从 data/courses.json 读取原始 JSON，逐条通过 Pydantic Course 模型
    验证，返回验证后的 Course 对象列表。

    Returns:
        list[Course]: 已验证的课程对象列表

    Raises:
        FileNotFoundError: 如果 courses.json 不存在
        DataCorruptionError: 如果 JSON 解析或 Pydantic 验证失败
    """
    raw = _read_json(COURSES_PATH)

    try:
        courses_data: list[dict[str, Any]] = raw["courses"]
    except (KeyError, TypeError) as exc:
        raise DataCorruptionError(
            f"courses.json 缺少 'courses' 顶层键: {exc}",
            details={"file": str(COURSES_PATH)},
        ) from exc

    if not isinstance(courses_data, list):
        raise DataCorruptionError(
            "courses.json 中 'courses' 必须是数组",
            details={"file": str(COURSES_PATH), "type": str(type(courses_data))},
        )

    courses: list[Course] = []
    for i, item in enumerate(courses_data):
        try:
            courses.append(Course(**item))
        except Exception as exc:
            raise DataCorruptionError(
                f"courses.json 第 {i} 条数据验证失败: {exc}",
                details={
                    "file": str(COURSES_PATH),
                    "index": i,
                    "course_id": item.get("id", "unknown"),
                },
            ) from exc

    return courses


def load_prerequisite_map() -> dict[str, dict[str, list[str]]]:
    """加载先修关系依赖图。

    从 data/prerequisites.json 读取原始 JSON，验证结构后返回。

    Returns:
        dict: 以课程名称为键的先修关系字典，每项包含:
              - required: list[str]  硬性先修课
              - recommended: list[str]  推荐先修课

    Raises:
        FileNotFoundError: 如果 prerequisites.json 不存在
        DataCorruptionError: 如果 JSON 解析或结构验证失败
    """
    raw = _read_json(PREREQUISITES_PATH)

    try:
        prereq_map: dict[str, dict[str, list[str]]] = raw["prerequisite_map"]
    except (KeyError, TypeError) as exc:
        raise DataCorruptionError(
            f"prerequisites.json 缺少 'prerequisite_map' 顶层键: {exc}",
            details={"file": str(PREREQUISITES_PATH)},
        ) from exc

    if not isinstance(prereq_map, dict):
        raise DataCorruptionError(
            "prerequisites.json 中 'prerequisite_map' 必须是对象",
            details={"file": str(PREREQUISITES_PATH)},
        )

    # 验证每个条目的结构
    for course_name, entry in prereq_map.items():
        if not isinstance(entry, dict):
            raise DataCorruptionError(
                f"prerequisites.json 中课程 '{course_name}' 的值必须是对象",
                details={"file": str(PREREQUISITES_PATH), "course": course_name},
            )
        if "required" not in entry or "recommended" not in entry:
            raise DataCorruptionError(
                f"prerequisites.json 中课程 '{course_name}' 缺少 'required' 或 'recommended' 键",
                details={"file": str(PREREQUISITES_PATH), "course": course_name},
            )
        if not isinstance(entry["required"], list):
            raise DataCorruptionError(
                f"prerequisites.json 中课程 '{course_name}' 的 'required' 必须是数组",
                details={"file": str(PREREQUISITES_PATH), "course": course_name},
            )
        if not isinstance(entry["recommended"], list):
            raise DataCorruptionError(
                f"prerequisites.json 中课程 '{course_name}' 的 'recommended' 必须是数组",
                details={"file": str(PREREQUISITES_PATH), "course": course_name},
            )

    return prereq_map


# ── 内部工具函数 ────────────────────────────────────────────

def _read_json(filepath: Path) -> dict[str, Any]:
    """从文件路径读取并解析 JSON。

    Args:
        filepath: JSON 文件的 Path 对象

    Returns:
        dict: 解析后的 JSON 字典

    Raises:
        FileNotFoundError: 文件不存在
        DataCorruptionError: JSON 解析失败
    """
    if not filepath.exists():
        raise FileNotFoundError(
            f"数据文件不存在: {filepath}\n"
            f"请确认文件已放入 data/ 目录"
        )

    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as exc:
        raise DataCorruptionError(
            f"JSON 解析失败: {filepath}\n{exc}",
            details={"file": str(filepath), "line": exc.lineno},
        ) from exc
