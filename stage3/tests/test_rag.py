import pytest
import httpx

RAG_URL = "http://localhost:8000"
RAG_KEY = "homelab-rag-key-2024"
HEADERS = {"X-API-Key": RAG_KEY}


class TestRAGHealth:
    def test_health_endpoint_returns_ok(self):
        response = httpx.get(f"{RAG_URL}/health", timeout=30.0)
        assert response.status_code == 200

    def test_qdrant_connected(self):
        response = httpx.get(f"{RAG_URL}/health", timeout=30.0)
        data = response.json()
        assert data["qdrant"] == "ok"

    def test_ollama_connected(self):
        response = httpx.get(f"{RAG_URL}/health", timeout=30.0)
        data = response.json()
        assert data["ollama"] == "ok"


class TestRAGAuth:
    def test_query_rejected_without_api_key(self):
        response = httpx.post(
            f"{RAG_URL}/query",
            json={"question": "test"},
            timeout=30.0
        )
        assert response.status_code == 403

    def test_ingest_rejected_without_api_key(self):
        response = httpx.post(
            f"{RAG_URL}/ingest",
            files={"file": ("test.txt", "test content", "text/plain")},
            timeout=30.0
        )
        assert response.status_code == 403

    def test_collections_rejected_without_api_key(self):
        response = httpx.get(f"{RAG_URL}/collections", timeout=30.0)
        assert response.status_code == 403

    def test_query_accepted_with_api_key(self):
        response = httpx.post(
            f"{RAG_URL}/query",
            json={"question": "What is a restart policy?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200


class TestRAGIngestion:
    def test_collection_exists_after_ingest(self):
        response = httpx.get(
            f"{RAG_URL}/collections",
            headers=HEADERS,
            timeout=30.0
        )
        assert response.status_code == 200
        data = response.json()
        collections = [c["name"] for c in data["collections"]]
        assert "homelab_docs" in collections

    def test_ingest_returns_chunk_count(self):
        test_content = "Test document for chunk count verification."
        response = httpx.post(
            f"{RAG_URL}/ingest",
            files={"file": ("chunk-test.txt", test_content, "text/plain")},
            headers=HEADERS,
            timeout=60.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_stored"] >= 1

    def test_rejects_unsupported_file_type(self):
        response = httpx.post(
            f"{RAG_URL}/ingest",
            files={"file": ("test.csv", "a,b,c", "text/csv")},
            headers=HEADERS,
            timeout=30.0
        )
        assert response.status_code == 400


class TestRAGRetrieval:
    def test_query_restart_policy(self):
        response = httpx.post(
            f"{RAG_URL}/query",
            json={"question": "What restart policy should I use for production services?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        answer = data["answer"].lower()
        assert any(keyword in answer for keyword in [
            "unless-stopped", "unless stopped", "always"
        ])

    def test_query_memory_limits(self):
        response = httpx.post(
            f"{RAG_URL}/query",
            json={"question": "What happens when a container exceeds its memory limit?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        answer = data["answer"].lower()
        assert any(keyword in answer for keyword in [
            "oomkilled", "killed", "restart", "memory", "mem_limit"
        ])

    def test_query_returns_question_echo(self):
        question = "What is the recommended restart policy?"
        response = httpx.post(
            f"{RAG_URL}/query",
            json={"question": question},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == question

    def test_query_returns_collection_name(self):
        response = httpx.post(
            f"{RAG_URL}/query",
            json={"question": "What is mem_limit?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["collection"] == "homelab_docs"
