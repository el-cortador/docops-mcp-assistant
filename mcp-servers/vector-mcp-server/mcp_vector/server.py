# mcp-servers/vector-mcp-server/mcp_vector/server.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("docops-vector-demo")


def get_store_path() -> Path:
    import os

    env_path = os.getenv("DOCOPS_VECTOR_STORE_PATH")
    if env_path:
        p = Path(env_path).expanduser().resolve()
    else:
        # <root>/demo_data/vector_store/documents.jsonl
        root = Path(__file__).resolve().parents[4]
        p = root / "demo_data" / "vector_store" / "documents.jsonl"

    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@dataclass
class StoredDocument:
    project_slug: str
    doc_id: str  # произвольная строка (например, путь к файлу или ID страницы)
    title: str
    text: str
    metadata: Dict[str, Any]


def _load_all() -> List[StoredDocument]:
    path = get_store_path()
    if not path.exists():
        return []
    docs: List[StoredDocument] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            raw = json.loads(line)
            docs.append(
                StoredDocument(
                    project_slug=raw["project_slug"],
                    doc_id=raw["doc_id"],
                    title=raw.get("title", ""),
                    text=raw.get("text", ""),
                    metadata=raw.get("metadata", {}),
                )
            )
    return docs


def _save_all(docs: List[StoredDocument]) -> None:
    path = get_store_path()
    with path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(asdict(d), ensure_ascii=False) + "\n")


@mcp.tool()
def upsert_document(
    project_slug: str,
    doc_id: str,
    title: str,
    text: str,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    docs = _load_all()
    metadata = metadata or {}

    # заменяем, если уже есть
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

    _save_all(docs)

    return {
        "status": "ok",
        "replaced": replaced,
    }


@mcp.tool()
def search_documents(
    project_slug: str,
    query: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    docs = [d for d in _load_all() if d.project_slug == project_slug]
    if not docs:
        return []

    q = query.lower()
    scored: List[tuple[int, StoredDocument]] = []
    for d in docs:
        count = d.text.lower().count(q)
        if count > 0:
            scored.append((count, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

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