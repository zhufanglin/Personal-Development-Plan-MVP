"""
业务异常类。

所有 Agent 相关的业务异常统一在此定义。
每个异常包含错误码（error_code），与 Tool 层的 ErrorResponse 保持一致。
"""


class CourseLearningError(Exception):
    """Agent 业务异常的基类。"""

    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict | None = None) -> None:
        """
        初始化业务异常。

        Args:
            message: 人类可读的错误描述
            details: 可选的调试上下文信息
        """
        super().__init__(message)
        self.message: str = message
        self.details: dict | None = details


class CourseNotFoundError(CourseLearningError):
    """请求的课程不在目录中时抛出。"""

    error_code: str = "COURSE_NOT_FOUND"


class PrerequisiteConflictError(CourseLearningError):
    """用户不满足课程先修条件时抛出。"""

    error_code: str = "PREREQUISITE_CONFLICT"


class TimeInsufficientError(CourseLearningError):
    """学习时间不足以完成课程时抛出。"""

    error_code: str = "TIME_INSUFFICIENT"


class ValidationError(CourseLearningError):
    """输入参数不符合约束时抛出。"""

    error_code: str = "VALIDATION_ERROR"


class DataCorruptionError(CourseLearningError):
    """数据文件损坏或格式错误时抛出。"""

    error_code: str = "DATA_CORRUPTION"


class CircularDependencyError(CourseLearningError):
    """先修课程存在循环依赖时抛出。"""

    error_code: str = "CIRCULAR_DEPENDENCY"


class MaxRecursionDepthError(CourseLearningError):
    """先修树递归深度超限时抛出。"""

    error_code: str = "MAX_RECURSION_DEPTH"
