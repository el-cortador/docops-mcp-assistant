# app/core/llm.py

# Интеграция LLM через OpenAI API

from __future__ import annotations

from typing import List, Dict, Any, Optional
import os

from openai import OpenAI

from app.config.settings import settings


# Инициализация клиента
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    # Создает инстанс для OpenAI клиента

    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Explicit error to make it clear what's wrong
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Set it in .env or environment."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _extract_content_from_choice(choice: Any) -> str:
    # Извлекает данные из chat completion
    
    message = choice.message

    # Новый SDK: объект с атрибутом .content
    if hasattr(message, "content"):
        return message.content  # type: ignore[return-value]

    # Fallback: если возвращает dict (например, в моках)
    if isinstance(message, dict):
        return message.get("content", "")

    # Строковое представление
    return str(message)


def chat(
    messages: List[Dict[str, Any]],
    *,
    model: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.2,
) -> str:
    # Отправляет запрос к LLM и получает ответ
    
    client = get_client()
    model_name = model or settings.llm.model

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if not completion.choices:
        return ""

    choice = completion.choices[0]
    return _extract_content_from_choice(choice)
