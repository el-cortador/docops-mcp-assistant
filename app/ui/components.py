# app/ui/components.py

from __future__ import annotations

from typing import List, Tuple

import gradio as gr


def project_dropdown(
    label: str = "Проект",
    value: str | None = None,
) -> gr.Dropdown:
    # Создает выпадающий список для выбора демо-проекта (доступны два предустановленных варианта)

    choices: List[Tuple[str, str]] = [
        ("DocOps SaaS Platform", "docops-saas"),
        ("Airport Food Delivery", "airport-food"),
    ]

    return gr.Dropdown(
        label=label,
        choices=[c[1] for c in choices],
        value=value or "docops-saas",
        info="Выберите демо-проект, на вопросы по которому должен отвечать агент",
    )


def sources_markdown(label: str = "Использованные источники") -> gr.Markdown:
    # Создает markdown-компонент для отображения источников

    return gr.Markdown(value="", label=label)


def qa_tab_components():
    # Создает набор UI-компонентов для вкладки Q&A: выбор проекта, ввод вопроса и вывод ответа

    project_dd = project_dropdown()

    question_input = gr.Textbox(
        label="Вопрос по системе/документации",
        placeholder="Например: Какая архитектура у биллингового сервиса?",
        lines=3,
    )

    ask_btn = gr.Button("Задать вопрос")

    answer_md = gr.Markdown(label="Ответ")
    sources_md = sources_markdown()

    return project_dd, question_input, ask_btn, answer_md, sources_md