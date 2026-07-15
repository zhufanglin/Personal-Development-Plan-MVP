"""
Agent 集成测试。

验证完整 Agent Runtime 链路:
- AgentRunner 生命周期
- End-to-End 成功/先修冲突/时间不足流程
- 依赖注入 (MockRegistry / MockAgent)
- Trace 验证
- Prompt 集成
"""

from unittest.mock import MagicMock

import pytest

from src.agent.prompt_loader import PromptLoader
from src.agent.react_loop import ReActResult
from src.agent.runner import AgentRunOutput, AgentRunner
from src.agent.tool_registry import ToolEntry, ToolRegistry


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def runner() -> AgentRunner:
    """返回默认的 AgentRunner（含真实 Registry + Agent）。"""
    return AgentRunner()


# ═══════════════════════════════════════════════════════════
# 1. AgentRunner 生命周期测试
# ═══════════════════════════════════════════════════════════

class TestAgentRunnerLifecycle:
    """AgentRunner 生命周期测试。"""

    def test_initialize(self) -> None:
        """initialize() 应正确设置所有组件。"""
        runner = AgentRunner()
        runner.initialize()
        assert runner._initialized is True
        assert runner.registry is not None
        assert runner.agent is not None
        assert runner.prompt_loader is not None

    def test_prepare_returns_prompt(self, runner: AgentRunner) -> None:
        """prepare() 应返回包含所有变量的完整 Prompt。"""
        prompt = runner.prepare("Python", 3, 12)
        assert isinstance(prompt, str)
        assert len(prompt) > 500
        # 验证变量注入
        assert "get_course_info" in prompt
        assert "Python" in prompt
        assert "2026" in prompt
        # 验证不含未替换的占位符
        assert "{{tool_list}}" not in prompt
        assert "{{workflow}}" not in prompt
        assert "{{current_date}}" not in prompt

    def test_run_returns_output(self, runner: AgentRunner) -> None:
        """run() 应返回 AgentRunOutput。"""
        out = runner.run("Python", 3, 12)
        assert isinstance(out, AgentRunOutput)
        assert isinstance(out.success, bool)

    def test_format_result_text(self, runner: AgentRunner) -> None:
        """format_result(mode='text') 应返回可读文本。"""
        out = runner.run("Python", 3, 12)
        text = runner.format_result(out, mode="text")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_format_result_json(self, runner: AgentRunner) -> None:
        """format_result(mode='json') 应返回合法 JSON。"""
        import json
        out = runner.run("Python", 3, 12)
        text = runner.format_result(out, mode="json")
        data = json.loads(text)
        assert data["success"] == out.success

    def test_shutdown(self, runner: AgentRunner) -> None:
        """shutdown() 应将 _initialized 设为 False。"""
        runner.shutdown()
        assert runner._initialized is False


# ═══════════════════════════════════════════════════════════
# 2. End-to-End 成功流程
# ═══════════════════════════════════════════════════════════

class TestEndToEndSuccess:
    """完整成功流程测试。"""

    @pytest.fixture
    def result(self) -> AgentRunOutput:
        runner = AgentRunner()
        return runner.run("Python", 3, 12)

    def test_success_flag(self, result: AgentRunOutput) -> None:
        """结果应标记为成功。"""
        assert result.success is True

    def test_data_exists(self, result: AgentRunOutput) -> None:
        """data 应包含所有关键字段。"""
        assert result.data is not None
        assert "plan_id" in result.data
        assert "course_name" in result.data
        assert result.data["course_name"] == "Python"

    def test_learning_path_exists(self, result: AgentRunOutput) -> None:
        """learning_path 应非空。"""
        assert len(result.data["learning_path"]) >= 1

    def test_daily_schedule_exists(self, result: AgentRunOutput) -> None:
        """daily_schedule 应非空。"""
        assert len(result.data["daily_schedule"]) >= 1

    def test_resources_exist(self, result: AgentRunOutput) -> None:
        """resources 应非空。"""
        assert len(result.data["resources"]) >= 1

    def test_trace_non_empty(self, result: AgentRunOutput) -> None:
        """trace 应非空。"""
        assert len(result.trace) >= 1

    def test_summary_aggregates(self, result: AgentRunOutput) -> None:
        """summary 应有正确的聚合数据。"""
        s = result.data["summary"]
        assert s["total_modules"] >= 1
        assert s["total_days"] >= 1
        assert s["total_learning_hours"] >= 1


