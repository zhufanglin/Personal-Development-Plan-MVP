"""
System Prompt Loader。

职责: 加载 System Prompt 模板，支持变量注入。
不单纯读取静态文件 — 支持 {{variable}} 占位符替换。
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── 文件路径 ──────────────────────────────────────────────

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"
_PROMPT_FILE = _PROMPTS_DIR / "system_prompt.txt"

# ── 输出格式模板（硬编码，未来可提取为独立文件） ─────────────

_OUTPUT_SCHEMA_TEMPLATE: str = """
## 输出格式

### 成功时:
# 📚 学习计划: {course_name}
## 课程概览 | 课程名称 | 难度 | 总学时 | 描述 |
## 先修条件检查 ✅ / ⚠️
## 可行性评估 | 可用时间 | 需要时间 | 缓冲时间 | 缓冲比例 |
## 学习路径 | 序号 | 模块 | 学时 | 类型 |
## 每日学习计划 | 天数 | 类型 | 学习内容 | 学时 |
## 推荐学习资源 | 模块 | 资源 | 类型 | 免费 |

### 先修冲突时:
# ⚠️ 先修条件不满足
## 目标课程 | 你的背景 | 缺失先修课 (含学时) | 建议先修路径 | 预估先修周期

### 时间不足时:
# ⚠️ 学习时间不足
## 时间分析表 | 方案 A (延长时间) | 方案 B (增加强度) | 方案 C (缩减范围)
"""


# ── 公开接口 ──────────────────────────────────────────────

def load_system_prompt(
    tool_registry: Any | None = None,
    workflow: str = "",
) -> str:
    """加载 System Prompt 模板并注入动态变量。

    Args:
        tool_registry: ToolRegistry 实例（可选）。
                       提供 {{tool_list}} 变量值。
        workflow: 工作流描述文本。
                  提供 {{workflow}} 变量值。

    Returns:
        str: 变量注入后的完整 System Prompt
    """
    # ── 读取模板 ──────────────────────────────────────
    template: str = _read_template()

    # ── 构建变量表 ────────────────────────────────────
    variables: dict[str, str] = {}

    # tool_list: 从 Registry 获取
    if tool_registry is not None:
        tools = tool_registry.list_tools()
        lines: list[str] = []
        for t in tools:
            lines.append(
                f"- {t['name']}: {t['description']}"
            )
        variables["tool_list"] = "\n".join(lines)
    else:
        variables["tool_list"] = "(Tool list not available — registry not provided)"

    # workflow: 从 Agent FSM 传入
    variables["workflow"] = workflow if workflow else "(Workflow not specified)"

    # current_date: 动态日期
    variables["current_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # output_schema: 硬编码输出格式
    variables["output_schema"] = _OUTPUT_SCHEMA_TEMPLATE

    # ── 变量替换 ──────────────────────────────────────
    resolved: str = template
    for var_name, var_value in variables.items():
        placeholder: str = "{{" + var_name + "}}"
        resolved = resolved.replace(placeholder, var_value)

    return resolved


def format_prompt_with_input(
    system_prompt: str,
    course_name: str,
    daily_hours: float,
    duration_days: int,
    user_knowledge: list[str] | None = None,
) -> str:
    """将用户输入注入到 System Prompt 中。

    Args:
        system_prompt: load_system_prompt() 返回的完整 Prompt
        course_name: 课程名称
        daily_hours: 每日学习小时数
        duration_days: 学习天数
        user_knowledge: 用户已完成课程列表

    Returns:
        str: 包含用户输入的完整 Prompt 上下文
    """
    knowledge: list[str] = user_knowledge or []
    knowledge_str: str = "、".join(knowledge) if knowledge else "（无）"

    user_input: str = (
        f"\n\n---\n\n"
        f"## 用户输入\n\n"
        f"- 课程名称: {course_name}\n"
        f"- 每日学习时间: {daily_hours} 小时\n"
        f"- 学习周期: {duration_days} 天\n"
        f"- 已完成的课程: {knowledge_str}\n"
        f"- 当前日期: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n"
    )

    # 注入 {{user_input}}
    return system_prompt.replace("{{user_input}}", user_input)


# ── 内部函数 ──────────────────────────────────────────────

def _read_template() -> str:
    """读取 System Prompt 模板文件。

    Returns:
        str: 模板原始内容

    Raises:
        FileNotFoundError: 如果模板文件不存在
    """
    if not _PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"System Prompt 模板文件不存在: {_PROMPT_FILE}\n"
            f"请确认文件已放入 prompts/ 目录"
        )

    with open(_PROMPT_FILE, encoding="utf-8") as f:
        return f.read()


# ── PromptLoader 类（依赖注入友好） ──────────────────────────

class PromptLoader:
    """System Prompt 加载器（可注入）。

    封装模板读取和变量注入，支持依赖注入替换。
    """

    def load(
        self,
        tool_registry: Any | None = None,
        workflow: str = "",
    ) -> str:
        """加载 System Prompt 并注入动态变量。

        Args:
            tool_registry: ToolRegistry 实例
            workflow: 工作流描述文本

        Returns:
            str: 变量注入后的完整 System Prompt
        """
        return load_system_prompt(tool_registry=tool_registry, workflow=workflow)

    def format_with_input(
        self,
        system_prompt: str,
        course_name: str,
        daily_hours: float,
        duration_days: int,
        user_knowledge: list[str] | None = None,
    ) -> str:
        """将用户输入注入到 System Prompt 中。

        Args:
            system_prompt: load() 返回的完整 Prompt
            course_name: 课程名称
            daily_hours: 每日学习小时数
            duration_days: 学习天数
            user_knowledge: 用户已完成课程列表

        Returns:
            str: 包含用户输入的完整 Prompt 上下文
        """
        return format_prompt_with_input(
            system_prompt=system_prompt,
            course_name=course_name,
            daily_hours=daily_hours,
            duration_days=duration_days,
            user_knowledge=user_knowledge,
        )
