import httpx
from typing import Optional
from app.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_API_BASE_URL
        self.model = settings.AI_MODEL

    async def chat(self, messages: list, system_prompt: Optional[str] = None, temperature: float = 0.7) -> str:
        if not self.api_key:
            return ""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": full_messages,
                    "temperature": temperature
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def analyze_assessment_result(self, assessment_type: str, responses: list[dict], questions: list[dict]) -> dict:
        system_prompt = "你是一名大学生发展评估专家。请根据测评数据生成分析结果。"
        user_msg = f"测评类型: {assessment_type}\n题目与回答: {responses}"
        result = await self.chat(
            messages=[{"role": "user", "content": user_msg}],
            system_prompt=system_prompt
        )
        return {"ai_analysis": result}

ai_service = AIService()
