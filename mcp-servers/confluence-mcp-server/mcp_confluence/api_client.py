# mcp-servers/confluence-mcp-server/mcp_confluence/api_client.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

import httpx

from .utils import get_required_env, build_cql


class ConfluenceClient:
    def __init__(
        self,
        base_url: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = (
            base_url
            or get_required_env("CONFLUENCE_BASE_URL").rstrip("/")
        )
        self.email = email or get_required_env("CONFLUENCE_EMAIL")
        self.api_token = api_token or get_required_env("CONFLUENCE_API_TOKEN")

        # httpx.Client переиспользуем между запросами
        self.client = httpx.Client(
            base_url=self.base_url,
            auth=(self.email, self.api_token),
            timeout=timeout,
        )

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self.client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.client.post(path, json=json_body)
        resp.raise_for_status()
        return resp.json()

    def search_pages(
        self,
        query: str,
        space_key: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        cql = build_cql(query=query, space_key=space_key)
        params = {"cql": cql, "limit": limit}

        data = self._get("/rest/api/search", params=params)

        results: List[Dict[str, Any]] = []
        for item in data.get("results", []):
            content = item.get("content", {})
            links = content.get("_links", {}) if isinstance(content, dict) else {}

            results.append(
                {
                    "id": content.get("id"),
                    "title": content.get("title"),
                    "space": content.get("space", {}).get("key")
                    if isinstance(content.get("space"), dict)
                    else None,
                    # относительный путь в интерфейсе Confluence
                    "url": links.get("webui"),
                }
            )
        return results

    def get_page(self, page_id: str) -> Dict[str, Any]:
        params = {
            "expand": "body.storage,version,space",
        }
        return self._get(f"/rest/api/content/{page_id}", params=params)

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

        return self._post("/rest/api/content", json_body=payload)

    def close(self) -> None:
        self.client.close()