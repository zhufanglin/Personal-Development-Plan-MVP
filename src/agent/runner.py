"""
Agent Runner — 顶层入口。

职责: 组件编排（Thin Glue Layer）。
- 组装 Registry / PromptLoader / ReActAgent
- 协调加载 Prompt → 执行 Agent → 格式化输出
- 不包含业务逻辑、不直接调用 Tool、不修改 FSM
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.agent.prompt_loader import PromptLoader
from src.agent.react_loop import ReActResult, RuleBasedReActAgent
from src.agent.tool_registry import ToolRegistry, create_default_registry

# ── Workflow 描述常量 ──────────────────────────────────────

_WORKFLOW_DESCRIPTION: str = (
    "Step 1: get_course_info → 查询课程元数据（名称/学时/难度/先修课/主题模块）\n"
    "Step 2: get_prerequisite → 检查先修条件（递归展开先修树，最大深度5层）\n"
    "Step 3: calculate_learning_time → 评估时间可行性（不可行时提供3种调整方案）\n"
    "Step 4: generate_learning_plan → 生成完整学习计划（学习路径 + 每日计划 + 资源推荐）"
)


# ── 类型定义 ───────────────────────────────────────────────

@dataclass
class AgentRunInput:
    """Agent 运行输入参数。"""

    course_name: str
    daily_hours: float
    duration_days: int
    user_knowledge: list[str] = field(default_factory=list)


@dataclass
class AgentRunOutput:
    """Agent 运行输出。

    统一格式，与 Tool 层返回协议保持一致。
    """

    success: bool
    data: dict | None = None
    error: dict | None = None
    trace: list[dict] = field(default_factory=list)
    prompt: str = ""  # 本次执行的完整 Prompt（调试用）

    def to_dict(self) -> dict:
        """序列化为字典。"""
        result: dict = {"success": self.success, "trace": self.trace}
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error
        return result


# ── AgentRunner ─────────────────────────────────────────────

class AgentRunner:
    """Agent 顶层入口 — 组件编排器。

    职责: 组装 Registry/PromptLoader/ReActAgent，
    协调 Prompt 加载 → Agent 执行 → 结果格式化的完整流程。

    使用方式:
        runner = AgentRunner()
        output = runner.run(AgentRunInput(
            course_name="Python",
            daily_hours=3.0,
            duration_days=12,
        ))
        print(runner.format_result(output))
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        agent: RuleBasedReActAgent | None = None,
        prompt_loader: PromptLoader | None = None,
    ) -> None:
        """初始化 AgentRunner。

        所有参数可选 — 未提供时使用生产默认值。
        支持依赖注入以方便测试。

        Args:
            registry: ToolRegistry 实例（默认: create_default_registry()）
            agent: ReActAgent 实例（默认: RuleBasedReActAgent(registry)）
            prompt_loader: PromptLoader 实例（默认: PromptLoader()）
        """
        self.registry: ToolRegistry = registry or create_default_registry()
        self.agent: RuleBasedReActAgent = agent or RuleBasedReActAgent(self.registry)
        self.prompt_loader: PromptLoader = prompt_loader or PromptLoader()
        self._initialized: bool = True

    # ── 生命周期 ──────────────────────────────────────

    def initialize(self) -> None:
        """(Re)初始化组件。

        用于重置状态或在依赖注入后显式初始化。
        """
        if self.registry is None:
            self.registry = create_default_registry()
        if self.agent is None:
            self.agent = RuleBasedReActAgent(self.registry)
        if self.prompt_loader is None:
            self.prompt_loader = PromptLoader()
        self._initialized = True

    def prepare(
        self,
        course_name: str,
        daily_hours: float,
        duration_days: int,
        user_knowledge: list[str] | None = None,
    ) -> str:
        """准备执行上下文（加载 Prompt + 注入变量）。

        Args:
            course_name: 课程名称
            daily_hours: 每日学习小时数
            duration_days: 学习天数
            user_knowledge: 用户已完成课程列表

        Returns:
            str: 完整的 System Prompt 上下文（含用户输入）
        """
        # 加载 System Prompt（注入 tool_list / workflow / date / output_schema）
        prompt: str = self.prompt_loader.load(
            tool_registry=self.registry,
            workflow=_WORKFLOW_DESCRIPTION,
        )
        # 注入用户输入
        prompt = self.prompt_loader.format_with_input(
            system_prompt=prompt,
            course_name=course_name,
            daily_hours=daily_hours,
            duration_days=duration_days,
            user_knowledge=user_knowledge,
        )
        return prompt

    def run(
        self,
        course_name: str,
        daily_hours: float,
        duration_days: int,
        user_knowledge: list[str] | None = None,
    ) -> AgentRunOutput:
        """执行完整的课程学习规划流程。

        Args:
            course_name: 课程名称
            daily_hours: 每日学习小时数 (0.5 ~ 16)
            duration_days: 计划学习天数 (1 ~ 365)
            user_knowledge: 用户已完成的课程列表（可选）

        Returns:
            AgentRunOutput: 统一格式的运行结果
        """
        # ── 输入验证（阻断非法输入） ──────────────────
        validation_error: AgentRunOutput | None = self._validate_input(
            course_name=course_name,
            daily_hours=daily_hours,
            duration_days=duration_days,
            user_knowledge=user_knowledge,
        )
        if validation_error is not None:
            return validation_error
        # ── 准备上下文 ────────────────────────────────
        prompt: str = self.prepare(
            course_name=course_name,
            daily_hours=daily_hours,
            duration_days=duration_days,
            user_knowledge=user_knowledge,
        )

        # ── 执行 Agent ────────────────────────────────
        result: ReActResult = self.agent.run(
            course_name=course_name,
            daily_hours=daily_hours,
            duration_days=duration_days,
            user_knowledge=user_knowledge,
        )

        # ── 组装输出 ──────────────────────────────────
        return AgentRunOutput(
            success=result.success,
            data=result.data,
            error=result.error,
            trace=result.trace,
            prompt=prompt,
        )

    def format_result(
        self,
        output: AgentRunOutput,
        mode: str = "text",
    ) -> str:
        """格式化最终输出。

        Args:
            output: Agent 运行结果
            mode: 输出模式 — "text" (可读文本) 或 "json" (JSON 字符串)

        Returns:
            str: 格式化后的输出
        """
        if mode == "json":
            import json as _json
            return _json.dumps(output.to_dict(), ensure_ascii=False, indent=2)

        # 文本模式
        lines: list[str] = []
        lines.append("=" * 60)

        if output.success:
            data: dict = output.data or {}
            plan_id: str = data.get("plan_id", "N/A")
            course: str = data.get("course_name", "N/A")
            summary: dict = data.get("summary", {})
            warnings: list = data.get("warnings", [])

            lines.append(f"  学习计划: {course}")
            lines.append(f"  Plan ID: {plan_id}")
            lines.append(f"  模块: {summary.get('total_modules', 0)} 个")
            lines.append(f"  学习日: {summary.get('study_days', 0)} 天")
            lines.append(f"  复习日: {summary.get('review_days', 0)} 天")
            lines.append(f"  评估日: {summary.get('assessment_days', 0)} 天")
            lines.append(f"  总天数: {summary.get('total_days', 0)} 天")
            lines.append(f"  学习资源: {len(data.get('resources', []))} 条")

            if warnings:
                lines.append("")
                lines.append("  ⚠️ 注意事项:")
                for w in warnings:
                    lines.append(f"    - {w}")
        else:
            error: dict = output.error or {}
            code: str = error.get("code", "UNKNOWN")
            message: str = error.get("message", "")
            details: dict = error.get("details", {})

            lines.append(f"  ❌ 错误: {code}")
            lines.append(f"  {message}")

            if code == "PREREQUISITE_CONFLICT":
                missing: list = details.get("missing", [])
                hours: float = details.get("total_prerequisite_hours", 0)
                if missing:
                    lines.append(f"  缺失先修课: {', '.join(missing)}")
                lines.append(f"  总先修学时: {hours:.0f}h")
            elif code == "TIME_INSUFFICIENT":
                opts: list = details.get("adjustment_options", [])
                for opt in opts:
                    lines.append(f"  {opt.get('label', '')}: {opt.get('description', '')}")
            elif code == "COURSE_NOT_FOUND":
                available: list = details.get("available_courses", [])
                if available:
                    lines.append(f"  可用课程: {', '.join(available)}")

        lines.append("=" * 60)
        return "\n".join(lines)

    def shutdown(self) -> None:
        """清理资源（MVP 中为预留接口）。"""
        self._initialized = False

    # ── 输入验证（内部） ──────────────────────────────

    @staticmethod
    def _validate_input(
        course_name: str,
        daily_hours: float,
        duration_days: int,
        user_knowledge: list[str] | None = None,
    ) -> AgentRunOutput | None:
        """集中验证所有输入参数。

        在 Agent 执行前拦截非法输入，避免浪费 Tool 调用。

        Returns:
            AgentRunOutput 如果验证失败（含 VALIDATION_ERROR），None 如果通过
        """
        errors: list[dict] = []

        # course_name
        if not course_name or not isinstance(course_name, str) or not course_name.strip():
            errors.append({
                "field": "course_name",
                "message": "course_name 必须是非空字符串。",
                "received": str(course_name),
            })

        # daily_hours
        if not isinstance(daily_hours, (int, float)):
            errors.append({
                "field": "daily_hours",
                "message": "daily_hours 必须是数字。",
                "received": str(daily_hours),
            })
        elif daily_hours < 0.5 or daily_hours > 16:
            errors.append({
                "field": "daily_hours",
                "message": f"daily_hours 必须在 0.5 ~ 16 之间，收到 {daily_hours}。",
                "constraint": "0.5 <= daily_hours <= 16",
            })

        # duration_days
        if not isinstance(duration_days, int):
            errors.append({
                "field": "duration_days",
                "message": "duration_days 必须是整数。",
                "received": str(duration_days),
            })
        elif duration_days < 1 or duration_days > 365:
            errors.append({
                "field": "duration_days",
                "message": f"duration_days 必须在 1 ~ 365 之间，收到 {duration_days}。",
                "constraint": "1 <= duration_days <= 365",
            })

        # user_knowledge (optional)
        if user_knowledge is not None:
            if not isinstance(user_knowledge, list):
                errors.append({
                    "field": "user_knowledge",
                    "message": "user_knowledge 必须是字符串列表。",
                    "received": str(type(user_knowledge)),
                })
            else:
                for i, item in enumerate(user_knowledge):
                    if not isinstance(item, str) or not item.strip():
                        errors.append({
                            "field": f"user_knowledge[{i}]",
                            "message": "user_knowledge 中的每个元素必须是非空字符串。",
                            "received": str(item),
                        })

        if errors:
            return AgentRunOutput(
                success=False,
                error={
                    "code": "VALIDATION_ERROR",
                    "message": f"输入验证失败: {len(errors)} 项错误。",
                    "details": {"errors": errors},
                    "tool_name": "agent_runner",
                },
                trace=[{
                    "step": 0,
                    "state": "VALIDATION",
                    "thought": None,
                    "selected_tool": None,
                    "tool_input": None,
                    "tool_output": None,
                    "timestamp": _now_iso(),
                    "elapsed_ms": 0,
                }],
            )

        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