# ═══════════════════════════════════════════════════════════
# 3. 先修冲突流程
# ═══════════════════════════════════════════════════════════

class TestPrerequisiteConflict:
    """先修冲突流程测试。"""

    @pytest.fixture
    def result(self) -> AgentRunOutput:
        runner = AgentRunner()
        return runner.run("Spark", 2, 30)

    def test_success_false(self, result: AgentRunOutput) -> None:
        """结果应标记为失败。"""
        assert result.success is False

    def test_error_code(self, result: AgentRunOutput) -> None:
        """错误码应为 PREREQUISITE_CONFLICT。"""
        assert result.error["code"] == "PREREQUISITE_CONFLICT"

    def test_missing_listed(self, result: AgentRunOutput) -> None:
        """details 应包含 missing 列表。"""
        missing = result.error["details"]["missing"]
        assert "Python" in missing
        assert "Hadoop" in missing

    def test_trace_stops_at_prereq(self, result: AgentRunOutput) -> None:
        """trace 应在 get_prerequisite 处停止，不继续后续 Tool。"""
        tool_names = [
            t["selected_tool"]
            for t in result.trace
            if t["selected_tool"] is not None
        ]
        assert "get_course_info" in tool_names
        assert "get_prerequisite" in tool_names
        # 后续 Tool 不应被调用
        assert "calculate_learning_time" not in tool_names
        assert "generate_learning_plan" not in tool_names

    def test_trace_has_response_state(self, result: AgentRunOutput) -> None:
        """trace 最后一条应为 RESPONSE 状态。"""
        assert result.trace[-1]["state"] == "RESPONSE"


# ═══════════════════════════════════════════════════════════
# 4. 时间不足流程
# ═══════════════════════════════════════════════════════════

class TestTimeInsufficient:
    """时间不足流程测试。"""

    @pytest.fixture
    def result(self) -> AgentRunOutput:
        runner = AgentRunner()
        return runner.run(
            "Flink", 1, 10,
            user_knowledge=["Python", "Linux", "Java", "Spark"],
        )

    def test_success_false(self, result: AgentRunOutput) -> None:
        """结果应标记为失败。"""
        assert result.success is False

    def test_error_code(self, result: AgentRunOutput) -> None:
        """错误码应为 TIME_INSUFFICIENT。"""
        assert result.error["code"] == "TIME_INSUFFICIENT"

    def test_calculate_learning_time_executed(self, result: AgentRunOutput) -> None:
        """calculate_learning_time 应被执行。"""
        tool_names = [
            t["selected_tool"]
            for t in result.trace
            if t["selected_tool"] is not None
        ]
        assert "calculate_learning_time" in tool_names

    def test_adjustment_options_exist(self, result: AgentRunOutput) -> None:
        """details 应包含 adjustment_options。"""
        opts = result.error["details"]["adjustment_options"]
        assert len(opts) == 3

    def test_three_strategies(self, result: AgentRunOutput) -> None:
        """应包含三种策略。"""
        opts = result.error["details"]["adjustment_options"]
        strategies = {o["strategy"] for o in opts}
        assert "extend_duration" in strategies
        assert "increase_hours" in strategies
        assert "reduce_scope" in strategies

    def test_generate_plan_not_executed(self, result: AgentRunOutput) -> None:
        """generate_learning_plan 不应被执行。"""
        tool_names = [
            t["selected_tool"]
            for t in result.trace
            if t["selected_tool"] is not None
        ]
        assert "generate_learning_plan" not in tool_names


# ═══════════════════════════════════════════════════════════
# 5. Tool Registry 注入测试
# ═══════════════════════════════════════════════════════════

