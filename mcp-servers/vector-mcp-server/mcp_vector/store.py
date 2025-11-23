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
    ) -> List[Dict[str, Any]]:
        all_docs = self._load_all()
        docs = [d for d in all_docs if d.project_slug == project_slug]
        if not docs:
            return []

        q = query.lower()
        scored: List[Tuple[int, StoredDocument]] = []

        for d in docs:
            count = d.text.lower().count(q)
            if count > 0:
                scored.append((count, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: max(limit, 0)]

        results: List[Dict[str, Any]] = []
        for _, d in top:
            idx = d.text.lower().find(q)
            if idx == -1:
                snippet = d.text[:160].replace("\n", " ")
            else:
                start = max(0, idx - 80)
                end = min(len(d.text), idx + 80)
                snippet = d.text[start:end].replace("\n", " ")

            results.append(
                {
                    "doc_id": d.doc_id,
                    "title": d.title,
                    "snippet": snippet,
                    "metadata": d.metadata,
                }
            )

        return results