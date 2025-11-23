# mcp-servers/git-mcp-server/mcp_git/tests/test_server.py

from pathlib import Path

import pytest

from mcp_git.server import list_files, read_file, search_in_docs


def _setup_demo_repo(tmp_path: Path, slug: str = "demo-proj") -> Path:
    repo_root = tmp_path / slug
    docs_dir = repo_root / "docs"
    code_dir = repo_root / "services" / "billing"

    docs_dir.mkdir(parents=True)
    code_dir.mkdir(parents=True)

    (repo_root / "README.md").write_text("# Demo Repo\n", encoding="utf-8")
    (docs_dir / "billing_overview.md").write_text(
        "# Billing\n\nСервис биллинга отвечает за выставление счетов.",
        encoding="utf-8",
    )
    (code_dir / "main.py").write_text(
        "def create_invoice():\n    return {'status': 'ok'}\n",
        encoding="utf-8",
    )

    return repo_root


@pytest.fixture(autouse=True)
def demo_repos_env(monkeypatch, tmp_path):
    base = tmp_path / "demo_repos"
    base.mkdir()
    _setup_demo_repo(base, slug="demo-proj")
    monkeypatch.setenv("DOCOPS_DEMO_REPOS_DIR", str(base))
    return base


def test_list_files_returns_files_for_subdir():
    files = list_files(project_slug="demo-proj", subdir="docs")
    assert any(f.endswith("billing_overview.md") for f in files)
    assert all("/" in f or f.endswith(".md") for f in files)


def test_read_file_reads_markdown():
    content = read_file(
        project_slug="demo-proj",
        path="docs/billing_overview.md",
    )
    assert "Сервис биллинга" in content


def test_search_in_docs_finds_query():
    results = search_in_docs(
        project_slug="demo-proj",
        query="биллинга",
        docs_subdir="docs",
        max_results=3,
    )
    assert len(results) >= 1
    first = results[0]
    assert first["path"].endswith("billing_overview.md")
    assert "биллинга" in first["snippet"]


def test_list_files_invalid_subdir_returns_empty():
    files = list_files(project_slug="demo-proj", subdir="unknown-dir")
    assert files == []