class TestRegistryInjection:
    """ToolRegistry 依赖注入测试。"""

    def test_mock_registry_injection(self) -> None:
        """注入 MockRegistry 后 AgentRunner 应正常运作。"""
        mock_registry = ToolRegistry()

        # 注册最小 Tool 集合
        mock_registry.register(ToolEntry(
            name="get_course_info",
            description="Mock",
            input_schema={},
            output_schema={},
            function=lambda **kw: {
                "success": True,
                "data": {
                    "id": "COURSE-TEST-001",
                    "name": "Python",
                    "hours": 24,
                    "difficulty": "beginner",
                    "prerequisite": [],
                    "description": "Test",
                    "category": "test",
                    "topics": [{"name": "T1", "hours": 24, "order": 1, "required": True, "description": ""}],
                },
            },
        ))
        mock_registry.register(ToolEntry(
            name="get_prerequisite",
            description="Mock",
            input_schema={},
            output_schema={},
            function=lambda **kw: {
                "success": True,
                "data": {
                    "satisfied": True, "course_name": "Python",
                    "required_prerequisites": [], "recommended_prerequisites": [],
                    "missing": [], "completed": [],
                    "total_prerequisite_hours": 0,
                    "recommendation": "OK",
                },
            },
        ))
        mock_registry.register(ToolEntry(
            name="calculate_learning_time",
            description="Mock",
            input_schema={},
            output_schema={},
            function=lambda **kw: {
                "success": True,
                "data": {
                    "feasible": True, "course_name": "Python",
                    "course_total_hours": 24, "daily_hours": 3,
                    "duration_days": 12, "available_hours": 36,
                    "buffer_hours": 12, "buffer_ratio": 0.5,
                    "recommended_buffer": 4.8, "buffer_sufficient": True,
                    "minimum_days_needed": 8, "minimum_hours_per_day": 2.0,
                    "adjustment_options": [], "recommendation": "可行",
                },
            },
        ))
        mock_registry.register(ToolEntry(
            name="generate_learning_plan",
            description="Mock",
            input_schema={},
            output_schema={},
            function=lambda **kw: {
                "success": True,
                "data": {
                    "plan_id": "mock-plan-001",
                    "course_name": "Python",
                    "generated_at": "2026-07-11T00:00:00Z",
                    "parameters": {},
                    "summary": {"total_modules": 1, "total_days": 1, "total_learning_hours": 24,
                                 "required_modules": 1, "optional_modules": 0, "skipped_modules": 0,
                                 "study_days": 1, "review_days": 0, "assessment_days": 0},
                    "learning_path": [{"name": "T1", "hours": 24, "order": 1, "required": True, "estimated_days": 8}],
                    "daily_schedule": [{"day": 1, "type": "study", "topics": ["T1"], "hours": 24}],
                    "resources": [],
                    "warnings": [],
                    "trace": [],
                },
            },
        ))

        runner = AgentRunner(registry=mock_registry)
        out = runner.run("Python", 3, 12)
        assert out.success is True
        assert out.data["plan_id"] == "mock-plan-001"


# ═══════════════════════════════════════════════════════════
# 6. Mock Agent 测试
# ═══════════════════════════════════════════════════════════

class TestMockAgent:
    """Mock Agent 注入测试。"""

    def test_mock_agent_injection(self) -> None:
        """注入 MockAgent 后 Runner 应正确封装输出。"""
        class MockAgent:
            def run(self, **kw: object) -> ReActResult:
                return ReActResult(
                    success=True,
                    data={"plan_id": "mock-123", "course_name": "Test"},
                    trace=[{"step": 1, "state": "THINKING", "thought": "mock"}],
                )

        runner = AgentRunner(agent=MockAgent())  # type: ignore[arg-type]
        out = runner.run("Test", 1, 1)
        assert out.success is True
        assert out.data is not None
        assert out.data["plan_id"] == "mock-123"
        assert len(out.trace) == 1

    def test_mock_agent_returns_error(self) -> None:
        """MockAgent 返回错误时 Runner 应正确传递。"""
        class MockErrorAgent:
            def run(self, **kw: object) -> ReActResult:
                return ReActResult(
                    success=False,
                    error={"code": "TEST_ERROR", "message": "Mock error"},
                    trace=[],
                )

        runner = AgentRunner(agent=MockErrorAgent())  # type: ignore[arg-type]
        out = runner.run("Test", 1, 1)
        assert out.success is False
        assert out.error["code"] == "TEST_ERROR"


# ═══════════════════════════════════════════════════════════
# 7. Trace 验证
# ═══════════════════════════════════════════════════════════

