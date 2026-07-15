"""
Tool Calling Adapter。

将 ToolRegistry 中注册的 Tool 转换为 OpenAI Function Calling schema。
不修改 ToolRegistry — 只读取 list_tools() 元数据并转换格式。
"""

from typing import Any


def to_openai_tools(registry: Any) -> list[dict[str, Any]]:
    """将 ToolRegistry 中所有 Tool 转换为 OpenAI Function Calling 格式。

    Args:
        registry: ToolRegistry 实例（需有 list_tools() 方法）

    Returns:
        list[dict]: OpenAI-compatible tools schema
    """
    tools: list[dict[str, Any]] = []
    for tool in registry.list_tools():
        tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    return tools
