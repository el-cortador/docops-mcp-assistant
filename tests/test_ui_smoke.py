# tests/test_ui_smoke.py

from __future__ import annotations

import gradio as gr

from app.ui.layouts import build_app


def test_build_app_returns_blocks():
    app = build_app()
    assert isinstance(app, gr.Blocks)


def test_build_app_config_smoke():
    app = build_app()
    # вызов .config() должен отработать без исключений
    cfg = app.config
    assert isinstance(cfg, dict)
    assert "dependencies" in cfg