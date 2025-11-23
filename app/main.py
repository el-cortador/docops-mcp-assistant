# app/main.py

from __future__ import annotations

import os

from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from fastapi import FastAPI
import uvicorn

from app.core import logging as _logging  # noqa: F401
from app.ui.layouts import build_app

def _resolve_gradio_theme() -> object | None:
    # Определяет тему Gradio по переменным окружения и возвращает соответствующий объект темы

    theme_name = os.getenv("GRADIO_THEME") or os.getenv("DOCOPS_GRADIO_THEME")
    if not theme_name:
        return None

    theme_name = theme_name.lower().strip()

    # Сравнивает названия темы с одной из стандартных тем Gradio
    try:
        mapping = {
            "default": gr.themes.Default,
            "soft": gr.themes.Soft,
            "monochrome": gr.themes.Monochrome,
            "glass": gr.themes.Glass,
        }
    except Exception:
        return None

    theme_cls = mapping.get(theme_name)
    if theme_cls is None:
        try:
            return gr.themes.Default()
        except Exception:
            return None

    try:
        return theme_cls()
    except Exception:
        return None

# Создает приложение на FastAPI с интерфейсом Gradio
def create_fastapi_app() -> FastAPI:
    
    # Создает интерфейс Gradio
    blocks: gr.Blocks = build_app()

    # Устанавливает тему
    theme = _resolve_gradio_theme()
    if theme is not None:
        try:
            blocks.theme = theme
        except Exception:
            pass

    fastapi_app = FastAPI(title="DocOps MCP Assistant")

    @fastapi_app.get("/healthz")
    async def healthcheck():
        # Проверка состояния приложения
        return {"status": "ok"}

    fastapi_app = gr.mount_gradio_app(
        fastapi_app,
        blocks,
        path="/",
    )

    return fastapi_app


# ASGI-приложение, пригодное для uvicorn/Hypercorn и т.п.
app: FastAPI = create_fastapi_app()


def main() -> None:
    # Запуск сервера

    host = os.getenv("DOCOPS_GRADIO_HOST", "0.0.0.0")
    raw_port = os.getenv("DOCOPS_GRADIO_PORT", "7860")

    # пнх, кавычки и пробелы
    raw_port = str(raw_port).strip().strip('"').strip("'")

    try:
        port = int(raw_port)
    except ValueError:
        # fallback, если окружение сломано
        port = 7860

    uvicorn.run(
        app,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()