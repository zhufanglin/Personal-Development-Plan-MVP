"""
Tool Registry — 基于 Registry Pattern 的 Tool 注册与调度中心。

职责：
- 注册/注销 Tool（元数据 + 可调用函数）
- 按名称查找 Tool
- 列出所有已注册 Tool
- 统一调度执行（invoke）

不参与 Agent 决策、Workflow 或推理。
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from src.exceptions import ValidationError as AppValidationError


# ── ToolEntry ──────────────────────────────────────────────

@dataclass
class ToolEntry:
    """单个 Tool 的注册信息。

    包含元数据和可调用函数引用。
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    function: Callable[..., dict]


# ── ToolRegistry ───────────────────────────────────────────

class ToolRegistry:
    """Tool 注册中心。

    使用 dict 存储，O(1) 查找。无 if/elif 分支。

    使用方式:
        registry = ToolRegistry()
        registry.register(ToolEntry(
            name="get_course_info",
            description="查询课程元数据",
            input_schema={"type": "object", "properties": {...}},
            output_schema={"type": "object", "properties": {...}},
            function=get_course_info,
        ))
        result = registry.invoke("get_course_info", course_name="Python")
    """

    def __init__(self) -> None:
        """初始化空的 Tool 注册表。"""
        self._tools: dict[str, ToolEntry] = {}

    # ── 注册/注销 ──────────────────────────────────────

    def register(self, entry: ToolEntry) -> None:
        """注册一个 Tool。

        如果同名 Tool 已存在，覆盖旧注册（幂等）。

        Args:
            entry: ToolEntry 实例

        Raises:
            AppValidationError: 如果 entry.name 为空
        """
        if not entry.name or not isinstance(entry.name, str):
            raise AppValidationError(
                "Tool 名称必须是非空字符串。",
                details={"received": str(entry.name)},
            )
        self._tools[entry.name] = entry

    def unregister(self, name: str) -> bool:
        """注销一个 Tool。

        Args:
            name: Tool 名称

        Returns:
            True 如果成功注销，False 如果 Tool 不存在
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    # ── 查询 ──────────────────────────────────────────

    def get_tool(self, name: str) -> ToolEntry | None:
        """按名称获取 Tool 注册信息。

        Args:
            name: Tool 名称

        Returns:
            ToolEntry 如果找到，否则 None
        """
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """列出所有已注册 Tool 的元数据（不含函数引用）。

        Returns:
            list[dict]: 每个 Tool 的 {name, description, input_schema, output_schema}
        """
        return [
            {
                "name": e.name,
                "description": e.description,
                "input_schema": e.input_schema,
                "output_schema": e.output_schema,
            }
            for e in self._tools.values()
        ]

    # ── 调度执行 ──────────────────────────────────────

    def invoke(self, name: str, **kwargs: Any) -> dict:
        """按名称执行 Tool。

        使用 dict 直接查找，无 if/elif 分支。

        Args:
            name: Tool 名称
            **kwargs: 传递给 Tool 函数的参数

        Returns:
            Tool 函数的返回值（统一为 dict）

        Raises:
            AppValidationError: 如果 Tool 不存在
        """
        entry = self._tools.get(name)
        if entry is None:
            available = list(self._tools.keys())
            return {
                "success": False,
                "error": {
                    "code": "TOOL_NOT_FOUND",
                    "message": f"未知 Tool: '{name}'。可用 Tool: {', '.join(available)}",
                    "details": {"tool_name": name, "available": available},
                    "tool_name": "tool_registry",
                },
            }

        try:
            return entry.function(**kwargs)
        except Exception as exc:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Tool '{name}' 执行异常: {exc}",
                    "details": {"tool_name": name, "exception": str(exc)},
                    "tool_name": "tool_registry",
                },
            }

    # ── 批量注册 ──────────────────────────────────────

    def register_all(self, entries: list[ToolEntry]) -> None:
        """批量注册 Tool。

        Args:
            entries: ToolEntry 列表
        """
        for entry in entries:
            self.register(entry)

    # ── 查询辅助 ──────────────────────────────────────

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ── 默认 Registry 构建 ─────────────────────────────────────

def create_default_registry() -> ToolRegistry:
    """创建包含全部 4 个 Tool 的默认 Registry。

    Returns:
        ToolRegistry: 已注册 get_course_info, get_prerequisite,
                      calculate_learning_time, generate_learning_plan
    """
    from src.tools.course_info import get_course_info
    from src.tools.feasibility import calculate_learning_time
    from src.tools.learning_plan import generate_learning_plan
    from src.tools.prerequisites import get_prerequisite

    registry = ToolRegistry()
    registry.register_all([
        ToolEntry(
            name="get_course_info",
            description="查询课程目录，返回课程元数据（名称、学时、难度、先修课、主题模块）",
            input_schema={
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "课程名称，大小写不敏感",
                        "minLength": 1,
                        "maxLength": 100,
                    },
                },
                "required": ["course_name"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "hours": {"type": "number"},
                            "difficulty": {"type": "string"},
                            "prerequisite": {"type": "array"},
                            "description": {"type": "string"},
                            "category": {"type": "string"},
                            "topics": {"type": "array"},
                        },
                    },
                },
            },
            function=get_course_info,
        ),
        ToolEntry(
            name="get_prerequisite",
            description="递归展开先修树，检查用户是否满足先修条件",
            input_schema={
                "type": "object",
                "properties": {
                    "course_name": {
                        "type": "string",
                        "description": "目标课程名称",
                        "minLength": 1,
                    },
                    "user_knowledge": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "用户已完成的课程列表",
                    },
                },
                "required": ["course_name", "user_knowledge"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "satisfied": {"type": "boolean"},
                            "course_name": {"type": "string"},
                            "required_prerequisites": {"type": "array"},
                            "recommended_prerequisites": {"type": "array"},
                            "missing": {"type": "array"},
                            "completed": {"type": "array"},
                            "total_prerequisite_hours": {"type": "number"},
                            "recommendation": {"type": "string"},
                        },
                    },
                },
            },
            function=get_prerequisite,
        ),
        ToolEntry(
            name="calculate_learning_time",
            description="评估学习目标的时间可行性，不可行时提供三种调整方案",
            input_schema={
                "type": "object",
                "properties": {
                    "course_name": {"type": "string", "minLength": 1},
                    "daily_hours": {"type": "number", "minimum": 0.5, "maximum": 16},
                    "duration_days": {"type": "integer", "minimum": 1, "maximum": 365},
                },
                "required": ["course_name", "daily_hours", "duration_days"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "feasible": {"type": "boolean"},
                            "course_total_hours": {"type": "number"},
                            "available_hours": {"type": "number"},
                            "buffer_hours": {"type": "number"},
                            "buffer_ratio": {"type": "number"},
                            "adjustment_options": {"type": "array"},
                            "recommendation": {"type": "string"},
                        },
                    },
                },
            },
            function=calculate_learning_time,
        ),
        ToolEntry(
            name="generate_learning_plan",
            description="编排完整学习计划：学习路径 + 每日计划 + 资源推荐",
            input_schema={
                "type": "object",
                "properties": {
                    "course_name": {"type": "string", "minLength": 1},
                    "daily_hours": {"type": "number", "minimum": 0.5, "maximum": 16},
                    "duration_days": {"type": "integer", "minimum": 1, "maximum": 365},
                    "skip_optional": {"type": "boolean", "default": False},
                    "start_date": {"type": "string", "format": "date"},
                    "user_knowledge": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["course_name", "daily_hours", "duration_days"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "plan_id": {"type": "string"},
                            "course_name": {"type": "string"},
                            "generated_at": {"type": "string"},
                            "parameters": {"type": "object"},
                            "summary": {"type": "object"},
                            "learning_path": {"type": "array"},
                            "daily_schedule": {"type": "array"},
                            "resources": {"type": "array"},
                            "warnings": {"type": "array"},
                            "trace": {"type": "array"},
                        },
                    },
                },
            },
            function=generate_learning_plan,
        ),
    ])
    return registry
