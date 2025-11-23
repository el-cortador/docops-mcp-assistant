# mcp-servers/confluence-mcp-server/mcp_confluence/utils.py
from __future__ import annotations

from typing import Optional


def get_required_env(name: str) -> str:
    import os

    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Переменная окружения {name} не задана. "
            f"Ее нужно указать для работы Confluence MCP-сервера."
        )
    return value


def build_cql(query: str, space_key: Optional[str] = None) -> str:
    safe_query = query.replace('"', '\\"')

    parts = [f'text ~ "{safe_query}"']
    if space_key:
        parts.append(f'space = "{space_key}"')

    return " AND ".join(parts)