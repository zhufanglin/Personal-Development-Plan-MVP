"""
LLMReActAgent — 基于 LLM 的 ReAct Agent。

替代 RuleBasedReActAgent，使用 LLM 动态决定 Tool 调用。
保持相同的 run() 接口，与 AgentRunner 完全兼容。
"""

import json
import time
from typing import Any

from src.agent.prompt_loader import PromptLoader
from src.agent.react_loop import ReActResult, TraceEntry
from src.agent.tool_adapter import to_openai_tools
from src.agent.tool_registry import ToolRegistry
from src.providers.base import LLMProvider, LLMResponse


class LLMReActAgent:
    """LLM 驱动的 ReAct Agent。

    使用 LLM Provider 动态推理 + Tool Calling，
    替代硬编码的 EXECUTION_PLAN。

    使用方式:
        agent = LLMReActAgent(registry, provider, prompt_loader)
        result = agent.run("Python", 3, 12)             # 课程规划
        result = agent.chat("帮我计算 234*567")          # 通用对话
    """

    MAX_TOOL_ROUNDS: int = 10  # 防止死循环

    def __init__(
        self,
        registry: ToolRegistry,
        provider: LLMProvider,
        prompt_loader: PromptLoader | None = None,
    ) -> None:
        """初始化 LLM ReAct Agent。

        Args:
            registry: ToolRegistry 实例
            provider: LLM Provider（如 DeepSeekProvider）
            prompt_loader: PromptLoader（可选，课程规划时需要）
        """
        self.registry: ToolRegistry = registry
        self.provider: LLMProvider = provider
        self.prompt_loader: PromptLoader = prompt_loader or PromptLoader()

    # ── 课程规划模式（兼容 AgentRunner） ──────────────

    def run(
        self,
        course_name: str,
        daily_hours: float,
        duration_days: int,
        user_knowledge: list[str] | None = None,
    ) -> ReActResult:
        """课程学习规划（与 RuleBasedReActAgent 相同接口）。

        构建系统提示词 → LLM 推理 → Tool Calling → 返回计划。
        """
        knowledge: list[str] = list(user_knowledge or [])

        # 构建系统消息
        system_prompt: str = self.prompt_loader.load(
            tool_registry=self.registry,
            workflow=(
                "Step 1: get_course_info → Step 2: get_prerequisite → "
                "Step 3: calculate_learning_time → Step 4: generate_learning_plan"
            ),
        )

        user_msg: str = (
            f"请为以下课程规划学习路径:\n"
            f"- 课程: {course_name}\n"
            f"- 每日学习时间: {daily_hours} 小时\n"
            f"- 学习周期: {duration_days} 天\n"
            f"- 已完成的课程: {', '.join(knowledge) if knowledge else '（无）'}"
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        return self._run_loop(messages)

    # ── 通用对话模式（Demo 工具） ────────────────────

    def chat(self, user_message: str) -> ReActResult:
        """通用对话模式。

        LLM 自主决定调用哪些 Tool，适用于 calculator/weather 等 demo。
        """
        system_prompt: str = (
            "你是一个有用的 AI 助手。你可以使用工具来完成用户的请求。\n"
            "当用户提出需要工具才能完成的任务时，请调用相应的工具。\n"
            "当你获得工具返回的结果后，用中文给出清晰、友好的回答。\n"
            "当前日期: 2026-07-11。"
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        return self._run_loop(messages)

    # ── 核心 ReAct 循环 ──────────────────────────────

    def _run_loop(self, messages: list[dict[str, Any]]) -> ReActResult:
        """ReAct 主循环: LLM → Tool → Observation → 循环。

        Args:
            messages: 初始消息列表 (system + user)

        Returns:
            ReActResult(success, data/error, trace)
        """
        trace: list[TraceEntry] = []
        step: int = 0
        tools_schema: list[dict[str, Any]] = to_openai_tools(self.registry)

        for _ in range(self.MAX_TOOL_ROUNDS):
            # 调用 LLM
            t0: float = time.perf_counter()
            response: LLMResponse = self.provider.chat(messages, tools_schema)
            elapsed: int = round((time.perf_counter() - t0) * 1000)

            # 记录 trace
            step += 1
            trace.append(TraceEntry(
                step=step,
                state="LLM_CALL",
                thought=f"LLM response: finish_reason={response.finish_reason}",
                tool_output={
                    "finish_reason": response.finish_reason,
                    "has_content": response.content is not None,
                    "tool_call_count": len(response.tool_calls),
                },
                elapsed_ms=elapsed,
            ))

            # 无 tool_calls → LLM 返回最终答案
            if not response.tool_calls:
                step += 1
                trace.append(TraceEntry(step=step, state="RESPONSE"))
                return ReActResult(
                    success=True,
                    data={"answer": response.content or ""},
                    trace=[t.to_dict() for t in trace],
                )

            # 执行 tool_calls
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {
                        "id": tc.id or f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for i, tc in enumerate(response.tool_calls)
                ],
            }
            messages.append(assistant_msg)

            for i, tc in enumerate(response.tool_calls):
                step += 1
                t0 = time.perf_counter()
                result: dict = self.registry.invoke(tc.name, **tc.arguments)
                tool_elapsed: int = round((time.perf_counter() - t0) * 1000)

                trace.append(TraceEntry(
                    step=step,
                    state="TOOL_EXECUTION",
                    selected_tool=tc.name,
                    tool_input=tc.arguments,
                    tool_output={"success": result.get("success")},
                    elapsed_ms=tool_elapsed,
                ))

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id or f"call_{i}",
                    "content": json.dumps(result, ensure_ascii=False),
                })

                # 检查阻断条件
                data: dict = result.get("data", {})
                if isinstance(data, dict):
                    if data.get("satisfied") is False:
                        return ReActResult(
                            success=False,
                            error={
                                "code": "PREREQUISITE_CONFLICT",
                                "message": f"先修条件不满足: 缺少 {len(data.get('missing', []))} 门课。",
                                "details": data,
                            },
                            trace=[t.to_dict() for t in trace],
                        )
                    if data.get("feasible") is False:
                        return ReActResult(
                            success=False,
                            error={
                                "code": "TIME_INSUFFICIENT",
                                "message": f"学习时间不足。",
                                "details": data,
                            },
                            trace=[t.to_dict() for t in trace],
                        )

        # 达到最大轮次
        step += 1
        trace.append(TraceEntry(step=step, state="RESPONSE",
                                thought="达到最大 Tool 调用轮次，强制终止。"))
        return ReActResult(
            success=False,
            error={"code": "MAX_ROUNDS", "message": f"超过最大轮次 {self.MAX_TOOL_ROUNDS}"},
            trace=[t.to_dict() for t in trace],
        )
