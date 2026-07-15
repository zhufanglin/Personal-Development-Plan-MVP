"""
DeepSeek Provider — 通过 OpenAI Compatible API 调用 DeepSeek。

使用 openai 包，设置 base_url 指向 DeepSeek API。
包含完整的异常处理: 网络错误、认证失败、速率限制、超时。
"""

from typing import Any

from openai import (
    APIError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
    OpenAI,
)

from src.providers.base import LLMProvider, LLMResponse, ToolCall


class ProviderError(Exception):
    """LLM Provider 调用异常。"""

    def __init__(self, message: str, code: str = "PROVIDER_ERROR", details: dict | None = None) -> None:
        super().__init__(message)
        self.code: str = code
        self.details: dict | None = details


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM Provider。

    使用 OpenAI SDK + DeepSeek base_url 实现。
    DeepSeek 完全兼容 OpenAI chat/completions API。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        **kwargs: Any,
    ) -> None:
        """初始化 DeepSeek Provider。

        Args:
            api_key: DeepSeek API Key
            model: 模型名称（deepseek-chat / deepseek-reasoner）
            base_url: API 地址
            **kwargs: 其他 OpenAI 兼容参数（temperature, max_tokens 等）
        """
        super().__init__(model=model, api_key=api_key, **kwargs)
        self._client: OpenAI = OpenAI(api_key=api_key, base_url=base_url)
        self._temperature: float = float(kwargs.get("temperature", 0.0))
        self._max_tokens: int = int(kwargs.get("max_tokens", 4096))

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """调用 DeepSeek Chat API。

        Args:
            messages: 对话历史
            tools: OpenAI Function Calling schema（可选）
            **kwargs: 覆盖默认 temperature/max_tokens

        Returns:
            LLMResponse: 统一响应格式
        """
        params: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self._temperature),
            "max_tokens": kwargs.get("max_tokens", self._max_tokens),
        }

        if tools:
            params["tools"] = tools

        try:
            response = self._client.chat.completions.create(**params)
        except AuthenticationError as exc:
            raise ProviderError(
                f"DeepSeek API 认证失败。请检查 DEEPSEEK_API_KEY 是否正确。",
                code="AUTH_ERROR",
                details={"exception": str(exc)},
            ) from exc
        except RateLimitError as exc:
            raise ProviderError(
                f"DeepSeek API 速率限制。请稍后重试。",
                code="RATE_LIMIT",
                details={"exception": str(exc)},
            ) from exc
        except APITimeoutError as exc:
            raise ProviderError(
                f"DeepSeek API 请求超时。请检查网络连接。",
                code="TIMEOUT",
                details={"exception": str(exc)},
            ) from exc
        except APIError as exc:
            raise ProviderError(
                f"DeepSeek API 错误: {exc}",
                code="API_ERROR",
                details={"exception": str(exc)},
            ) from exc
        except Exception as exc:
            raise ProviderError(
                f"DeepSeek Provider 未知错误: {exc}",
                code="PROVIDER_ERROR",
                details={"exception": str(exc)},
            ) from exc

        return self._parse_response(response)

    def _parse_response(self, response: Any) -> LLMResponse:
        """将 OpenAI SDK 响应转换为 LLMResponse。"""
        choice = response.choices[0]
        message = choice.message
        finish: str = choice.finish_reason or "stop"

        tool_calls: list[ToolCall] = []
        if message.tool_calls:
            finish = "tool_calls"
            for tc in message.tool_calls:
                import json as _json
                try:
                    args = _json.loads(tc.function.arguments)
                except (_json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))

        usage: dict[str, int] = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens or 0,
                "completion_tokens": response.usage.completion_tokens or 0,
                "total_tokens": response.usage.total_tokens or 0,
            }

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=finish,
            usage=usage,
            raw_response=response,
        )
