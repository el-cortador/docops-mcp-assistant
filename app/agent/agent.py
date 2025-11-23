# app/agent/agent.py

# Главный модуль ассистента, содержит класс DocOpsAgent для обработки вопросов и ответов по доке

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.agent import workflows


@dataclass
class ProjectContext:
    # Контекст проекта, с которым работает агент (slug, имя, описание)
    slug: str
    name: Optional[str] = None
    description: Optional[str] = None


class DocOpsAgent:
    # Основной класс агента для работы с документацией (Q&A)
    def __init__(
        self,
        project: ProjectContext,
        *,
        model: str | None = None,
    ) -> None:
        # Инициализирует агента с контекстом проекта и опциональной моделью LLM
        self.project = project
        self.model = model

    def answer_question(self, question: str) -> dict:
        # Отвечает на вопросы по документации
        qa_result = workflows.qa_over_docs(
            project_slug=self.project.slug,
            question=question,
            model=self.model,
        )
        return {
            "answer": qa_result.answer,
            "sources": qa_result.sources,
        }

