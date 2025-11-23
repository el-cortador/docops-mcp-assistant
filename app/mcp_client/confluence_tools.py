# app/mcp_client/confluence_tools.py

from __future__ import annotations

from typing import List, Dict, Any, Optional

from app.mcp_client.client import get_confluence_client


def search_pages(
    query: str,
    space_key: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    client = get_confluence_client()
    return client.search_pages(query=query, space_key=space_key, limit=limit)


def get_page(page_id: str) -> Dict[str, Any]:
    client = get_confluence_client()
    return client.get_page(page_id)


def get_page_storage_body(page: Dict[str, Any]) -> str:
    body = page.get("body", {})
    if not isinstance(body, dict):
        return ""
    storage = body.get("storage", {})
    if not isinstance(storage, dict):
        return ""
    value = storage.get("value", "")
    return value if isinstance(value, str) else ""


def create_page(
    space_key: str,
    title: str,
    body_storage: str,
    parent_page_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_confluence_client()
    return client.create_page(
        space_key=space_key,
        title=title,
        body_storage=body_storage,
        parent_page_id=parent_page_id,
    )