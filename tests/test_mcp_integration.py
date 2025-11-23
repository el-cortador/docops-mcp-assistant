# tests/test_mcp_integration.py

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.config.settings import settings
from app.mcp_client import git_tools, vector_tools
from app.mcp_client.client import _clients  # type: ignore[attr-defined]


def _setup_demo_repo(base: Path, slug: str = "docops-saas") -> Path:
    repo_root = base / slug
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "billing_overview.md").write_text(
        "# Billing\n\nСервис биллинга отвечает за выставление счетов и подписки.",
        encoding="utf-8",
    )

    return repo_root


@pytest.fixture
def mcp_env(tmp_path, monkeypatch):
    demo_repos = tmp_path / "demo_repos"
    demo_repos.mkdir()
    _setup_demo_repo(demo_repos, slug="docops-saas")

    settings.paths.demo_repos_dir = demo_repos

    vector_path = tmp_path / "vector_store" / "documents.jsonl"
    os.environ["DOCOPS_VECTOR_STORE_PATH"] = str(vector_path)
    settings.paths.vector_store_path = vector_path

    # сбрасываем внутренний кэш vector_store, если он уже создавался
    _clients._vector_store = None  # type: ignore[attr-defined]

    yield {
        "demo_repos_dir": demo_repos,
        "vector_store_path": vector_path,
    }


def test_git_tools_and_vector_tools_integration(mcp_env):
    project_slug = "docops-saas"

    docs = git_tools.list_files(project_slug=project_slug, subdir="docs")
    assert any("billing_overview.md" in p for p in docs)

    content = git_tools.read_file(
        project_slug=project_slug,
        path="docs/billing_overview.md",
    )
    assert "Сервис биллинга" in content

    upsert_res = vector_tools.upsert_document(
        project_slug=project_slug,
        doc_id="docs/billing_overview.md",
        title="Billing Overview",
        text=content,
        metadata={"kind": "doc"},
    )
    assert upsert_res["status"] == "ok"

    # поиск по слову "подписки"
    hits = vector_tools.search_documents(
        project_slug=project_slug,
        query="подписки",
        limit=5,
    )
    assert len(hits) >= 1
    first = hits[0]
    assert first["doc_id"] == "docs/billing_overview.md"
    assert "подписки" in first["snippet"]
    assert first["metadata"]["kind"] == "doc"