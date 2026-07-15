"""
LLM Provider 抽象层。

定义 LLMProvider 统一接口和 LLMResponse/ToolCall 数据结构。
所有 Provider 实现（DeepSeek/OpenAI/Claude）必须继承 LLMProvider。

Agent 层只依赖此接口，不感知具体模型厂商。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """LLM 请求调用单个 Tool 的数据结构。

    屏蔽不同 Provider（OpenAI/Anthropic）的 Tool Call 格式差异。
    """

    name: str
    """Tool 名称，对应 ToolRegistry 中注册的 name。"""

    arguments: dict[str, Any]
    """Tool 调用参数，已从 JSON 字符串解析为 dict。"""

    id: str | None = None
    """Tool Call 唯一 ID。

    用于并行 tool_calls 场景下关联 assistant 消息和 tool 结果。
    OpenAI: tool_calls[].id
    Anthropic: tool_use.id
    单次调用时可留空。
    """


@dataclass
class LLMResponse:
    """LLM 的统一响应格式。

    所有 Provider 的 chat() 方法必须返回此类型，
    无论底层是 OpenAI SDK / Anthropic SDK / HTTP API。
    """

    content: str | None = None
    """LLM 的文本回复。

    - 当 finish_reason="stop" 时，包含 Final Answer
    - 当 finish_reason="tool_calls" 时，通常为 None（LLM 只返回 tool_calls）
    - 部分模型可能同时返回 content 和 tool_calls
    """

    tool_calls: list[ToolCall] = field(default_factory=list)
    """LLM 请求的 Tool 调用列表。

    空列表表示 LLM 未请求任何 Tool 调用（应返回 Final Answer）。
    """

    finish_reason: str = "stop"
    """完成原因。

    常见值:
    - "stop": LLM 完成文本回复
    - "tool_calls": LLM 请求 Tool 调用
    - "length": 达到 token 上限
    """

    usage: dict[str, int] = field(default_factory=dict)
    """Token 使用量。

    格式: {"prompt_tokens": N, "completion_tokens": M, "total_tokens": T}
    """

    raw_response: Any = None
    """Provider 原始响应对象。

    用于调试和 Provider 特定信息访问。
    Agent 层不应依赖此字段。
    """


class LLMProvider(ABC):
    """LLM Provider 抽象基类。

    定义统一的 chat() 接口。
    所有具体 Provider 实现必须继承此类。

    使用方式:
        provider = DeepSeekProvider(model="deepseek-chat", api_key="sk-...")
        response = provider.chat(messages=[...], tools=[...])
        if response.tool_calls:
            for call in response.tool_calls:
                result = registry.invoke(call.name, **call.arguments)
    """

    def __init__(self, model: str, api_key: str, **kwargs: Any) -> None:
        """初始化 Provider。

        Args:
            model: 模型名称（如 "deepseek-chat", "gpt-4o", "claude-fable-5"）
            api_key: API 密钥
            **kwargs: Provider 特定配置（如 base_url, temperature 等）
        """
        self.model: str = model
        self.api_key: str = api_key
        self._config: dict[str, Any] = kwargs

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """发送对话到 LLM 并返回统一格式响应。

        Args:
            messages: 对话历史列表。
                      格式: [{"role": "system"|"user"|"assistant"|"tool",
                              "content": str | None,
                              "tool_calls": [...] | None,
                              "tool_call_id": str | None}, ...]
            tools: OpenAI-compatible function calling schema。
                   格式: [{"type": "function",
                           "function": {"name": str,
                                        "description": str,
                                        "parameters": dict}}, ...]
                   None 表示不提供 Tool（纯文本对话）。
            **kwargs: Provider 特定参数（如 temperature, max_tokens 等）。

        Returns:
            LLMResponse: 统一格式的响应，包含 content 或 tool_calls。

        Raises:
            ProviderError: LLM 调用失败时抛出（由子类定义）。
        """
        ...
