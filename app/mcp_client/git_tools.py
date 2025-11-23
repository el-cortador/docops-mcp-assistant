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
    min_score: float = 5.0,
) -> List[Dict[str, Any]]:
    """
    Ищет строку/фразу в markdown-файлах документации проекта.
    Использует токенизацию и фразовый поиск для улучшения релевантности.

    Возвращает список словарей:
      {"path": str, "snippet": str, "score": float}
    """
    root = _project_root(project_slug)
    docs_root = (root / docs_subdir).resolve()

    if not docs_root.exists():
        return []

    query_norm = query.lower().strip()

    # Токенизация: разбиваем запрос на слова, фильтруем короткие стоп-слова
    stop_words = {"как", "что", "где", "когда", "и", "в", "на", "с", "по", "для", "или", "а", "это", "эта", "этот"}
    tokens = [
        word for word in query_norm.split()
        if len(word) > 2 and word not in stop_words
    ]

    if not tokens:
        # Если после фильтрации не осталось токенов, используем исходный запрос
        tokens = [query_norm]

    # Извлекаем технические термины (2-3 слова подряд из латиницы/цифр)
    import re
    technical_phrases = re.findall(r'\b[a-z][a-z0-9_-]*(?:\s+[a-z][a-z0-9_-]*){0,2}\b', query_norm)
    technical_phrases = [p for p in technical_phrases if len(p) > 3]

    results: List[Dict[str, Any]] = []

    for path in docs_root.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        text_norm = text.lower()

        # Подсчитываем релевантность на основе токенов и фраз
        score = 0.0
        matched_tokens = []

        # 1. Фразовый поиск (высокий вес) - exact match дает большой бонус
        for phrase in technical_phrases:
            phrase_count = text_norm.count(phrase)
            if phrase_count > 0:
                score += phrase_count * 10.0  # Фраза дает 10 баллов за вхождение
                matched_tokens.append(phrase)

        # 2. Поиск по токенам (базовый вес)
        token_matches = 0
        for token in tokens:
            count = text_norm.count(token)
            if count > 0:
                score += count * 1.0  # Токен дает 1 балл за вхождение
                matched_tokens.append(token)
                token_matches += 1

        # 3. Бонус за количество совпавших разных токенов (diversity bonus)
        if token_matches >= 2:
            score += token_matches * 2.0

        # Применяем минимальный порог релевантности
        if score >= min_score:
            # Находим фрагмент с наибольшей концентрацией совпадений
            best_idx = -1
            if matched_tokens:
                # Приоритет - фразы, потом токены
                for token in matched_tokens:
                    idx = text_norm.find(token)
                    if idx != -1:
                        best_idx = idx
                        break

            if best_idx == -1:
                best_idx = 0

            # Берем фрагмент вокруг найденного места
            start = max(0, best_idx - 200)
            end = min(len(text), best_idx + 200)
            snippet = text[start:end].strip()

            results.append(
                {
                    "path": str(path.relative_to(root)),
                    "snippet": snippet,
                    "score": score,
                }
            )

    # Сортируем по score (релевантности) по убыванию
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