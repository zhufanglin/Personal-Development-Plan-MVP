"""
Tool 与 Tool Registry 单元测试。

覆盖:
- ToolRegistry: register / unregister / duplicate / overwrite / get / list / invoke / unknown / empty
- get_course_info: 查詢/大小寫/不存在/空輸入/返回結構
- get_prerequisite: 滿足/不滿足/深層鏈/推薦/DAG共享依賴
- calculate_learning_time: 可行/不可行/緩衝不足/三方案/參數驗證
- generate_learning_plan: 完整計劃/先修衝突/時間不足/跳過可選/trace
"""

import pytest

from src.agent.tool_registry import (
    ToolEntry,
    ToolRegistry,
    create_default_registry,
)
from src.tools.course_info import get_course_info
from src.tools.feasibility import calculate_learning_time
from src.tools.learning_plan import generate_learning_plan
from src.tools.prerequisites import get_prerequisite


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def empty_registry() -> ToolRegistry:
    """空 Registry。"""
    return ToolRegistry()


@pytest.fixture
def default_registry() -> ToolRegistry:
    """含全部 4 个 Tool 的默认 Registry。"""
    return create_default_registry()


@pytest.fixture
def sample_entry() -> ToolEntry:
    """範例 ToolEntry。"""
    return ToolEntry(
        name="sample_tool",
        description="A sample tool for testing",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {}},
        function=lambda **kw: {"success": True, "data": kw},
    )


# ═══════════════════════════════════════════════════════════
# ToolRegistry 测试
# ═══════════════════════════════════════════════════════════

class TestRegistryBasics:
    """基礎操作測試。"""

    def test_register(self, empty_registry: ToolRegistry, sample_entry: ToolEntry) -> None:
        """註冊一個 Tool，Registry 應包含它。"""
        empty_registry.register(sample_entry)
        assert len(empty_registry) == 1
        assert "sample_tool" in empty_registry

    def test_register_empty_name_raises(self, empty_registry: ToolRegistry) -> None:
        """空名稱應拋出 AppValidationError。"""
        from src.exceptions import ValidationError as AppValidationError
        bad_entry = ToolEntry(
            name="", description="", input_schema={}, output_schema={},
            function=lambda **kw: {},
        )
        with pytest.raises(AppValidationError):
            empty_registry.register(bad_entry)

    def test_unregister_existing(self, empty_registry: ToolRegistry, sample_entry: ToolEntry) -> None:
        """註銷已存在的 Tool。"""
        empty_registry.register(sample_entry)
        assert empty_registry.unregister("sample_tool") is True
        assert len(empty_registry) == 0

    def test_unregister_nonexistent(self, empty_registry: ToolRegistry) -> None:
        """註銷不存在的 Tool 應返回 False。"""
        assert empty_registry.unregister("nonexistent") is False

    def test_duplicate_register_overwrites(self, empty_registry: ToolRegistry, sample_entry: ToolEntry) -> None:
        """同名註冊應覆蓋舊的（冪等）。"""
        empty_registry.register(sample_entry)
        entry_v2 = ToolEntry(
            name="sample_tool", description="v2",
            input_schema={}, output_schema={},
            function=lambda **kw: {"success": True, "data": "v2"},
        )
        empty_registry.register(entry_v2)
        assert len(empty_registry) == 1  # 數量不變
        result = empty_registry.invoke("sample_tool")
        assert result["data"] == "v2"  # 執行的已是 v2

    def test_get_tool_found(self, empty_registry: ToolRegistry, sample_entry: ToolEntry) -> None:
        """獲取存在的 Tool。"""
        empty_registry.register(sample_entry)
        entry = empty_registry.get_tool("sample_tool")
        assert entry is not None
        assert entry.name == "sample_tool"

    def test_get_tool_not_found(self, empty_registry: ToolRegistry) -> None:
        """獲取不存在的 Tool 應返回 None。"""
        assert empty_registry.get_tool("nonexistent") is None

    def test_list_tools(self, default_registry: ToolRegistry) -> None:
        """列出所有 Tool 應返回元數據（不含 function）。"""
        tools = default_registry.list_tools()
        assert len(tools) == 4
        for t in tools:
            assert "name" in t
            assert "description" in t
            assert "input_schema" in t
            assert "output_schema" in t
            assert "function" not in t  # 不暴露函數引用

    def test_invoke_unknown_tool(self, empty_registry: ToolRegistry) -> None:
        """調用不存在的 Tool 應返回 TOOL_NOT_FOUND。"""
        result = empty_registry.invoke("nonexistent")
        assert result["success"] is False
        assert result["error"]["code"] == "TOOL_NOT_FOUND"
        assert "available" in result["error"]["details"]

    def test_empty_registry(self, empty_registry: ToolRegistry) -> None:
        """空 Registry 應有 0 個 Tool，list 為空。"""
        assert len(empty_registry) == 0
        assert empty_registry.list_tools() == []

    def test_register_all(self, empty_registry: ToolRegistry) -> None:
        """批量註冊。"""
        entries = [
            ToolEntry(name=f"tool_{i}", description=f"Tool {i}",
                      input_schema={}, output_schema={},
                      function=lambda i=i, **kw: {"success": True, "data": i})
            for i in range(3)
        ]
        empty_registry.register_all(entries)
        assert len(empty_registry) == 3
        for i in range(3):
            assert empty_registry.invoke(f"tool_{i}")["data"] == i


