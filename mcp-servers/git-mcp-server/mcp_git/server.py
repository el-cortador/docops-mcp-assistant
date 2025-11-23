# mcp-servers/git-mcp-server/mcp_git/server.py
from pathlib import Path
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("docops-git")


def get_demo_repos_dir() -> Path:
    import os

    env_path = os.getenv("DOCOPS_DEMO_REPOS_DIR")
    if env_path:
        return Path(env_path).expanduser().resolve()

    # Путь вида: <root>/mcp-servers/git-mcp-server/mcp_git/server.py
    # root = parents[4]
    root = Path(__file__).resolve().parents[4]
    return root / "demo_data" / "demo_repos"


def _project_root(project_slug: str) -> Path:
    base = get_demo_repos_dir()
    root = base / project_slug
    if not root.exists():
        raise FileNotFoundError(f"Project repo not found for slug={project_slug}")
    return root


@mcp.tool()
def list_files(project_slug: str, subdir: str = "") -> List[str]:
    root = _project_root(project_slug)
    target = (root / subdir).resolve()

    if not target.exists():
        return []

    if not str(target).startswith(str(root)):
        raise ValueError("subdir must stay inside project root")

    files: List[str] = []
    for p in target.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            files.append(rel)
    return files


@mcp.resource("repo://{project_slug}/{path}")
def read_file(project_slug: str, path: str) -> str:
    """
    [Не проверено]
    Простой ресурс: прочитать файл по относительному пути из корня репо.
    Используй для загрузки README, docs и т.п. в контекст модели.
    """
    root = _project_root(project_slug)
    fpath = (root / path).resolve()

    if not str(fpath).startswith(str(root)):
        raise ValueError("Path escapes project root")

    if not fpath.exists() or not fpath.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    return fpath.read_text(encoding="utf-8")


@mcp.tool()
def search_in_docs(
    project_slug: str,
    query: str,
    docs_subdir: str = "docs",
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    root = _project_root(project_slug)
    docs_root = (root / docs_subdir).resolve()

    if not docs_root.exists():
        return []

    results: List[Dict[str, Any]] = []
    q_lower = query.lower()

    for md in docs_root.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        idx = text.lower().find(q_lower)
        if idx == -1:
            continue

        start = max(0, idx - 80)
        end = min(len(text), idx + 80)
        snippet = text[start:end].replace("\n", " ")

        results.append(
            {
                "path": md.relative_to(root).as_posix(),
                "snippet": snippet,
            }
        )
        if len(results) >= max_results:
            break

    return results