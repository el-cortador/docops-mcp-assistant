# mcp-servers/vector-mcp-server/mcp_vector/store.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def get_store_path() -> Path:
    env_path = os.getenv("DOCOPS_VECTOR_STORE_PATH")
    if env_path:
        p = Path(env_path).expanduser().resolve()
    else:
        # Текущий файл: <root>/mcp-servers/vector-mcp-server/mcp_vector/store.py
        # root = parents[3]
        root = Path(__file__).resolve().parents[3]
        p = root / "demo_data" / "vector_store" / "documents.jsonl"

    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@dataclass
class StoredDocument:
    project_slug: str
    doc_id: str
    title: str
    text: str
    metadata: Dict[str, Any]


class JsonlDocumentStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path: Path = path or get_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------
    # Внутренние helpers
    # ------------------------

    def _load_all(self) -> List[StoredDocument]:
        if not self.path.exists():
            return []

        docs: List[StoredDocument] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                docs.append(
                    StoredDocument(
                        project_slug=raw["project_slug"],
                        doc_id=raw["doc_id"],
                        title=raw.get("title", ""),
                        text=raw.get("text", ""),
                        metadata=raw.get("metadata", {}) or {},
                    )
                )
        return docs

    def _save_all(self, docs: List[StoredDocument]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(asdict(d), ensure_ascii=False) + "\n")

    def upsert_document(
        self,
        project_slug: str,
        doc_id: str,
        title: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        docs = self._load_all()
        metadata = metadata or {}

        replaced = False
        for i, d in enumerate(docs):
            if d.project_slug == project_slug and d.doc_id == doc_id:
                docs[i] = StoredDocument(
                    project_slug=project_slug,
                    doc_id=doc_id,
                    title=title,
                    text=text,
                    metadata=metadata,
                )
                replaced = True
                break

        if not replaced:
            docs.append(
                StoredDocument(
                    project_slug=project_slug,
                    doc_id=doc_id,
                    title=title,
                    text=text,
                    metadata=metadata,
                )
            )

        self._save_all(docs)

        return {
            "status": "ok",
            "replaced": replaced,
        }

    def search_documents(
        self,
        project_slug: str,
        query: str,
        limit: int = 5,
        min_score: float = 5.0,
    ) -> List[Dict[str, Any]]:
        import re

        all_docs = self._load_all()
        docs = [d for d in all_docs if d.project_slug == project_slug]
        if not docs:
            return []

        q = query.lower()

        # Токенизация: разбиваем запрос на слова, фильтруем короткие стоп-слова
        stop_words = {"как", "что", "где", "когда", "и", "в", "на", "с", "по", "для", "или", "а", "это", "эта", "этот"}
        tokens = [
            word for word in q.split()
            if len(word) > 2 and word not in stop_words
        ]

        if not tokens:
            # Если после фильтрации не осталось токенов, используем исходный запрос
            tokens = [q]

        # Извлекаем технические термины (2-3 слова подряд из латиницы/цифр)
        technical_phrases = re.findall(r'\b[a-z][a-z0-9_-]*(?:\s+[a-z][a-z0-9_-]*){0,2}\b', q)
        technical_phrases = [p for p in technical_phrases if len(p) > 3]

        scored: List[Tuple[float, StoredDocument, str]] = []

        for d in docs:
            text_lower = d.text.lower()

            # Подсчитываем релевантность на основе токенов и фраз
            score = 0.0
            matched_tokens = []

            # 1. Фразовый поиск (высокий вес)
            for phrase in technical_phrases:
                phrase_count = text_lower.count(phrase)
                if phrase_count > 0:
                    score += phrase_count * 10.0  # Фраза дает 10 баллов за вхождение
                    matched_tokens.append(phrase)

            # 2. Поиск по токенам (базовый вес)
            token_matches = 0
            for token in tokens:
                count = text_lower.count(token)
                if count > 0:
                    score += count * 1.0  # Токен дает 1 балл за вхождение
                    matched_tokens.append(token)
                    token_matches += 1

            # 3. Бонус за количество совпавших разных токенов
            if token_matches >= 2:
                score += token_matches * 2.0

            # Применяем минимальный порог релевантности
            if score >= min_score:
                # Находим фрагмент с наибольшей концентрацией совпадений
                best_idx = -1
                if matched_tokens:
                    for token in matched_tokens:
                        idx = text_lower.find(token)
                        if idx != -1:
                            best_idx = idx
                            break

                if best_idx == -1:
                    best_idx = 0

                start = max(0, best_idx - 80)
                end = min(len(d.text), best_idx + 80)
                snippet = d.text[start:end].replace("\n", " ")

                scored.append((score, d, snippet))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: max(limit, 0)]

        results: List[Dict[str, Any]] = []
        for score, d, snippet in top:
            results.append(
                {
                    "doc_id": d.doc_id,
                    "title": d.title,
                    "snippet": snippet,
                    "metadata": d.metadata,
                }
            )

        return results