class TestRegistryInvoke:
    """invoke 調度測試。"""

    def test_invoke_passes_kwargs(self, empty_registry: ToolRegistry) -> None:
        """invoke 應將 **kwargs 傳遞給 Tool 函數。"""
        empty_registry.register(ToolEntry(
            name="echo", description="", input_schema={}, output_schema={},
            function=lambda **kw: {"success": True, "data": kw},
        ))
        result = empty_registry.invoke("echo", a=1, b="hello")
        assert result["data"] == {"a": 1, "b": "hello"}

    def test_invoke_returns_error_dict_on_exception(self, empty_registry: ToolRegistry) -> None:
        """Tool 拋出異常時應捕獲並返回 INTERNAL_ERROR。"""
        def broken(**kw: object) -> dict:
            raise RuntimeError("Boom!")

        empty_registry.register(ToolEntry(
            name="broken", description="", input_schema={}, output_schema={},
            function=broken,
        ))
        result = empty_registry.invoke("broken")
        assert result["success"] is False
        assert result["error"]["code"] == "INTERNAL_ERROR"
        assert "Boom" in result["error"]["message"]

    def test_invoke_all_default_tools(self, default_registry: ToolRegistry) -> None:
        """默认 Registry 的所有 4 個 Tool 應可獨立調用。"""
        # get_course_info
        r = default_registry.invoke("get_course_info", course_name="Python")
        assert r["success"] is True and r["data"]["name"] == "Python"

        # get_prerequisite
        r = default_registry.invoke("get_prerequisite", course_name="Python", user_knowledge=[])
        assert r["success"] is True and r["data"]["satisfied"] is True

        # calculate_learning_time
        r = default_registry.invoke("calculate_learning_time", course_name="Python", daily_hours=3, duration_days=12)
        assert r["success"] is True and r["data"]["feasible"] is True

        # generate_learning_plan
        r = default_registry.invoke("generate_learning_plan", course_name="Python", daily_hours=3, duration_days=12)
        assert r["success"] is True and "plan_id" in r["data"]


# ═══════════════════════════════════════════════════════════
# get_course_info 测试
# ═══════════════════════════════════════════════════════════

class TestGetCourseInfo:
    """get_course_info Tool 測試。"""

    def test_success_exact_match(self) -> None:
        """精確匹配應返回完整課程數據。"""
        r = get_course_info("Python")
        assert r["success"] is True
        d = r["data"]
        assert d["name"] == "Python"
        assert d["hours"] == 24.0
        assert d["difficulty"] == "beginner"
        assert len(d["topics"]) == 7
        assert isinstance(d["prerequisite"], list)

    def test_success_case_insensitive(self) -> None:
        """大小寫不敏感匹配。"""
        for query in ("python", "PYTHON", "Python", "  python  "):
            r = get_course_info(query)
            assert r["success"] is True and r["data"]["name"] == "Python"

    def test_not_found(self) -> None:
        """不存在的課程應返回 COURSE_NOT_FOUND。"""
        r = get_course_info("Nonexistent")
        assert r["success"] is False
        assert r["error"]["code"] == "COURSE_NOT_FOUND"
        assert "available_courses" in r["error"]["details"]

    def test_empty_input(self) -> None:
        """空字串應返回 VALIDATION_ERROR。"""
        r = get_course_info("")
        assert r["success"] is False
        assert r["error"]["code"] == "VALIDATION_ERROR"

    def test_output_schema_fields(self) -> None:
        """成功輸出應包含所有必要字段。"""
        r = get_course_info("Python")
        expected = {"id", "name", "hours", "difficulty", "prerequisite",
                     "description", "category", "topics"}
        assert set(r["data"].keys()) == expected

    def test_all_courses_accessible(self) -> None:
        """全部 10 門課程均可查詢。"""
        names = ["Python", "SQL", "Linux", "Git", "Java",
                 "Hadoop", "Hive", "Spark", "Kafka", "Flink"]
        for name in names:
            r = get_course_info(name)
            assert r["success"] is True, f"{name} should be found"


