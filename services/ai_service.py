from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI

from config import config
from logger import get_logger

logger = get_logger(__name__)

_CONTACT_ANALYSIS_PROMPT = """Analyze the following contact form submission and return a JSON with:
- "category": one of ["Collaboration", "Support", "Feedback", "Other"]
- "sentiment": one of ["positive", "neutral", "negative"]
- "suggested_reply": a short, polite response in Russian

Contact data:
Name: {name}
Email: {email}
Message: {message}
"""


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=config.deepseek.api_key,
            base_url=config.deepseek.base_url,
        )
        self.model = config.deepseek.model

    async def chat(self, message: str) -> str:
        logger.info("Sending request to DeepSeek")
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": message}],
        )
        answer = response.choices[0].message.content or ""
        logger.info("Received response from DeepSeek")
        return answer

    async def analyze_contact(self, name: str, email: str, message: str) -> dict:
        """Анализирует обращение: категория, тональность, ответ.

        Возвращает словарь с ключами category, sentiment, suggested_reply.
        При ошибке AI — fallback со значениями по умолчанию.
        """
        prompt = _CONTACT_ANALYSIS_PROMPT.format(
            name=name, email=email, message=message
        )
        try:
            logger.info("Requesting AI analysis for contact message")
            answer = await self.chat(prompt)
            import json

            result = json.loads(
                answer.strip().removeprefix("```json").removesuffix("```").strip()
            )
            return {
                "category": result.get("category", "Other"),
                "sentiment": result.get("sentiment", "neutral"),
                "suggested_reply": result.get("suggested_reply", ""),
            }
        except Exception as e:
            logger.warning("AI analysis failed, using fallback: %s", e)
            return self._fallback_analysis()

    @staticmethod
    def _fallback_analysis() -> dict:
        return {
            "category": "Other",
            "sentiment": "neutral",
            "suggested_reply": (
                "Здравствуйте! Спасибо за ваше обращение. "
                "Мы получили ваше сообщение и свяжемся с вами в ближайшее время."
            ),
        }


AIServiceDep = Annotated[AIService, Depends(AIService)]
