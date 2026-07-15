"""
数据模型单元测试。

覆盖:
- Topic / Course 模型验证与序列化
- LearningPath / Module / DailyPlan / DayEntry 模型
- FeasibilityResult / AdjustmentOption / PrerequisiteCheck 模型
- JSON 直接加载与验证
- 业务异常类
- 边界测试 (零值、空列表、最大长度)
- 非法输入测试 (类型错误、范围超限、缺失必填字段)
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.exceptions import (
    CircularDependencyError,
    CourseLearningError,
    CourseNotFoundError,
    DataCorruptionError,
    MaxRecursionDepthError,
    PrerequisiteConflictError,
    TimeInsufficientError,
    ValidationError as AppValidationError,
)
from src.models import (
    AdjustmentOption,
    Course,
    DailyPlan,
    DayEntry,
    FeasibilityResult,
    LearningPath,
    Module,
    PrerequisiteCheck,
    Topic,
)

# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def valid_topic() -> dict:
    """返回一个合法的 Topic 字典。"""
    return {
        "name": "变量与数据类型",
        "hours": 3.0,
        "order": 1,
        "required": True,
        "description": "Python 基础数据类型",
    }


@pytest.fixture
def valid_course() -> dict:
    """返回一个合法的 Course 字典。"""
    return {
        "id": "COURSE-TEST-001",
        "name": "Test Course",
        "hours": 20.0,
        "difficulty": "beginner",
        "prerequisite": [],
        "description": "A test course for unit testing",
        "category": "testing",
        "topics": [
            {
                "name": "Topic 1",
                "hours": 10.0,
                "order": 1,
                "required": True,
                "description": "First topic",
            },
            {
                "name": "Topic 2",
                "hours": 10.0,
                "order": 2,
                "required": True,
                "description": "Second topic",
            },
        ],
    }


@pytest.fixture
def all_courses() -> list[dict]:
    """加载 courses.json 中的所有课程。"""
    with open(DATA_DIR / "courses.json", encoding="utf-8") as f:
        data = json.load(f)
    return data["courses"]


# ═══════════════════════════════════════════════════════════
# Topic 模型测试
# ═══════════════════════════════════════════════════════════

class TestTopic:
    """Topic 模型单元测试。"""

    def test_create_valid_topic(self, valid_topic: dict) -> None:
        """合法数据应成功创建 Topic。"""
        topic = Topic(**valid_topic)
        assert topic.name == "变量与数据类型"
        assert topic.hours == 3.0
        assert topic.order == 1
        assert topic.required is True

    def test_topic_default_description(self) -> None:
        """description 默认值应为空字符串。"""
        topic = Topic(name="Test", hours=1.0, order=1, required=True)
        assert topic.description == ""

    def test_topic_negative_hours_raises(self) -> None:
        """负数学时不应通过验证（ge=0 约束只校验 >=0，pydantic 允许 0 但不允许负数）。"""
        with pytest.raises(ValidationError):
            Topic(name="Bad", hours=-1.0, order=1, required=True)

    def test_topic_zero_order_raises(self) -> None:
        """order < 1 应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Topic(name="Bad", hours=1.0, order=0, required=True)

    def test_topic_missing_required_field_raises(self) -> None:
        """缺失必填字段应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Topic(name="Bad")  # type: ignore[call-arg]

    def test_topic_serialize(self, valid_topic: dict) -> None:
        """model_dump() 应输出正确的字典。"""
        topic = Topic(**valid_topic)
        dumped = topic.model_dump()
        assert dumped["name"] == "变量与数据类型"
        assert dumped["hours"] == 3.0

    def test_topic_optional_true_and_false(self) -> None:
        """required 字段支持 True 和 False。"""
        req = Topic(name="Required", hours=2.0, order=1, required=True)
        opt = Topic(name="Optional", hours=1.0, order=2, required=False)
        assert req.required is True
        assert opt.required is False


# ═══════════════════════════════════════════════════════════
# Course 模型测试
# ═══════════════════════════════════════════════════════════

class TestCourse:
    """Course 模型单元测试。"""

    def test_create_valid_course(self, valid_course: dict) -> None:
        """合法数据应成功创建 Course。"""
        course = Course(**valid_course)
        assert course.id == "COURSE-TEST-001"
        assert course.name == "Test Course"
        assert course.hours == 20.0
        assert course.difficulty == "beginner"
        assert course.category == "testing"
        assert len(course.topics) == 2

    def test_course_empty_prerequisite_default(self) -> None:
        """未提供 prerequisite 时应默认为空列表。"""
        data = {
            "id": "COURSE-TEST-002",
            "name": "No Prereq",
            "hours": 10.0,
            "difficulty": "beginner",
            "description": "Test",
            "category": "test",
            "topics": [{"name": "T", "hours": 10.0, "order": 1, "required": True}],
        }
        course = Course(**data)
        assert course.prerequisite == []

    def test_course_invalid_id_pattern_raises(self) -> None:
        """不符合 COURSE-XX-NNN 格式的 id 应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Course(
                id="bad-id",
                name="Test",
                hours=10,
                difficulty="beginner",
                description="Test",
                topics=[{"name": "T", "hours": 10, "order": 1, "required": True}],
            )

    def test_course_empty_name_raises(self) -> None:
        """空课程名应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Course(
                id="COURSE-TEST-003",
                name="",
                hours=10,
                difficulty="beginner",
                description="Test",
                topics=[{"name": "T", "hours": 10, "order": 1, "required": True}],
            )

    def test_course_invalid_difficulty_raises(self) -> None:
        """非法的 difficulty 值应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Course(
                id="COURSE-TEST-004",
                name="Test",
                hours=10,
                difficulty="expert",  # type: ignore[arg-type]
                description="Test",
                topics=[{"name": "T", "hours": 10, "order": 1, "required": True}],
            )

    def test_course_empty_topics_raises(self) -> None:
        """空 topics 列表应抛出 ValidationError（min_length=1）。"""
        with pytest.raises(ValidationError):
            Course(
                id="COURSE-TEST-005",
                name="Test",
                hours=10,
                difficulty="beginner",
                description="Test",
                topics=[],
            )

    def test_course_serialize(self, valid_course: dict) -> None:
        """model_dump() 应输出所有字段。"""
        course = Course(**valid_course)
        dumped = course.model_dump()
        assert "id" in dumped
        assert "name" in dumped
        assert "hours" in dumped
        assert "difficulty" in dumped
        assert "prerequisite" in dumped
        assert "description" in dumped
        assert "category" in dumped
        assert "topics" in dumped

    def test_course_field_names_match_json(self) -> None:
        """确保字段名与 courses.json 的键名完全一致。"""
        field_names = set(Course.model_fields.keys())
        # courses.json 的键:
        json_keys = {"id", "name", "hours", "difficulty", "prerequisite",
                      "description", "category", "topics"}
        assert field_names == json_keys, f"Mismatch: {field_names ^ json_keys}"