# ═══════════════════════════════════════════════════════════
# get_prerequisite 测试
# ═══════════════════════════════════════════════════════════

class TestGetPrerequisite:
    """get_prerequisite Tool 測試。"""

    def test_no_prerequisites(self) -> None:
        """無先修課的課程應返回 satisfied=true。"""
        r = get_prerequisite("Python", [])
        assert r["success"] is True
        assert r["data"]["satisfied"] is True
        assert r["data"]["missing"] == []
        assert r["data"]["total_prerequisite_hours"] == 0.0

    def test_shallow_missing(self) -> None:
        """直接先修課缺失。"""
        r = get_prerequisite("Hadoop", [])
        assert r["success"] is True
        assert r["data"]["satisfied"] is False
        assert "Linux" in r["data"]["missing"]
        assert "Java" in r["data"]["missing"]

    def test_deep_chain(self) -> None:
        """深層先修鏈: Spark → Hadoop → Linux+Java。"""
        r = get_prerequisite("Spark", [])
        d = r["data"]
        assert "Python" in d["required_prerequisites"]
        assert "Hadoop" in d["required_prerequisites"]
        assert "Linux" in d["required_prerequisites"]
        assert "Java" in d["required_prerequisites"]
        assert d["total_prerequisite_hours"] == 112.0

    def test_recommended_prerequisites(self) -> None:
        """推薦先修課應被列出但不影響 satisfied。"""
        r = get_prerequisite("Java", [])
        assert r["data"]["satisfied"] is True  # 無 required
        assert "Python" in r["data"]["recommended_prerequisites"]

    def test_user_completed_some(self) -> None:
        """用戶已完成部分先修課。"""
        r = get_prerequisite("Hadoop", ["Linux"])
        assert r["data"]["satisfied"] is False
        assert "Linux" in r["data"]["completed"]
        assert "Java" in r["data"]["missing"]

    def test_user_completed_all(self) -> None:
        """用戶已完成所有先修課。"""
        r = get_prerequisite("Hadoop", ["Linux", "Java"])
        assert r["data"]["satisfied"] is True
        assert r["data"]["missing"] == []

    def test_dag_shared_dependency(self) -> None:
        """DAG 共享依賴不應觸發循環錯誤: Flink→Java + Flink→Spark→Hadoop→Java。"""
        r = get_prerequisite("Flink", [])
        assert r["success"] is True
        # Java 應出現一次（去重）
        assert r["data"]["required_prerequisites"].count("Java") == 1

    def test_completed_skips_recursion(self) -> None:
        """已完成的課程不應遞歸展開其先修。"""
        # Spark 有先修 Python+Hadoop+Hadoop先修...但 Spark 已完成 → 不展開
        r = get_prerequisite("Flink", ["Java", "Spark"])
        assert r["data"]["satisfied"] is True

    def test_nonexistent_course(self) -> None:
        """不存在的課程應返回錯誤。"""
        r = get_prerequisite("QuantumComputing", [])
        assert r["success"] is False
        assert r["error"]["code"] == "COURSE_NOT_FOUND"

    def test_invalid_user_knowledge_type(self) -> None:
        """user_knowledge 不是 list 應返回 VALIDATION_ERROR。"""
        r = get_prerequisite("Python", "not_a_list")  # type: ignore[arg-type]
        assert r["success"] is False
        assert r["error"]["code"] == "VALIDATION_ERROR"

    def test_output_schema_fields(self) -> None:
        """輸出應包含所有必要字段。"""
        r = get_prerequisite("Python", [])
        expected = {"satisfied", "course_name", "required_prerequisites",
                     "recommended_prerequisites", "missing", "completed",
                     "total_prerequisite_hours", "recommendation"}
        assert set(r["data"].keys()) == expected


