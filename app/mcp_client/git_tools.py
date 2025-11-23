# app/mcp_client/git_tools.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from app.config.settings import settings


def _project_root(project_slug: str) -> Path:
    # Защита от выхода за пределы корня репозитория
    root = settings.paths.demo_repos_dir / project_slug
    return root.resolve()


def search_in_docs(
    project_slug: str,
    query: str,
    docs_subdir: str = "docs",
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    [Не проверено]
    Ищет строку/фразу в markdown-файлах документации проекта.

    Возвращает список словарей:
      {"path": str, "snippet": str, "score": int}
    """
    root = _project_root(project_slug)
    docs_root = (root / docs_subdir).resolve()

    if not docs_root.exists():
        return []

    query_norm = query.lower().strip()
    results: List[Dict[str, Any]] = []

    for path in docs_root.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        text_norm = text.lower()
        score = text_norm.count(query_norm) if query_norm else 0

        if score > 0:
            idx = text_norm.find(query_norm)
            # берем фрагмент вокруг первого вхождения
            start = max(0, idx - 200)
            end = min(len(text), idx + 200)
            snippet = text[start:end].strip()

            results.append(
                {
                    "path": str(path.relative_to(root)),
                    "snippet": snippet,
                    "score": score,
                }
            )

    # Если прямых совпадений нет — вернем просто топ-файлы как контекст,
    # чтобы LLM все равно имел под рукой хоть что-то.
    if not results:
        fallback_results: List[Dict[str, Any]] = []
        for path in docs_root.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            snippet = text[:400].strip()
            if not snippet:
                continue
            fallback_results.append(
                {
                    "path": str(path.relative_to(root)),
                    "snippet": snippet,
                    "score": 0,
                }
            )
        results = fallback_results

    # Сортируем по score (кол-во совпадений) по убыванию
    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return results[:max_results]

def list_files(project_slug: str, subdir: str = "docs") -> List[Dict[str, Any]]:
    # Возвращает список файлов подкаталога с их содержимым: path + content
    root = _project_root(project_slug)
    base_dir = (root / subdir).resolve()

    if not base_dir.exists():
        return []

    results: List[Dict[str, Any]] = []

    for path in base_dir.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        results.append(
            {
                "path": str(path.relative_to(root)),
                "content": text,
            }
        )

    return results


def read_file(project_slug: str, path: str) -> str:
    # Читает содержимое файла по указанному пути
    root = _project_root(project_slug)
    file_path = (root / path).resolve()
    
    # Защита от выхода за пределы корня
    try:
        file_path.relative_to(root)
    except ValueError:
        raise ValueError(f"Path {path} is outside project root")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    return file_path.read_text(encoding="utf-8")