# ═══════════════════════════════════════════════════════════
# LearningPath / Module / DailyPlan / DayEntry 测试
# ═══════════════════════════════════════════════════════════

class TestLearningPathModels:
    """LearningPath 相关模型单元测试。"""

    def test_create_module(self) -> None:
        """合法数据应成功创建 Module。"""
        m = Module(
            name="变量",
            topic="变量与数据类型",
            hours=3.0,
            order=1,
            required=True,
            estimated_days=1.5,
        )
        assert m.name == "变量"
        assert m.estimated_days == 1.5

    def test_create_learning_path(self) -> None:
        """合法数据应成功创建 LearningPath。"""
        modules = [
            Module(name="M1", topic="T1", hours=5.0, order=1, required=True, estimated_days=2.5),
            Module(name="M2", topic="T2", hours=3.0, order=2, required=False, estimated_days=1.5),
        ]
        lp = LearningPath(
            course_name="Test",
            modules=modules,
            total_modules=2,
            required_modules=1,
            optional_modules=1,
            total_hours=8.0,
        )
        assert lp.total_modules == 2
        assert lp.required_modules == 1
        assert lp.optional_modules == 1

    def test_create_day_entry(self) -> None:
        """合法数据应成功创建 DayEntry。"""
        de = DayEntry(day=1, topics=["变量", "流程控制"], hours=2.0, type="study")
        assert de.day == 1
        assert de.type == "study"

    def test_day_entry_invalid_type_raises(self) -> None:
        """非法的 type 值应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            DayEntry(day=1, topics=["X"], hours=1.0, type="lecture")  # type: ignore[arg-type]

    def test_create_daily_plan(self) -> None:
        """合法数据应成功创建 DailyPlan。"""
        days = [
            DayEntry(day=1, topics=["A"], hours=2.0, type="study"),
            DayEntry(day=2, topics=["A"], hours=2.0, type="study"),
            DayEntry(day=3, topics=[], hours=2.0, type="review"),
        ]
        dp = DailyPlan(
            days=days,
            total_days=3,
            total_hours=6.0,
            includes_review_days=True,
            includes_assessments=False,
        )
        assert dp.total_days == 3
        assert dp.includes_review_days is True
        assert dp.includes_assessments is False

    def test_daily_plan_default_flags(self) -> None:
        """includes_review_days 和 includes_assessments 默认应为 False。"""
        dp = DailyPlan(
            days=[DayEntry(day=1, topics=["A"], hours=2.0, type="study")],
            total_days=1,
            total_hours=2.0,
        )
        assert dp.includes_review_days is False
        assert dp.includes_assessments is False

    def test_module_negative_hours_raises(self) -> None:
        """负数学时应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Module(name="Bad", topic="T", hours=-1.0, order=1, required=True, estimated_days=1.0)

    def test_day_entry_zero_day_raises(self) -> None:
        """day < 1 应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            DayEntry(day=0, topics=["X"], hours=1.0, type="study")


# ═══════════════════════════════════════════════════════════
# FeasibilityResult / PrerequisiteCheck / AdjustmentOption 测试
# ═══════════════════════════════════════════════════════════

class TestFeasibilityModels:
    """可行性相关模型单元测试。"""

    def test_create_feasible_result(self) -> None:
        """可行结果应正确创建。"""
        fr = FeasibilityResult(
            feasible=True,
            course_name="Python",
            course_total_hours=24.0,
            daily_hours=3.0,
            duration_days=12,
            available_hours=36.0,
            buffer_hours=12.0,
            buffer_ratio=0.5,
            minimum_days_needed=8.0,
            minimum_hours_per_day=2.0,
            recommendation="可行，缓冲充足。",
        )
        assert fr.feasible is True
        assert fr.buffer_hours == 12.0

    def test_create_infeasible_result(self) -> None:
        """不可行结果（buffer_hours 为负数）应正确创建。"""
        fr = FeasibilityResult(
            feasible=False,
            course_name="Flink",
            course_total_hours=36.0,
            daily_hours=1.0,
            duration_days=10,
            available_hours=10.0,
            buffer_hours=-26.0,
            buffer_ratio=-0.72,
            minimum_days_needed=36.0,
            minimum_hours_per_day=3.6,
            recommendation="不可行。",
        )
        assert fr.feasible is False
        assert fr.buffer_hours == -26.0
        assert fr.minimum_days_needed == 36.0

    def test_create_adjustment_option_extend(self) -> None:
        """延长周期方案应正确创建。"""
        ao = AdjustmentOption(
            strategy="extend_duration",
            label="方案 A: 延长学习周期",
            description="保持每天 1h，延长至 36 天。",
            new_duration_days=36,
        )
        assert ao.strategy == "extend_duration"
        assert ao.new_duration_days == 36
        assert ao.new_daily_hours is None

    def test_create_adjustment_option_increase(self) -> None:
        """增加强度方案应正确创建。"""
        ao = AdjustmentOption(
            strategy="increase_hours",
            label="方案 B: 增加每日学习时间",
            description="保持 10 天周期，每天学 3.6h。",
            new_daily_hours=3.6,
        )
        assert ao.strategy == "increase_hours"
        assert ao.new_daily_hours == 3.6
        assert ao.new_duration_days is None

    def test_create_adjustment_option_reduce(self) -> None:
        """缩减范围方案应正确创建。"""
        ao = AdjustmentOption(
            strategy="reduce_scope",
            label="方案 C: 缩减学习范围",
            description="跳过可选模块，必学降至 31h。",
            reduced_hours=31.0,
        )
        assert ao.strategy == "reduce_scope"
        assert ao.reduced_hours == 31.0

    def test_create_prerequisite_check_satisfied(self) -> None:
        """先修满足的结果应正确创建。"""
        pc = PrerequisiteCheck(
            satisfied=True,
            course_name="Python",
            required_prerequisites=[],
            missing=[],
            completed=[],
            total_prerequisite_hours=0.0,
            recommendation="无先修要求。",
        )
        assert pc.satisfied is True
        assert pc.missing == []

    def test_create_prerequisite_check_unsatisfied(self) -> None:
        """先修不满足的结果应正确创建。"""
        pc = PrerequisiteCheck(
            satisfied=False,
            course_name="Spark",
            required_prerequisites=["Python", "Hadoop", "Linux", "Java"],
            missing=["Python", "Hadoop", "Linux", "Java"],
            completed=[],
            total_prerequisite_hours=112.0,
            recommendation="需要先完成 4 门先修课，共 112h。",
        )
        assert pc.satisfied is False
        assert len(pc.missing) == 4
        assert pc.total_prerequisite_hours == 112.0

    def test_prerequisite_check_defaults(self) -> None:
        """未提供的列表字段应默认为空列表。"""
        pc = PrerequisiteCheck(satisfied=True, course_name="Test")
        assert pc.required_prerequisites == []
        assert pc.missing == []
        assert pc.completed == []
        assert pc.total_prerequisite_hours == 0.0
        assert pc.recommendation == ""

    def test_feasibility_negative_available_hours_raises(self) -> None:
        """available_hours 不能为负（ge=0 约束）。"""
        with pytest.raises(ValidationError):
            FeasibilityResult(
                feasible=False,
                course_name="Test",
                course_total_hours=10.0,
                daily_hours=1.0,
                duration_days=1,
                available_hours=-1.0,
                buffer_hours=-11.0,
                buffer_ratio=-1.1,
                minimum_days_needed=10.0,
                minimum_hours_per_day=10.0,
                recommendation="No",
            )


# ═══════════════════════════════════════════════════════════
# JSON 数据加载测试
# ═══════════════════════════════════════════════════════════

class TestJsonLoading:
    """courses.json 加载与验证测试。"""

    def test_load_all_courses(self, all_courses: list[dict]) -> None:
        """courses.json 中所有课程应被成功解析。"""
        courses = [Course(**c) for c in all_courses]
        assert len(courses) == 10

    def test_all_courses_have_valid_id(self, all_courses: list[dict]) -> None:
        """所有课程 id 应符合 COURSE-XX-NNN 格式。"""
        courses = [Course(**c) for c in all_courses]
        for c in courses:
            assert c.id.startswith("COURSE-"), f"Invalid id: {c.id}"

    def test_all_courses_have_topics(self, all_courses: list[dict]) -> None:
        """所有课程至少有一个 topic。"""
        courses = [Course(**c) for c in all_courses]
        for c in courses:
            assert len(c.topics) >= 1, f"{c.name} has no topics"

    def test_all_courses_have_valid_difficulty(self, all_courses: list[dict]) -> None:
        """所有课程 difficulty 应为合法值。"""
        valid = {"beginner", "intermediate", "advanced"}
        courses = [Course(**c) for c in all_courses]
        for c in courses:
            assert c.difficulty in valid, f"{c.name}: {c.difficulty}"

    def test_topic_orders_are_sequential(self, all_courses: list[dict]) -> None:
        """每个课程的 topics 应按 order 字段升序排列且连续。"""
        courses = [Course(**c) for c in all_courses]
        for c in courses:
            orders = [t.order for t in c.topics]
            assert orders == sorted(orders), f"{c.name}: topics not sorted"

    def test_hours_roughly_match_topics(self, all_courses: list[dict]) -> None:
        """课程的 hours 应 >= 所有 topics 的 hours 之和。"""
        courses = [Course(**c) for c in all_courses]
        for c in courses:
            topic_sum = sum(t.hours for t in c.topics)
            assert c.hours >= topic_sum, (
                f"{c.name}: course hours ({c.hours}) < topic sum ({topic_sum})"
            )

    def test_multi_prereq_courses_exist(self, all_courses: list[dict]) -> None:
        """至少有一个课程有多个先修课（触发先修异常）。"""
        courses = [Course(**c) for c in all_courses]
        multi = [c for c in courses if len(c.prerequisite) >= 2]
        assert len(multi) >= 1, "No course with >=2 prerequisites found"

    def test_prerequisite_graph_consistency(self, all_courses: list[dict]) -> None:
        """所有课程的 prerequisite 应指向真实存在的课程名。"""
        courses = [Course(**c) for c in all_courses]
        names = {c.name for c in courses}
        for c in courses:
            for prereq in c.prerequisite:
                assert prereq in names, (
                    f"{c.name}: prerequisite '{prereq}' not found in catalog"
                )


# ═══════════════════════════════════════════════════════════
# 业务异常测试
# ═══════════════════════════════════════════════════════════

class TestExceptions:
    """业务异常类单元测试。"""

    def test_course_not_found_error(self) -> None:
        """CourseNotFoundError 应有正确的 error_code。"""
        err = CourseNotFoundError("Course 'X' not found")
        assert err.error_code == "COURSE_NOT_FOUND"
        assert "X" in str(err)

    def test_prerequisite_conflict_error(self) -> None:
        """PrerequisiteConflictError 应有正确的 error_code 和 details。"""
        err = PrerequisiteConflictError(
            "Missing prerequisites",
            details={"missing": ["Python", "Hadoop"]},
        )
        assert err.error_code == "PREREQUISITE_CONFLICT"
        assert err.details == {"missing": ["Python", "Hadoop"]}

    def test_time_insufficient_error(self) -> None:
        """TimeInsufficientError 应有正确的 error_code。"""
        err = TimeInsufficientError("Not enough time", details={"deficit": 26.0})
        assert err.error_code == "TIME_INSUFFICIENT"
        assert err.details["deficit"] == 26.0

    def test_validation_error(self) -> None:
        """AppValidationError 应有正确的 error_code。"""
        err = AppValidationError("Invalid input", details={"field": "daily_hours"})
        assert err.error_code == "VALIDATION_ERROR"
        assert err.details["field"] == "daily_hours"

    def test_data_corruption_error(self) -> None:
        """DataCorruptionError 应有正确的 error_code。"""
        err = DataCorruptionError("JSON parse error")
        assert err.error_code == "DATA_CORRUPTION"

    def test_circular_dependency_error(self) -> None:
        """CircularDependencyError 应有正确的 error_code。"""
        err = CircularDependencyError("A -> B -> A")
        assert err.error_code == "CIRCULAR_DEPENDENCY"

    def test_max_recursion_depth_error(self) -> None:
        """MaxRecursionDepthError 应有正确的 error_code。"""
        err = MaxRecursionDepthError("Max depth 5 exceeded")
        assert err.error_code == "MAX_RECURSION_DEPTH"

    def test_all_exceptions_inherit_from_base(self) -> None:
        """所有异常应继承自 CourseLearningError。"""
        exceptions = [
            CourseNotFoundError(""),
            PrerequisiteConflictError(""),
            TimeInsufficientError(""),
            AppValidationError(""),
            DataCorruptionError(""),
            CircularDependencyError(""),
            MaxRecursionDepthError(""),
        ]
        for exc in exceptions:
            assert isinstance(exc, CourseLearningError), type(exc)

    def test_exception_is_exception(self) -> None:
        """所有异常应同时是 Python Exception 的子类。"""
        err = CourseNotFoundError("test")
        assert isinstance(err, Exception)

    def test_exception_details_default_none(self) -> None:
        """未提供 details 时默认应为 None。"""
        err = CourseNotFoundError("test")
        assert err.details is None


# ═══════════════════════════════════════════════════════════
# 边界测试
# ═══════════════════════════════════════════════════════════

class TestBoundary:
    """边界值测试。"""

    def test_course_zero_hours(self) -> None:
        """hours=0 应通过验证（虽然现实中不常见）。"""
        course = Course(
            id="COURSE-TEST-006",
            name="Zero Hour",
            hours=0.0,
            difficulty="beginner",
            description="Zero",
            topics=[{"name": "T", "hours": 0.0, "order": 1, "required": True}],
        )
        assert course.hours == 0.0

    def test_course_max_name_length(self) -> None:
        """课程名接近 max_length=100 时应通过验证。"""
        name = "A" * 100
        course = Course(
            id="COURSE-TEST-007",
            name=name,
            hours=1.0,
            difficulty="beginner",
            description="Long name test",
            topics=[{"name": "T", "hours": 1.0, "order": 1, "required": True}],
        )
        assert len(course.name) == 100

    def test_course_name_exceeds_max_raises(self) -> None:
        """课程名超过 100 字符应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Course(
                id="COURSE-TEST-008",
                name="A" * 101,
                hours=1.0,
                difficulty="beginner",
                description="Too long",
                topics=[{"name": "T", "hours": 1.0, "order": 1, "required": True}],
            )

    def test_course_all_difficulties(self) -> None:
        """三种 difficulty 值应全部通过验证。"""
        for diff in ("beginner", "intermediate", "advanced"):
            course = Course(
                id="COURSE-TEST-009",
                name=f"{diff} course",
                hours=1.0,
                difficulty=diff,  # type: ignore[arg-type]
                description="Test",
                topics=[{"name": "T", "hours": 1.0, "order": 1, "required": True}],
            )
            assert course.difficulty == diff

    def test_topic_zero_hours(self) -> None:
        """Topic hours=0 应通过验证。"""
        topic = Topic(name="Zero", hours=0.0, order=1, required=True)
        assert topic.hours == 0.0

    def test_daily_plan_empty_days(self) -> None:
        """空 days 列表的 DailyPlan 应通过验证。"""
        dp = DailyPlan(days=[], total_days=0, total_hours=0.0)
        assert dp.total_days == 0


