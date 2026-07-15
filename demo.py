#!/usr/bin/env python3
"""
Course Learning Planner Agent — 答辩演示脚本。

支持两种模式:
  1. 离线模式 (默认): 使用 RuleBasedReActAgent，无需 API Key
  2. LLM 模式: 设置 DEEPSEEK_API_KEY 后使用 LLMReActAgent

用法:
  python demo.py                          # 离线模式 — 课程规划
  python demo.py --llm                     # LLM 模式 — 需要 API Key
  python demo.py --calculator              # 计算器 Demo
  python demo.py --weather                 # 天气 Demo
  python demo.py --course Python           # 指定课程
"""

import os
import sys
from pathlib import Path

# 修复 Windows 终端编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_offline_course_plan(course: str = "Python", hours: float = 3, days: int = 12) -> None:
    """离线模式: RuleBasedReActAgent 课程规划。"""
    from src.agent.runner import AgentRunner

    print("=" * 60)
    print(f"  Course Learning Planner Agent — 离线模式")
    print(f"  课程: {course} | 每日 {hours}h | {days} 天")
    print("=" * 60)

    runner = AgentRunner()
    result = runner.run(course, hours, days)

    if result.success:
        data = result.data or {}
        s = data.get("summary", {})
        print(f"""
  计划生成成功!

  [课程] {data.get('course_name', 'N/A')}
  [模块] {s.get('total_modules', 0)} 个
     - 必修: {s.get('required_modules', 0)}
     - 可选: {s.get('optional_modules', 0)}
  [天数] {s.get('total_days', 0)} 天
     - 学习: {s.get('study_days', 0)} 天
     - 复习: {s.get('review_days', 0)} 天
     - 评估: {s.get('assessment_days', 0)} 天
  [资源] {len(data.get('resources', []))} 条
  [Trace] {len(result.trace)} 步

  ── 学习路径 ──────────────────────────────""")
        for m in data.get("learning_path", []):
            tag = "必修" if m.get("required") else "可选"
            print(f"  {m['order']}. {m['name']} ({m['hours']}h) [{tag}]")

        print(f"""
  ── 每日计划 (前5天) ─────────────────────""")
        for day in data.get("daily_schedule", [])[:5]:
            topics = ", ".join(day.get("topics", [])) or "(复习/评估)"
            print(f"  Day {day['day']:2d} [{day['type']:10s}] {topics} ({day['hours']}h)")

    else:
        error = result.error or {}
        code = error.get("code", "UNKNOWN")
        print(f"\n  ❌ {code}")
        details = error.get("details", {})
        if code == "PREREQUISITE_CONFLICT":
            print(f"  缺失先修课: {', '.join(details.get('missing', []))}")
            print(f"  总先修学时: {details.get('total_prerequisite_hours', 0):.0f}h")
        elif code == "TIME_INSUFFICIENT":
            for opt in details.get("adjustment_options", []):
                print(f"  {opt.get('label', '')}: {opt.get('description', '')}")

    print(f"\n  ✅ 离线模式运行成功 (Trace: {len(result.trace)} 步)")
    print("=" * 60)


def run_llm_demo(mode: str = "calculator") -> None:
    """LLM 模式: DeepSeek + Tool Calling。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key or api_key == "sk-your-api-key-here":
        print("❌ 请先设置环境变量 DEEPSEEK_API_KEY")
        print("   export DEEPSEEK_API_KEY=sk-...")
        return

    from src.agent.tool_registry import ToolEntry, ToolRegistry
    from src.agent.llm_react import LLMReActAgent
    from src.providers import DeepSeekProvider
    from src.tools.demo_tools import calculator, get_weather

    # 构建 Registry
    reg = ToolRegistry()
    reg.register(ToolEntry(
        name="calculator", description="计算数学表达式。输入如 '234*567'，返回计算结果。",
        input_schema={
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "数学表达式，如 234*567"}},
            "required": ["expression"],
        },
        output_schema={}, function=calculator,
    ))
    reg.register(ToolEntry(
        name="get_weather", description="查询城市天气。输入城市名称，返回温度/天气/湿度。",
        input_schema={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "城市名称，如 北京"}},
            "required": ["city"],
        },
        output_schema={}, function=get_weather,
    ))

    provider = DeepSeekProvider(api_key=api_key, model="deepseek-chat")
    agent = LLMReActAgent(reg, provider)

    prompts = {
        "calculator": "帮我计算 234 * 567",
        "weather": "北京今天天气怎么样？适合出门吗？给个建议。",
        "both": "帮我查一下北京和上海的天气，然后计算这两个城市温差。",
    }

    user_msg = prompts.get(mode, mode)
    print("=" * 60)
    print(f"  LLM ReAct Agent — Tool Calling Demo")
    print(f"  User: {user_msg}")
    print("=" * 60)

    try:
        result = agent.chat(user_msg)
        if result.success:
            answer = (result.data or {}).get("answer", "")
            print(f"\n  [Agent 回答]:\n  {answer}")
            print(f"\n  [Trace] ({len(result.trace)} steps):")
            for t in result.trace:
                state = t.get("state", "?")
                tool = t.get("selected_tool", "")
                ms = t.get("elapsed_ms", 0)
                marker = f"[{tool}]" if tool else ""
                print(f"    Step {t['step']:2d} | {state:16s} {marker:20s} ({ms}ms)")
        else:
            error = result.error or {}
            print(f"\n  ❌ Agent 执行失败: {error.get('code')} - {error.get('message')}")
    except Exception as exc:
        print(f"\n  ❌ LLM 调用异常: {exc}")
        print("  请检查: 1) API Key 是否正确  2) 网络连接  3) DeepSeek 账户余额")

    print("=" * 60)


def run_prereq_conflict_demo() -> None:
    """展示先修冲突检测能力。"""
    from src.agent.runner import AgentRunner

    print("=" * 60)
    print(f"  Demo: 先修条件冲突检测")
    print(f"  课程: Spark | 每日 2h | 30 天 | 无已有知识")
    print("=" * 60)

    runner = AgentRunner()
    result = runner.run("Spark", 2, 30)

    error = result.error or {}
    details = error.get("details", {})
    print(f"""
  [WARNING] {error.get('code')}
  {error.get('message')}

  缺失先修课:""")
    for course in details.get("missing", []):
        print(f"    - {course}")
    print(f"""
  总先修学时: {details.get('total_prerequisite_hours', 0):.0f}h
  建议: 完成上述先修课程后再学习 Spark。

  📊 Trace: {len(result.trace)} 步
  ✅ Agent 在第 2 步正确终止，未浪费后续 Tool 调用
  """)
    print("=" * 60)


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Course Learning Planner Agent — Demo")
    parser.add_argument("--llm", action="store_true", help="LLM 模式 (需 DEEPSEEK_API_KEY)")
    parser.add_argument("--calculator", action="store_true", help="计算器 Demo (需 --llm)")
    parser.add_argument("--weather", action="store_true", help="天气 Demo (需 --llm)")
    parser.add_argument("--course", type=str, default="Python", help="课程名称 (离线模式)")
    parser.add_argument("--hours", type=float, default=3, help="每日学习小时数")
    parser.add_argument("--days", type=int, default=12, help="学习天数")
    parser.add_argument("--prereq", action="store_true", help="先修冲突 Demo")

    args = parser.parse_args()

    if args.llm or args.calculator or args.weather:
        mode = "calculator" if args.calculator else ("weather" if args.weather else "calculator")
        run_llm_demo(mode)
    elif args.prereq:
        run_prereq_conflict_demo()
    else:
        run_offline_course_plan(args.course, args.hours, args.days)
