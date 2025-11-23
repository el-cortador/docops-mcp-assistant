# app/mcp_client/git_tools.py

# Модуль для операций с Git-репозиторием и функции поиска по документации

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

from app.config.settings import settings


def _project_root(project_slug: str) -> Path:
    # Получает путь в корневую директорию проекта по его идентификатору
    
    base = settings.paths.demo_repos_dir
    root = base / project_slug
    if not root.exists():
        raise FileNotFoundError(
            f"Demo repository not found for slug={project_slug} at {root}"
        )
    return root


def list_files(project_slug: str, subdir: str = "") -> List[str]:
    # Выдает список всех файлов в репозитории проекта
    
    root = _project_root(project_slug)
    target = (root / subdir).resolve()

    if not target.exists():
        return []

    # Чтобы не вылезти за пределы корня репы
    if not str(target).startswith(str(root)):
        raise ValueError("subdir must stay inside project root")

    files: List[str] = []
    for p in target.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            files.append(rel)

    return files


def read_file(project_slug: str, path: str) -> str:
    # Считывает данные файла из репы проекта
    
    root = _project_root(project_slug)
    fpath = (root / path).resolve()

    if not str(fpath).startswith(str(root)):
        raise ValueError("Path escapes project root")

    if not fpath.exists() or not fpath.is_file():
        raise FileNotFoundError(f"File not found: {path} in project {project_slug}")

    return fpath.read_text(encoding="utf-8")


def search_in_docs(
    project_slug: str,
    query: str,
    docs_subdir: str = "docs",
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    # Ищет строку запроса в markdown-файлах проекта и возвращает пути и найденные фрагменты текста

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