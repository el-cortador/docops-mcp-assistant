# app/agent/workflows.py

# Модуль с базовой логикой DocOps-ассистента — сейчас содержит только функции для ответов на вопросы

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from app.core.llm import chat as llm_chat
from app.agent import prompts
from app.mcp_client import git_tools, vector_tools

@dataclass
class QAResult:
    # Результат работы QA-воркфлоу: содержит ответ и список использованных источников

    answer: str
    sources: List[Dict[str, Any]]  # например, [{path, snippet}, ...]


def qa_over_docs(
    project_slug: str,
    question: str,
    max_docs: int = 5,
    model: Optional[str] = None,
    max_chars_per_doc: int = 2000,
) -> QAResult:
    # Отвечает на вопрос по документации проекта: ищет релевантные материалы, извлекает фрагменты и генерирует ответ через LLM
    # 1. Ищем по Git-докам
    git_results = git_tools.search_in_docs(
        project_slug=project_slug,
        query=question,
        max_results=max_docs,
    )

    # 2. Ищем по векторному стораджу (если есть)
    try:
        vector_results = vector_tools.search_documents(
            project_slug=project_slug,
            query=question,
            limit=max_docs,
        )
    except Exception:
        vector_results = []

    # 3. Собираем контекст
    context_blocks: List[str] = []
    sources: List[Dict[str, Any]] = []

    def _add_source(path: str, snippet: str, kind: str) -> None:
        sources.append(
            {
                "path": path,
                "snippet": snippet[:max_chars_per_doc],
                "kind": kind,
            }
        )
        context_blocks.append(
            f"[{kind}] {path}\n{snippet[:max_chars_per_doc]}\n"
        )

    for r in git_results:
        _add_source(
            path=r.get("path", "unknown"),
            snippet=r.get("snippet", ""),
            kind="git",
        )

    for r in vector_results:
        _add_source(
            path=r.get("path", r.get("id", "vector-doc")),
            snippet=r.get("snippet", r.get("text", "")),
            kind="vector",
        )

    # 4. Если вообще НИЧЕГО не нашли — все равно спрашиваем LLM,
    #    но явно говорим, что специализированного контекста нет.
    if not context_blocks:
        system_msg = {
            "role": "system",
            "content": prompts.QA_SYSTEM_PROMPT_NO_CONTEXT,
        }
        user_msg = {
            "role": "user",
            "content": (
                "Вопрос пользователя:\n"
                f"{question}\n\n"
                "У тебя нет доступа к документации по этому проекту. "
                "Ответь общими словами и обязательно честно скажи, что "
                "не нашел соответствующую документацию."
            ),
        }
        answer_text = llm_chat(
            messages=[system_msg, user_msg],
            model=model,
        )
        return QAResult(answer=answer_text, sources=[])

    # 5. Нормальный случай: контекст есть
    context_str = "\n\n---\n\n".join(context_blocks)

    system_msg = {
        "role": "system",
        "content": prompts.QA_SYSTEM_PROMPT_WITH_CONTEXT,
    }
    user_msg = {
        "role": "user",
        "content": (
            "Вопрос пользователя:\n"
            f"{question}\n\n"
            "Ниже — фрагменты документации и/или кода, которые могут помочь:\n"
            "----------------------------------------\n"
            f"{context_str}"
        ),
    }

    answer_text = llm_chat(
        messages=[system_msg, user_msg],
        model=model,
    )

    return QAResult(answer=answer_text, sources=sources)