# ═══════════════════════════════════════════════════════════
# calculate_learning_time 测试
# ═══════════════════════════════════════════════════════════

class TestCalculateLearningTime:
    """calculate_learning_time Tool 測試。"""

    def test_feasible_with_buffer(self) -> None:
        """時間充足且緩衝足夠。"""
        r = calculate_learning_time("Python", 4, 10)
        d = r["data"]
        assert d["feasible"] is True
        assert d["buffer_sufficient"] is True
        assert d["available_hours"] == 40.0

    def test_feasible_but_tight(self) -> None:
        """時間充足但緩衝不足 20%。"""
        r = calculate_learning_time("Python", 2, 12)
        d = r["data"]
        assert d["feasible"] is True
        assert d["buffer_sufficient"] is False

    def test_infeasible(self) -> None:
        """時間不足。"""
        r = calculate_learning_time("Flink", 1, 10)
        d = r["data"]
        assert d["feasible"] is False
        assert d["buffer_hours"] < 0

    def test_three_adjustment_options(self) -> None:
        """不可行時應提供三種調整方案。"""
        r = calculate_learning_time("Flink", 1, 10)
        opts = r["data"]["adjustment_options"]
        assert len(opts) == 3
        strategies = {o["strategy"] for o in opts}
        assert strategies == {"extend_duration", "increase_hours", "reduce_scope"}

    def test_extend_duration_option(self) -> None:
        """延長方案應有正確的 new_duration_days。"""
        r = calculate_learning_time("Flink", 1, 10)
        opt = [o for o in r["data"]["adjustment_options"] if o["strategy"] == "extend_duration"][0]
        assert opt["new_duration_days"] == 36  # ceil(36/1)

    def test_increase_hours_option(self) -> None:
        """增加方案應有正確的 new_daily_hours。"""
        r = calculate_learning_time("Flink", 1, 10)
        opt = [o for o in r["data"]["adjustment_options"] if o["strategy"] == "increase_hours"][0]
        assert opt["new_daily_hours"] == 3.6

    def test_reduce_scope_option(self) -> None:
        """縮減方案應只計算必修模塊。"""
        r = calculate_learning_time("Python", 1, 10)
        opt = [o for o in r["data"]["adjustment_options"] if o["strategy"] == "reduce_scope"][0]
        assert opt["reduced_hours"] < 24.0  # 必修 < 總學時

    def test_validation_daily_hours_low(self) -> None:
        """daily_hours < 0.5 應返回 VALIDATION_ERROR。"""
        r = calculate_learning_time("Python", 0.1, 30)
        assert r["success"] is False and r["error"]["code"] == "VALIDATION_ERROR"

    def test_validation_daily_hours_high(self) -> None:
        """daily_hours > 16 應返回 VALIDATION_ERROR。"""
        r = calculate_learning_time("Python", 20, 30)
        assert r["success"] is False and r["error"]["code"] == "VALIDATION_ERROR"

    def test_validation_duration_days_invalid(self) -> None:
        """duration_days < 1 應返回 VALIDATION_ERROR。"""
        r = calculate_learning_time("Python", 2, 0)
        assert r["success"] is False and r["error"]["code"] == "VALIDATION_ERROR"

    def test_course_not_found(self) -> None:
        """不存在的課程應傳播 COURSE_NOT_FOUND。"""
        r = calculate_learning_time("Nonexistent", 2, 30)
        assert r["success"] is False and r["error"]["code"] == "COURSE_NOT_FOUND"

    def test_minimum_days_hours_calculated(self) -> None:
        """minimum_days_needed 和 minimum_hours_per_day 應正確計算。"""
        r = calculate_learning_time("Python", 2, 30)
        d = r["data"]
        assert d["minimum_days_needed"] == 12.0  # ceil(24/2)
        assert d["minimum_hours_per_day"] == 0.8  # 24/30

    def test_output_schema_fields(self) -> None:
        """輸出應包含所有核心字段。"""
        r = calculate_learning_time("Python", 3, 12)
        expected = {"feasible", "course_name", "course_total_hours",
                     "daily_hours", "duration_days", "available_hours",
                     "buffer_hours", "buffer_ratio", "recommended_buffer",
                     "buffer_sufficient", "minimum_days_needed",
                     "minimum_hours_per_day", "adjustment_options", "recommendation"}
        assert set(r["data"].keys()) == expected


