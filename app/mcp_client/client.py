# app/mcp_client/client.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.config.settings import settings

# Эти пакеты выбрасывают ошибку при установке MCP-серверов в editable-режиме
#   pip install -e mcp-servers/confluence-mcp-server
#   pip install -e mcp-servers/vector-mcp-server
from mcp_confluence.api_client import ConfluenceClient  # type: ignore
from mcp_vector.store import JsonlDocumentStore  # type: ignore


@dataclass
class MCPClients:
    _confluence: Optional[ConfluenceClient] = field(default=None, init=False)
    _vector_store: Optional[JsonlDocumentStore] = field(default=None, init=False)

    @property
    def confluence(self) -> ConfluenceClient:
        if self._confluence is None:
            self._confluence = ConfluenceClient(
                base_url=settings.confluence.base_url,
                email=settings.confluence.email,
                api_token=settings.confluence.api_token,
            )
        return self._confluence

    @property
    def vector_store(self) -> JsonlDocumentStore:
        if self._vector_store is None:
            self._vector_store = JsonlDocumentStore(
                path=settings.paths.vector_store_path
            )
        return self._vector_store

_clients = MCPClients()


def get_confluence_client() -> ConfluenceClient:
    return _clients.confluence


def get_vector_store() -> JsonlDocumentStore:
    return _clients.vector_store