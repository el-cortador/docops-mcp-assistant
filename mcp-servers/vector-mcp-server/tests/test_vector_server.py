# mcp-servers/vector-mcp-server/mcp_vector/tests/test_server.py

import os
from pathlib import Path

from mcp_vector.store import JsonlDocumentStore


def test_upsert_and_search_documents(tmp_path):
    store_path = tmp_path / "documents.jsonl"
    os.environ["DOCOPS_VECTOR_STORE_PATH"] = str(store_path)

    store = JsonlDocumentStore(path=store_path)

    # 1. Добавляем документ
    res1 = store.upsert_document(
        project_slug="docops-saas",
        doc_id="docs/billing_overview.md",
        title="Billing Overview",
        text="Сервис биллинга отвечает за выставление счетов.",
        metadata={"kind": "doc"},
    )
    assert res1["status"] == "ok"
    assert res1["replaced"] is False

    # 2. Обновляем этот же документ
    res2 = store.upsert_document(
        project_slug="docops-saas",
        doc_id="docs/billing_overview.md",
        title="Billing Overview v2",
        text="Обновленный текст: сервис биллинга и расчет подписок.",
        metadata={"kind": "doc", "version": 2},
    )
    assert res2["status"] == "ok"
    assert res2["replaced"] is True

    # 3. Ищем по слову "подписок"
    results = store.search_documents(
        project_slug="docops-saas",
        query="подписок",
        limit=5,
    )

    assert len(results) >= 1
    hit = results[0]
    assert hit["doc_id"] == "docs/billing_overview.md"
    assert "подписок" in hit["snippet"]
    assert hit["metadata"]["version"] == 2


def test_search_documents_empty_when_no_match(tmp_path):
    store_path = tmp_path / "documents.jsonl"
    os.environ["DOCOPS_VECTOR_STORE_PATH"] = str(store_path)

    store = JsonlDocumentStore(path=store_path)

    # добавим документ
    store.upsert_document(
        project_slug="airport-food",
        doc_id="docs/process_overview.md",
        title="Process",
        text="Процесс доставки в бизнес-зал аэропорта.",
        metadata={},
    )

    # поиск по слову, которого нет
    results = store.search_documents(
        project_slug="airport-food",
        query="несуществующее-слово",
        limit=5,
    )
    assert results == []