# ═══════════════════════════════════════════════════════════
# 非法输入测试
# ═══════════════════════════════════════════════════════════

class TestInvalidInput:
    """各类非法输入的综合测试。"""

    def test_course_wrong_type_for_hours(self) -> None:
        """hours 传入字符串应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Course(
                id="COURSE-TEST-010",
                name="Bad Type",
                hours="twenty",  # type: ignore[arg-type]
                difficulty="beginner",
                description="Test",
                topics=[{"name": "T", "hours": 1.0, "order": 1, "required": True}],
            )

    def test_course_wrong_type_for_prerequisite(self) -> None:
        """prerequisite 传入字符串而非列表应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            Course(
                id="COURSE-TEST-011",
                name="Bad Type",
                hours=10.0,
                difficulty="beginner",
                prerequisite="Python",  # type: ignore[arg-type]
                description="Test",
                topics=[{"name": "T", "hours": 10.0, "order": 1, "required": True}],
            )

    def test_topic_wrong_type_for_required(self) -> None:
        """required 传入非布尔值应抛出 ValidationError（None 无法强制转换）。"""
        with pytest.raises(ValidationError):
            Topic(name="Bad", hours=1.0, order=1, required=None)  # type: ignore[arg-type]

    def test_day_entry_wrong_type_for_day(self) -> None:
        """day 传入浮点数应抛出 ValidationError（int 类型约束）。"""
        with pytest.raises(ValidationError):
            DayEntry(day=1.5, topics=["X"], hours=1.0, type="study")  # type: ignore[arg-type]

    @pytest.mark.parametrize("field,value", [
        ("name", ""),
        ("hours", -1.0),
        ("order", 0),
    ])
    def test_topic_field_constraints(self, field: str, value) -> None:
        """Topic 各字段的约束应生效。"""
        data = {"name": "Test", "hours": 1.0, "order": 1, "required": True}
        data[field] = value
        with pytest.raises(ValidationError):
            Topic(**data)


