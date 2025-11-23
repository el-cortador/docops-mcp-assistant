# mcp-servers/confluence-mcp-server/tests/test_server.py

import pytest

from mcp_confluence.utils import build_cql, get_required_env
from mcp_confluence.api_client import ConfluenceClient


def test_get_required_env_present(monkeypatch):
    monkeypatch.setenv("TEST_ENV_VAR", "value123")
    assert get_required_env("TEST_ENV_VAR") == "value123"


def test_get_required_env_missing(monkeypatch):
    monkeypatch.delenv("TEST_ENV_VAR", raising=False)
    with pytest.raises(RuntimeError):
        get_required_env("TEST_ENV_VAR")


def test_build_cql_without_space_key():
    query = 'billing "core"'
    cql = build_cql(query=query, space_key=None)
    assert 'text ~ "billing \\"core\\"" ' in cql or cql == 'text ~ "billing \\"core\\""'


def test_build_cql_with_space_key():
    query = "billing"
    cql = build_cql(query=query, space_key="DOCS")
    assert 'text ~ "billing"' in cql
    assert 'space = "DOCS"' in cql
    assert "AND" in cql

class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


class DummyHttpxClient:
    def __init__(self, responses):
        # responses: dict[(method, path), data]
        self.responses = responses
        self.calls = []

    def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        key = ("GET", path)
        data = self.responses.get(key, {})
        return DummyResponse(data)

    def post(self, path, json=None):
        self.calls.append(("POST", path, json))
        key = ("POST", path)
        data = self.responses.get(key, json or {})
        return DummyResponse(data)

def _make_dummy_client(get_data=None, post_data=None) -> ConfluenceClient:
    get_data = get_data or {}
    post_data = post_data or {}
    responses = {}
    responses.update(get_data)
    responses.update(post_data)

    dummy = ConfluenceClient.__new__(ConfluenceClient)
    dummy.base_url = "https://example.com/wiki"
    dummy.email = "user@example.com"
    dummy.api_token = "dummy"
    dummy.client = DummyHttpxClient(responses)
    return dummy

def test_confluence_client_search_pages_parses_results():
    search_payload = {
        "results": [
            {
                "content": {
                    "id": "123",
                    "title": "Billing Overview",
                    "space": {"key": "DOCS"},
                    "_links": {"webui": "/spaces/DOCS/pages/123"},
                }
            }
        ]
    }

    client = _make_dummy_client(
        get_data={
            ("GET", "/rest/api/search"): search_payload,
        }
    )

    results = client.search_pages(query="billing", space_key="DOCS", limit=5)
    assert len(results) == 1
    item = results[0]
    assert item["id"] == "123"
    assert item["title"] == "Billing Overview"
    assert item["space"] == "DOCS"
    assert item["url"] == "/spaces/DOCS/pages/123"


def test_confluence_client_create_page_sends_payload():
    created = {
        "id": "999",
        "type": "page",
        "title": "New Page",
        "space": {"key": "DOCS"},
    }

    client = _make_dummy_client(
        post_data={
            ("POST", "/rest/api/content"): created,
        }
    )

    result = client.create_page(
        space_key="DOCS",
        title="New Page",
        body_storage="<p>Hello</p>",
        parent_page_id="111",
    )

    assert result["id"] == "999"
    assert result["title"] == "New Page"
    assert result["space"]["key"] == "DOCS"