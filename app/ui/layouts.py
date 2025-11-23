# app/ui/layouts.py

from __future__ import annotations

import gradio as gr

from app.ui import components
from app.ui import callbacks


def build_app() -> gr.Blocks:
    # Собирает и возвращает основной интерфейс Gradio, содержащий только Q&A-вкладку

    with gr.Blocks(title="DocOps MCP Assistant") as demo:
        gr.Markdown(
            """
# DocOps MCP-ассистент

_Демо-версия ИИ-агента для работы с документацией из базы знаний через MCP-сервисы._
"""
        )

        with gr.Tabs():
            with gr.Tab("Q&A по системе"):
                # Set up Q&A tab with its components and event handlers
                (
                    qa_project_dd,
                    qa_question_input,
                    qa_ask_btn,
                    qa_answer_md,
                    qa_sources_md,
                ) = components.qa_tab_components()

                # Connect the Q&A button click event to the appropriate callback
                qa_ask_btn.click(
                    fn=callbacks.on_ask_question,
                    inputs=[qa_project_dd, qa_question_input],
                    outputs=[qa_answer_md, qa_sources_md],
                )

    return demo