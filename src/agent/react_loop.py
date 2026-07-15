"""
ReAct 状态机控制器。

职责: 按预定义执行计划（EXECUTION_PLAN）依次调用 Tool，
在每个 Tool 调用后检查阻断条件，最终返回 ReActResult。

MVP: 规则化 FSM，不依赖 LLM。
LLM 替换: 子类化并覆写 _reason() / _select_tool() / _build_params() / _check_blocker()。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from src.agent.tool_registry import ToolRegistry


# ═══════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class ReActState:
    """Agent 执行过程中累积的上下文。

    每个 Tool 返回的 data 被合并到此结构中，
    供后续 ToolStep 的 params_builder 使用。
    """

    course_name: str
    daily_hours: float
    duration_days: int
    user_knowledge: list[str] = field(default_factory=list)

    # 累積的 Tool 返回数据
    course_data: dict | None = None
    prereq_result: dict | None = None
    feasibility_result: dict | None = None
    plan_data: dict | None = None

    def update(self, data: dict) -> None:
        """根据 Tool 返回数据更新上下文。

        通过检查 data 中的特征字段来判断来源 Tool。
        """
        if "satisfied" in data:
            self.prereq_result = data
        elif "feasible" in data:
            self.feasibility_result = data
        elif "plan_id" in data:
            self.plan_data = data
        else:
            # course_info: 包含 topics/hours/difficulty
            self.course_data = data


@dataclass
class TraceEntry:
    """单条 ReAct Trace 记录。"""

    step: int
    state: str  # THINKING / TOOL_EXECUTION / OBSERVATION / RESPONSE / ERROR
    thought: str | None = None
    selected_tool: str | None = None
    tool_input: dict | None = None
    tool_output: dict | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    elapsed_ms: int = 0

    def to_dict(self) -> dict:
        """序列化为字典（供 JSON 输出）。"""
        return {
            "step": self.step,
            "state": self.state,
            "thought": self.thought,
            "selected_tool": self.selected_tool,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "timestamp": self.timestamp,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class ReActResult:
    """Agent 最终输出。"""

    success: bool
    data: dict | None = None
    error: dict | None = None
    trace: list[dict] = field(default_factory=list)


@dataclass
class ToolStep:
    """执行计划中的单个步骤定义。"""

    tool_name: str
    thought_template: str
    params_builder: Callable[["ReActState"], dict]
    blocker_check: Callable[[dict], str | None] | None = None

    def format_thought(self, state: "ReActState") -> str:
        """将 thought_template 中的 {field} 替换为 state 中的实际值。"""
        try:
            return self.thought_template.format(
                course_name=state.course_name,
                daily_hours=state.daily_hours,
                duration_days=state.duration_days,
            )
        except (KeyError, ValueError):
            return self.thought_template


# ═══════════════════════════════════════════════════════════
# 执行计划定义
# ═══════════════════════════════════════════════════════════

def _build_get_course_info_params(state: ReActState) -> dict:
    return {"course_name": state.course_name}


def _build_get_prerequisite_params(state: ReActState) -> dict:
    return {
        "course_name": state.course_name,
        "user_knowledge": state.user_knowledge,
    }


def _build_calculate_learning_time_params(state: ReActState) -> dict:
    return {
        "course_name": state.course_name,
        "daily_hours": state.daily_hours,
        "duration_days": state.duration_days,
    }


def _build_generate_learning_plan_params(state: ReActState) -> dict:
    return {
        "course_name": state.course_name,
        "daily_hours": state.daily_hours,
        "duration_days": state.duration_days,
        "user_knowledge": state.user_knowledge,
    }


def _check_prereq_blocker(result: dict) -> str | None:
    """检查先修冲突阻断。"""
    data = result.get("data", {})
    if isinstance(data, dict) and data.get("satisfied") is False:
        return "PREREQ_CONFLICT"
    return None


def _check_feasibility_blocker(result: dict) -> str | None:
    """检查时间不足阻断。"""
    data = result.get("data", {})
    if isinstance(data, dict) and data.get("feasible") is False:
        return "TIME_INSUFFICIENT"
    return None


EXECUTION_PLAN: list[ToolStep] = [
    ToolStep(
        tool_name="get_course_info",
        thought_template="查询'{course_name}'课程信息，获取学时和先修要求。",
        params_builder=_build_get_course_info_params,
        blocker_check=None,  # 课程不存在时 success=false，直接传播 error
    ),
    ToolStep(
        tool_name="get_prerequisite",
        thought_template="检查用户是否满足'{course_name}'的先修条件。",
        params_builder=_build_get_prerequisite_params,
        blocker_check=_check_prereq_blocker,
    ),
    ToolStep(
        tool_name="calculate_learning_time",
        thought_template="评估时间可行性: {daily_hours}h/天 × {duration_days}天。",
        params_builder=_build_calculate_learning_time_params,
        blocker_check=_check_feasibility_blocker,
    ),
    ToolStep(
        tool_name="generate_learning_plan",
        thought_template="所有条件满足，生成完整学习计划。",
        params_builder=_build_generate_learning_plan_params,
        blocker_check=None,  # 最后一步
    ),
]


# ═══════════════════════════════════════════════════════════
# ReAct Agent (MVP: Rule-based FSM)
# ═══════════════════════════════════════════════════════════

class RuleBasedReActAgent:
    """MVP: 规则化 ReAct 状态机。

    按 EXECUTION_PLAN 预定义序列依次执行 Tool，
    每步记录 Trace，检测阻断条件。

    LLM 替换路径: 子类化并覆写:
        - _reason() → LLM 动态推理
        - _select_tool() → LLM 动态选择 Tool
        - _build_params() → 从 LLM function_call 提取参数
        - _check_blocker() → LLM 自行判断 Tool 返回
    """

    def __init__(self, registry: ToolRegistry) -> None:
        """初始化 Agent。

        Args:
            registry: ToolRegistry 实例，用于 Tool 调度
        """
        self.registry: ToolRegistry = registry
        self._plan: list[ToolStep] = list(EXECUTION_PLAN)

    def run(
        self,
        course_name: str,
        daily_hours: float,
        duration_days: int,
        user_knowledge: list[str] | None = None,
    ) -> ReActResult:
        """执行完整的 ReAct 循环。

        Args:
            course_name: 课程名称
            daily_hours: 每日学习小时数
            duration_days: 学习天数
            user_knowledge: 用户已完成的课程列表

        Returns:
            ReActResult(success, data/error, trace)
        """
        # ── 初始化 ────────────────────────────────────
        state = ReActState(
            course_name=course_name.strip(),
            daily_hours=daily_hours,
            duration_days=duration_days,
            user_knowledge=list(user_knowledge or []),
        )
        trace: list[TraceEntry] = []
        step_counter: int = 0

        # ── 遍历执行计划 ──────────────────────────────
        for step_def in self._plan:
            # ── THINKING ──────────────────────────────
            thought: str = step_def.format_thought(state)
            step_counter += 1
            trace.append(TraceEntry(
                step=step_counter,
                state="THINKING",
                thought=thought,
            ))

            # ── TOOL_SELECTION + TOOL_EXECUTION ───────
            params: dict = step_def.params_builder(state)

            step_counter += 1
            trace.append(TraceEntry(
                step=step_counter,
                state="TOOL_EXECUTION",
                selected_tool=step_def.tool_name,
                tool_input=params,
            ))

            import time
            t0 = time.perf_counter()
            result: dict = self.registry.invoke(step_def.tool_name, **params)
            elapsed: int = round((time.perf_counter() - t0) * 1000)

            # ── 更新 trace 耗时 ───────────────────────
            trace[-1].elapsed_ms = elapsed

            # ── OBSERVATION ───────────────────────────
            step_counter += 1
            output_summary: dict = _summarize_output(result)
            trace.append(TraceEntry(
                step=step_counter,
                state="OBSERVATION",
                tool_output=output_summary,
            ))

            # ── 检查 Tool 错误 ────────────────────────
            if not result.get("success"):
                return self._build_error_response(result, trace, tool_name=step_def.tool_name)

            # ── 检查业务阻断 ──────────────────────────
            blocker: str | None = None
            if step_def.blocker_check is not None:
                blocker = step_def.blocker_check(result)

            if blocker == "PREREQ_CONFLICT":
                return self._build_prereq_error(result, trace)
            if blocker == "TIME_INSUFFICIENT":
                return self._build_time_error(result, trace)

            # ── 更新上下文 ────────────────────────────
            data: dict = result.get("data", {})
            if isinstance(data, dict):
                state.update(data)

        # ═══ 所有步骤完成，无阻断 ═══════════════════════

        # ── RESPONSE ──────────────────────────────────
        step_counter += 1
        trace.append(TraceEntry(
            step=step_counter,
            state="RESPONSE",
        ))

        return ReActResult(
            success=True,
            data=state.plan_data if state.plan_data else {},
            trace=[t.to_dict() for t in trace],
        )

    # ── 内部方法: 错误响应构建 ──────────────────────

    def _build_error_response(
        self,
        result: dict,
        trace: list[TraceEntry],
        tool_name: str = "",
    ) -> ReActResult:
        """构建 Tool 层面的错误响应（success=false）。

        Args:
            result: Tool 返回的原始 dict
            trace: 累积的 Trace 列表
            tool_name: 出错时的 Tool 名称（用于错误上下文）
        """
        error_info: dict = result.get("error", {})
        step_counter: int = trace[-1].step + 1 if trace else 1

        # 增强错误上下文
        enhanced_error: dict = dict(error_info)  # 浅拷贝，避免修改原始
        enhanced_error.setdefault("details", {})
        if tool_name:
            enhanced_error["details"]["failed_tool"] = tool_name
            enhanced_error["details"]["failed_at_step"] = trace[-1].step if trace else 0

        trace.append(TraceEntry(
            step=step_counter,
            state="ERROR" if error_info.get("code") in ("INTERNAL_ERROR", "DATA_CORRUPTION") else "RESPONSE",
            thought=f"Tool 返回错误: {error_info.get('code', 'UNKNOWN')} — {error_info.get('message', '')[:80]}",
        ))

        return ReActResult(
            success=False,
            error=enhanced_error,
            trace=[t.to_dict() for t in trace],
        )

    def _build_prereq_error(
        self,
        result: dict,
        trace: list[TraceEntry],
    ) -> ReActResult:
        """构建先修冲突错误响应。"""
        data: dict = result.get("data", {})
        step_counter: int = trace[-1].step + 1 if trace else 1

        trace.append(TraceEntry(
            step=step_counter,
            state="RESPONSE",
            thought="先修条件不满足 → 终止。",
        ))

        return ReActResult(
            success=False,
            error={
                "code": "PREREQUISITE_CONFLICT",
                "message": (
                    f"先修条件不满足: 缺少 {len(data.get('missing', []))} 门先修课。"
                    f"总先修学时: {data.get('total_prerequisite_hours', 0):.0f}h。"
                ),
                "details": {
                    "course_name": data.get("course_name"),
                    "missing": data.get("missing", []),
                    "completed": data.get("completed", []),
                    "total_prerequisite_hours": data.get("total_prerequisite_hours", 0),
                    "recommendation": data.get("recommendation", ""),
                },
                "tool_name": "react_agent",
            },
            trace=[t.to_dict() for t in trace],
        )

    def _build_time_error(
        self,
        result: dict,
        trace: list[TraceEntry],
    ) -> ReActResult:
        """构建时间不足错误响应。"""
        data: dict = result.get("data", {})
        step_counter: int = trace[-1].step + 1 if trace else 1

        trace.append(TraceEntry(
            step=step_counter,
            state="RESPONSE",
            thought="学习时间不足 → 终止。输出3种调整方案。",
        ))

        return ReActResult(
            success=False,
            error={
                "code": "TIME_INSUFFICIENT",
                "message": (
                    f"学习时间不足: 需要 {data.get('course_total_hours', 0):.0f}h，"
                    f"可用 {data.get('available_hours', 0):.0f}h。"
                    f"缺口 {abs(data.get('buffer_hours', 0)):.0f}h。"
                ),
                "details": {
                    "course_total_hours": data.get("course_total_hours"),
                    "available_hours": data.get("available_hours"),
                    "deficit_hours": abs(data.get("buffer_hours", 0)),
                    "adjustment_options": data.get("adjustment_options", []),
                },
                "tool_name": "react_agent",
            },
            trace=[t.to_dict() for t in trace],
        )


# ═══════════════════════════════════════════════════════════
# 内部工具函数
# ═══════════════════════════════════════════════════════════

def _summarize_output(result: dict) -> dict:
    """生成 Tool 输出的摘要（避免 trace 中存储完整超大对象）。

    Args:
        result: Tool 的原始返回 dict

    Returns:
        dict: 摘要信息，保留关键决策字段
    """
    summary: dict = {"success": result.get("success", False)}

    if result.get("success"):
        data: dict = result.get("data", {})
        if isinstance(data, dict):
            summary["data_keys"] = list(data.keys())
            # 提取关键决策字段（每个 Tool 的核心输出）
            _extract_keys(data, summary, [
                "name", "course_name", "hours", "difficulty",
                "satisfied", "feasible", "plan_id",
                "total_prerequisite_hours", "total_modules",
                "total_days", "buffer_hours", "buffer_ratio",
                "missing_count", "required_count", "optional_count",
                "study_days", "review_days", "assessment_days",
                "total_learning_hours",
            ])
            # 特殊处理: missing 列表只显示数量，不显示完整列表
            if "missing" in data:
                summary["missing_count"] = len(data["missing"])
            if "required_prerequisites" in data:
                summary["required_count"] = len(data["required_prerequisites"])
            if "modules" in data:
                summary["total_modules"] = len(data.get("modules", []))
            if "resources" in data:
                summary["resource_count"] = len(data["resources"])
    else:
        error: dict = result.get("error", {})
        if isinstance(error, dict):
            summary["error_code"] = error.get("code", "UNKNOWN")
            summary["error_message"] = error.get("message", "")[:100]

    return summary


def _extract_keys(source: dict, target: dict, keys: list[str]) -> None:
    """从 source 提取指定 key 到 target（仅在 key 存在时）。"""
    for key in keys:
        if key in source:
            target[key] = source[key]
