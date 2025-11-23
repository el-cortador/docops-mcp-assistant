# app/ui/callbacks.py

# Колбэки UI для обработки действий пользователя в Gradio

from __future__ import annotations

from typing import List, Dict, Any

from app.agent.agent import DocOpsAgent, ProjectContext


def _make_agent(project_slug: str) -> DocOpsAgent:
    # Внутренний хелпер: создает DocOpsAgent для указанного slug проекта

    project = ProjectContext(slug=project_slug)
    agent = DocOpsAgent(project=project)
    return agent


def format_sources_markdown(sources: List[Dict[str, Any]]) -> str:
    # Форматирует список источников в markdown для отображения в UI

    if not sources:
        return "_Sources not found or not explicitly used._"

    lines = ["**What I used:**", ""]
    for src in sources:
        path = src.get("path", "")
        snippet = src.get("snippet", "")
        lines.append(f"- `{path}` — {snippet}")
    return "\n".join(lines)

def on_ask_question(
    project_slug: str,
    question: str,
) -> tuple[str, str]:
    # Колбэк обработки запроса Q&A: создает агента, отвечает на вопрос и возвращает ответ и источники

    if not question.strip():
        return "It appears the question is empty - please try to formulate it a bit more detailed.", ""

    agent = _make_agent(project_slug)
    result = agent.answer_question(question=question)

    answer = result.get("answer", "")
    sources = result.get("sources") or []

    sources_md = format_sources_markdown(sources)

    return answer, sources_md