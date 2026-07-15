"""
LLM Provider 抽象层。

提供统一的 LLMProvider 接口。
当前实现: DeepSeekProvider (OpenAI Compatible API)
"""

from src.providers.base import LLMProvider, LLMResponse, ToolCall
from src.providers.deepseek_provider import DeepSeekProvider

__all__ = ["LLMProvider", "LLMResponse", "ToolCall", "DeepSeekProvider"]