class TestTrace:
    """Trace 结构验证测试。"""

    @pytest.fixture
    def trace(self) -> list[dict]:
        runner = AgentRunner()
        out = runner.run("Python", 3, 12)
        assert out.success
        return out.trace

    def test_tool_execution_order(self, trace: list[dict]) -> None:
        """Tool 执行顺序应为固定 4 步。"""
        tool_names = [
            t["selected_tool"]
            for t in trace
            if t["selected_tool"] is not None
        ]
        assert tool_names == [
            "get_course_info",
            "get_prerequisite",
            "calculate_learning_time",
            "generate_learning_plan",
        ]

    def test_each_entry_has_step(self, trace: list[dict]) -> None:
        """每条 Trace 应有 step 字段。"""
        for t in trace:
            assert "step" in t
            assert isinstance(t["step"], int)

    def test_each_entry_has_state(self, trace: list[dict]) -> None:
        """每条 Trace 应有 state 字段。"""
        valid_states = {"THINKING", "TOOL_EXECUTION", "OBSERVATION", "RESPONSE"}
        for t in trace:
            assert t["state"] in valid_states, f"Unexpected state: {t['state']}"

    def test_think_entries_have_thought(self, trace: list[dict]) -> None:
        """THINKING 状态应有 thought 字段。"""
        thinking_entries = [t for t in trace if t["state"] == "THINKING"]
        assert len(thinking_entries) >= 1
        for t in thinking_entries:
            assert t["thought"] is not None

    def test_execution_entries_have_tool_input(self, trace: list[dict]) -> None:
        """TOOL_EXECUTION 状态应有 selected_tool + tool_input。"""
        exec_entries = [t for t in trace if t["state"] == "TOOL_EXECUTION"]
        assert len(exec_entries) == 4
        for t in exec_entries:
            assert t["selected_tool"] is not None
            assert t["tool_input"] is not None

    def test_observation_entries_have_tool_output(self, trace: list[dict]) -> None:
        """OBSERVATION 状态应有 tool_output。"""
        obs_entries = [t for t in trace if t["state"] == "OBSERVATION"]
        assert len(obs_entries) == 4
        for t in obs_entries:
            assert t["tool_output"] is not None

    def test_timestamps_are_iso_format(self, trace: list[dict]) -> None:
        """timestamp 应为 ISO 格式。"""
        for t in trace:
            assert "T" in t["timestamp"]

    def test_elapsed_ms_non_negative(self, trace: list[dict]) -> None:
        """elapsed_ms 应 >= 0。"""
        for t in trace:
            assert t.get("elapsed_ms", -1) >= 0


# ═══════════════════════════════════════════════════════════
# 8. Prompt 集成验证
# ═══════════════════════════════════════════════════════════

class TestPromptIntegration:
    """Prompt 变量注入验证。"""

    def test_tool_list_in_prompt(self) -> None:
        """Prompt 应包含所有 4 个 Tool。"""
        runner = AgentRunner()
        prompt = runner.prepare("Python", 3, 12)
        for tool in ["get_course_info", "get_prerequisite",
                      "calculate_learning_time", "generate_learning_plan"]:
            assert tool in prompt, f"{tool} missing from prompt"

    def test_workflow_in_prompt(self) -> None:
        """Prompt 应包含工作流描述。"""
        runner = AgentRunner()
        prompt = runner.prepare("Python", 3, 12)
        assert "Step 1" in prompt
        assert "Step 2" in prompt
        assert "Step 3" in prompt
        assert "Step 4" in prompt

    def test_user_input_in_prompt(self) -> None:
        """Prompt 应包含用户输入信息。"""
        runner = AgentRunner()
        prompt = runner.prepare("Spark", 2, 30, ["Python", "Java"])
        assert "Spark" in prompt
        assert "2" in prompt
        assert "30" in prompt
        assert "Python" in prompt

    def test_output_schema_in_prompt(self) -> None:
        """Prompt 应包含输出格式说明。"""
        runner = AgentRunner()
        prompt = runner.prepare("Python", 3, 12)
        assert "学习计划" in prompt
        assert "课程概览" in prompt

    def test_prompt_stored_in_output(self, runner: AgentRunner) -> None:
        """run() 返回的 AgentRunOutput 应包含 prompt 字段。"""
        out = runner.run("Python", 3, 12)
        assert len(out.prompt) > 0
        assert "Python" in out.prompt


# ═══════════════════════════════════════════════════════════
# 9. 输出协议验证
# ═══════════════════════════════════════════════════════════

class TestOutputProtocol:
    """to_dict() 输出协议验证。"""

    def test_success_output_format(self) -> None:
        """成功输出的 to_dict() 应包含 success + data + trace。"""
        runner = AgentRunner()
        out = runner.run("Python", 3, 12)
        d = out.to_dict()
        assert d["success"] is True
        assert "data" in d
        assert "trace" in d
        assert "error" not in d

    def test_error_output_format(self) -> None:
        """失败输出的 to_dict() 应包含 success + error + trace。"""
        runner = AgentRunner()
        out = runner.run("Spark", 2, 30)
        d = out.to_dict()
        assert d["success"] is False
        assert "error" in d
        assert "trace" in d
        assert "data" not in d
