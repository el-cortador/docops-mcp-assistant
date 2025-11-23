# app/agent/workflows.py

# Модуль с базовой логикой DocOps-ассистента — сейчас содержит только функции для ответов на вопросы

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from app.core.llm import chat as llm_chat
from app.agent import prompts
from app.mcp_client import git_tools


@dataclass
class QAResult:
    # Результат работы QA-воркфлоу: содержит ответ и список использованных источников

    answer: str
    sources: List[Dict[str, Any]]  # например, [{path, snippet}, ...]



def qa_over_docs(
    project_slug: str,
    question: str,
    *,
    max_docs: int = 5,
    model: str | None = None,
    max_chars_per_doc: int = 2000,
) -> QAResult:
    # Отвечает на вопрос: ищет материалы, извлекает фрагменты и генерит ответ через LLM

    # Поиск документации
    hits = git_tools.search_in_docs(
        project_slug=project_slug,
        query=question,
        max_results=max_docs,
    )

    context_chunks: List[str] = []
    used_sources: List[Dict[str, Any]] = []

    for hit in hits:
        path = hit.get("path")
        if not path:
            continue

        content = git_tools.read_file(
            project_slug=project_slug,
            path=path,
        )
        truncated = content[:max_chars_per_doc]

        context_chunks.append(
            f"### {path}\n{truncated}\n"
        )
        used_sources.append(
            {
                "path": path,
                "snippet": hit.get("snippet", ""),
            }
        )

    if not context_chunks:
        # Если контекст не найден, все равно вызывает LLM, но явно сообщает об отсутствии данных
        context = "Context not found: search query did not yield matches in documentation."
    else:
        context = "\n\n".join(context_chunks)

    system_msg = {"role": "system", "content": prompts.QUESTION_ANSWER_SYSTEM_PROMPT}
    user_msg = {
        "role": "user",
        "content": prompts.build_qa_user_prompt(question=question, context=context),
    }

    answer = llm_chat(
        messages=[system_msg, user_msg],
        model=model,
    )

    return QAResult(answer=answer, sources=used_sources)


