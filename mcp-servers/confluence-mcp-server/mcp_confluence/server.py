# mcp-servers/confluence-mcp-server/mcp_confluence/server.py
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("docops-confluence")


class ConfluenceClient:
    def __init__(self):
        import os

        self.base_url = os.getenv("CONFLUENCE_BASE_URL")
        self.email = os.getenv("CONFLUENCE_EMAIL")
        self.token = os.getenv("CONFLUENCE_API_TOKEN")

        if not self.base_url or not self.email or not self.token:
            raise RuntimeError(
                "CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL и CONFLUENCE_API_TOKEN "
                "должны быть заданы в окружении."
            )

        self.client = httpx.Client(
            base_url=self.base_url.rstrip("/"),
            auth=(self.email, self.token),
            timeout=15.0,
        )

    def search_pages(
        self,
        query: str,
        space_key: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        cql_parts = [f'text ~ "{query}"']
        if space_key:
            cql_parts.append(f'space = "{space_key}"')

        cql = " AND ".join(cql_parts)
        params = {
            "cql": cql,
            "limit": limit,
        }
        resp = self.client.get(f"/rest/api/search?{urlencode(params)}")
        resp.raise_for_status()
        data = resp.json()

        results: List[Dict[str, Any]] = []
        for item in data.get("results", []):
            content = item.get("content", {})
            results.append(
                {
                    "id": content.get("id"),
                    "title": content.get("title"),
                    "space": content.get("space", {}).get("key"),
                    "url": content.get("_links", {}).get("webui"),
                }
            )
        return results

    def get_page(self, page_id: str) -> Dict[str, Any]:
        resp = self.client.get(
            f"/rest/api/content/{page_id}",
            params={"expand": "body.storage,version,space"},
        )
        resp.raise_for_status()
        return resp.json()

    def create_page(
        self,
        space_key: str,
        title: str,
        body_storage: str,
        parent_page_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": body_storage,
                    "representation": "storage",
                }
            },
        }

        if parent_page_id:
            payload["ancestors"] = [{"id": parent_page_id}]

        resp = self.client.post("/rest/api/content", json=payload)
        resp.raise_for_status()
        return resp.json()


def get_client() -> ConfluenceClient:
    # Простейший singleton: в реальной жизни лучше использовать lifespan контекст.
    global _CLIENT  # type: ignore
    try:
        return _CLIENT  # type: ignore
    except NameError:
        _CLIENT = ConfluenceClient()  # type: ignore
        return _CLIENT


@mcp.tool()
def confluence_search_pages(
    query: str,
    space_key: str | None = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    client = get_client()
    return client.search_pages(query=query, space_key=space_key, limit=limit)


@mcp.tool()
def confluence_get_page(page_id: str) -> Dict[str, Any]:
    client = get_client()
    return client.get_page(page_id)


@mcp.tool()
def confluence_create_page(
    space_key: str,
    title: str,
    body_storage: str,
    parent_page_id: str | None = None,
) -> Dict[str, Any]:
    client = get_client()
    return client.create_page(
        space_key=space_key,
        title=title,
        body_storage=body_storage,
        parent_page_id=parent_page_id,
    )