# conftest.py

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent

MCP_CONFLUENCE_ROOT = ROOT / "mcp-servers" / "confluence-mcp-server"
MCP_GIT_ROOT = ROOT / "mcp-servers" / "git-mcp-server"
MCP_VECTOR_ROOT = ROOT / "mcp-servers" / "vector-mcp-server"

for p in (MCP_CONFLUENCE_ROOT, MCP_GIT_ROOT, MCP_VECTOR_ROOT):
    if p.exists():
        sys.path.append(str(p))

@pytest.fixture(scope="session", autouse=True)
def _test_env_defaults():
    os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

    os.environ.setdefault("CONFLUENCE_BASE_URL", "https://confluence-test.local")
    os.environ.setdefault("CONFLUENCE_EMAIL", "test@example.com")
    os.environ.setdefault("CONFLUENCE_API_TOKEN", "test-token")

    os.environ.setdefault("DOCOPS_GRADIO_HOST", "127.0.0.1")
    os.environ.setdefault("DOCOPS_GRADIO_PORT", "7860")

    # фикстура session-scope, ничего возвращать не нужно
    yield