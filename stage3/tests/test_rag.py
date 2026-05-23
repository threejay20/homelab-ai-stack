import pytest
import httpx

RAG_URL = "http://localhost:8000"

class TestRAGHealth:
    """Verify RAG pipeline and dependencies are reachable."""

    def test_health_endpoint_returns_ok(self):
        response = httpx.get(f"{RAG_URL}/health", timeout=30.0)
        assert response.status_code == 200

    def test_qdrant_connected(self):
        response = httpx.get(f"{RAG_URL}/health", timeout=30.0)
        data = response.json()
        assert data["qdrant"] == "ok", f"Qdrant not healthy: {data}"

    def test_ollama_connected(self):
        response = httpx.get(f"{RAG_URL}/health", timeout=30.0)
        data = response.json()
        assert data["ollama"] == "ok", f"Ollama not healthy: {data}"


class TestRAGIngestion:
    """Verify document ingestion pipeline."""

    def test_collection_exists_after_ingest(self):
        response = httpx.get(f"{RAG_URL}/collections", timeout=30.0)
        assert response.status_code == 200
        data = response.json()
        collections = [c["name"] for c in data["collections"]]
        assert "homelab_docs" in collections, \
            f"Expected homelab_docs collection, got: {collections}"

    def test_ingest_returns_chunk_count(self):
        test_content = "Test document for chunk count verification."
        response = httpx.post(
            f"{RAG_URL}/ingest",
            files={"file": ("chunk-test.txt", test_content, "text/plain")},
            timeout=60.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "chunks_stored" in data
        assert data["chunks_stored"] >= 1

    def test_rejects_unsupported_file_type(self):
        response = httpx.post(
            f"{RAG_URL}/ingest",
            files={"file": ("test.csv", "a,b,c", "text/csv")},
            timeout=30.0
        )
        assert response.status_code == 400


class TestRAGRetrieval:
    """
    Verify retrieval quality against known document content.
    These tests use the document ingested in conftest.py.
    Each test asks a question and verifies the answer contains
    expected keywords from the source document.
    """

    def test_query_restart_policy(self):
        response = httpx.post(
            f"{RAG_URL}/query",
            json={"question": "What restart policy should I use for production services?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer"
