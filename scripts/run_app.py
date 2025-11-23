# scripts/run_app.py

from __future__ import annotations

import os

import gradio as gr

from app.ui.layouts import build_app


def main() -> None:
    app: gr.Blocks = build_app()

    # Порт и host можно переопределить через ENV
    port = int(os.getenv("DOCOPS_GRADIO_PORT", "7860"))
    server_name = os.getenv("DOCOPS_GRADIO_HOST", "0.0.0.0")

    app.launch(
        server_name=server_name,
        server_port=port,
        show_api=False,
        share=False,  # при необходимости можно включить
    )


if __name__ == "__main__":
    main()