# ═══════════════════════════════════════════════════════════
# generate_learning_plan 测试
# ═══════════════════════════════════════════════════════════

class TestGenerateLearningPlan:
    """generate_learning_plan Orchestrator 測試。"""

    def test_happy_path(self) -> None:
        """正常生成完整計劃。"""
        r = generate_learning_plan("Python", 3, 12)
        assert r["success"] is True
        d = r["data"]
        assert "plan_id" in d
        assert d["course_name"] == "Python"
        assert len(d["learning_path"]) == 7
        assert len(d["daily_schedule"]) >= 1
        assert len(d["resources"]) >= 1
        assert len(d["trace"]) == 6

    def test_prerequisite_conflict(self) -> None:
        """先修不滿足時返回錯誤。"""
        r = generate_learning_plan("Spark", 2, 30)
        assert r["success"] is False
        assert r["error"]["code"] == "PREREQUISITE_CONFLICT"
        assert "missing" in r["error"]["details"]

    def test_time_insufficient(self) -> None:
        """時間不足時返回錯誤（附帶三方案）。"""
        r = generate_learning_plan("Flink", 1, 10, user_knowledge=["Python", "Linux", "Java", "Spark"])
        assert r["success"] is False
        assert r["error"]["code"] == "TIME_INSUFFICIENT"
        assert "adjustment_options" in r["error"]["details"]

    def test_skip_optional(self) -> None:
        """跳過可選模塊。"""
        r = generate_learning_plan("Python", 2, 15, skip_optional=True)
        s = r["data"]["summary"]
        assert s["optional_modules"] == 0  # 跳過後無可選模塊
        assert s["skipped_modules"] == 1
        assert s["total_modules"] == 6  # 7 - 1 optional skipped

    def test_trace_records_all_steps(self) -> None:
        """trace 應記錄所有 6 步。"""
        r = generate_learning_plan("Python", 3, 12)
        trace = r["data"]["trace"]
        step_names = [t["tool"] for t in trace]
        assert "get_course_info" in step_names
        assert "get_prerequisite" in step_names
        assert "calculate_learning_time" in step_names
        assert "_build_learning_path" in step_names
        assert "scheduler.schedule" in step_names
        assert "resource_provider.get_resources" in step_names
        for t in trace:
            assert t["status"] == "ok"
            assert t["elapsed_ms"] >= 0

    def test_warnings_when_tight_buffer(self) -> None:
        """時間較緊時應產生警告。"""
        r = generate_learning_plan("Python", 2, 12)
        warnings = r["data"]["warnings"]
        assert len(warnings) >= 1

    def test_default_user_knowledge_empty(self) -> None:
        """不提供 user_knowledge 時默認空列表。"""
        r = generate_learning_plan("Python", 3, 12)
        assert r["success"] is True

    def test_parameters_echoed(self) -> None:
        """輸入參數應被回顯。"""
        r = generate_learning_plan("SQL", 2, 15, skip_optional=False, start_date="2026-08-01")
        p = r["data"]["parameters"]
        assert p["daily_hours"] == 2
        assert p["duration_days"] == 15
        assert p["skip_optional"] is False
        assert p["start_date"] == "2026-08-01"

    def test_summary_aggregates_correctly(self) -> None:
        """summary 的聚合數據應正確。"""
        r = generate_learning_plan("Python", 3, 12)
        s = r["data"]["summary"]
        assert s["total_learning_hours"] == 24.0
        assert s["study_days"] + s["review_days"] + s["assessment_days"] == s["total_days"]

    def test_output_schema_fields(self) -> None:
        """輸出應包含所有頂層字段。"""
        r = generate_learning_plan("Python", 3, 12)
        expected = {"plan_id", "course_name", "generated_at", "parameters",
                     "summary", "learning_path", "daily_schedule",
                     "resources", "warnings", "trace"}
        assert set(r["data"].keys()) == expected
