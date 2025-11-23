# app/mcp_client/vector_tools.py

from __future__ import annotations

from typing import Dict, Any, List

from app.mcp_client.client import get_vector_store


def upsert_document(
    project_slug: str,
    doc_id: str,
    title: str,
    text: str,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    store = get_vector_store()
    return store.upsert_document(
        project_slug=project_slug,
        doc_id=doc_id,
        title=title,
        text=text,
        metadata=metadata,
    )


def search_documents(
    project_slug: str,
    query: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    store = get_vector_store()
    return store.search_documents(
        project_slug=project_slug,
        query=query,
        limit=limit,
    )