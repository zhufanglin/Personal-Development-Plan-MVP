"""
Demo Tools — 答辩演示用的简单工具。

calculator: 数学计算
weather: 天气查询（模拟）

这些工具注册到 ToolRegistry 后，LLM Agent 可动态调用它们。
演示 LLM 的通用 Tool Calling 能力，不限于课程规划场景。
"""


def calculator(expression: str) -> dict:
    """安全地计算数学表达式。

    使用 Python eval 的受限子集，仅支持基本算术运算。

    Args:
        expression: 数学表达式字符串，如 "234 * 567"

    Returns:
        {"success": true, "data": {"expression": str, "result": float}}
    """
    if not expression or not isinstance(expression, str):
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "expression 必须是非空字符串。",
                "details": {},
                "tool_name": "calculator",
            },
        }

    # 安全校验: 仅允许数字、运算符、空格、括号、小数点
    allowed: set[str] = set("0123456789+-*/.()% ")
    cleaned: str = expression.strip().replace("x", "*").replace("X", "*").replace("×", "*").replace("÷", "/")

    for ch in cleaned:
        if ch not in allowed:
            return {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"表达式包含不允许的字符: '{ch}'。仅支持基本算术运算。",
                    "details": {"expression": expression, "invalid_char": ch},
                    "tool_name": "calculator",
                },
            }

    try:
        result: float = eval(cleaned, {"__builtins__": {}}, {})
        return {
            "success": True,
            "data": {
                "expression": expression.strip(),
                "result": result,
            },
        }
    except Exception as exc:
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": f"计算失败: {exc}",
                "details": {"expression": expression},
                "tool_name": "calculator",
            },
        }


def get_weather(city: str) -> dict:
    """查询城市天气（模拟数据，用于演示）。

    实际生产环境中，此函数会调用真实天气 API。

    Args:
        city: 城市名称，如 "北京"

    Returns:
        {"success": true, "data": {"city": str, "temperature": int, "condition": str, "humidity": int}}
    """
    if not city or not isinstance(city, str):
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "city 必须是非空字符串。",
                "details": {},
                "tool_name": "get_weather",
            },
        }

    # 模拟天气数据
    city_lower: str = city.strip().lower()
    weather_map: dict[str, dict] = {
        "北京": {"temperature": 32, "condition": "晴", "humidity": 45},
        "上海": {"temperature": 29, "condition": "多云", "humidity": 70},
        "广州": {"temperature": 35, "condition": "雷阵雨", "humidity": 85},
        "深圳": {"temperature": 33, "condition": "多云转晴", "humidity": 65},
        "杭州": {"temperature": 30, "condition": "小雨", "humidity": 75},
        "成都": {"temperature": 27, "condition": "阴", "humidity": 80},
    }

    for key, data in weather_map.items():
        if key in city or city in key:
            return {
                "success": True,
                "data": {
                    "city": key,
                    **data,
                },
            }

    # 未匹配 → 返回默认数据
    return {
        "success": True,
        "data": {
            "city": city.strip(),
            "temperature": 28,
            "condition": "晴间多云",
            "humidity": 55,
        },
    }