# ═══════════════════════════════════════════════════════════
# model_dump / model_dump_json 测试
# ═══════════════════════════════════════════════════════════

class TestSerialization:
    """序列化相关测试。"""

    def test_course_model_dump_json(self, valid_course: dict) -> None:
        """model_dump_json() 应输出合法 JSON 字符串。"""
        course = Course(**valid_course)
        json_str = course.model_dump_json()
        assert isinstance(json_str, str)
        reloaded = json.loads(json_str)
        assert reloaded["id"] == "COURSE-TEST-001"

    def test_feasibility_model_dump_json(self) -> None:
        """FeasibilityResult 序列化应保留所有字段。"""
        fr = FeasibilityResult(
            feasible=True,
            course_name="Python",
            course_total_hours=24.0,
            daily_hours=3.0,
            duration_days=12,
            available_hours=36.0,
            buffer_hours=12.0,
            buffer_ratio=0.5,
            minimum_days_needed=8.0,
            minimum_hours_per_day=2.0,
            recommendation="可行。",
        )
        dumped = fr.model_dump()
        assert dumped["feasible"] is True
        assert dumped["buffer_hours"] == 12.0
        assert "adjustment_options" not in dumped  # 不是 FeasibilityResult 的字段

    def test_prerequisite_check_serialize(self) -> None:
        """PrerequisiteCheck 序列化应保留嵌套列表。"""
        pc = PrerequisiteCheck(
            satisfied=False,
            course_name="Spark",
            required_prerequisites=["Python", "Hadoop"],
            missing=["Python", "Hadoop"],
            completed=[],
            total_prerequisite_hours=60.0,
            recommendation="先学 Python 和 Hadoop",
        )
        dumped = pc.model_dump()
        assert len(dumped["missing"]) == 2
        assert dumped["total_prerequisite_hours"] == 60.0
