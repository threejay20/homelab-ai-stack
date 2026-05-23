import pytest
import httpx
import time

RAG_URL   = "http://localhost:8000"
AGENT_URL = "http://localhost:8001"
RAG_KEY   = "homelab-rag-key-2024"
AGENT_KEY = "homelab-agent-key-2024"

TEST_DOCUMENT = """
Container Restart Policy

A restart policy controls whether containers start automatically
after they exit or when Docker restarts.

The always policy restarts the container regardless of exit status.
Use always for services that must stay running in production.

The unless-stopped policy restarts the container unless it was
manually stopped. This is the recommended policy for most services.

The on-failure policy only restarts the container if it exits
with a non-zero exit code. Use this for batch jobs.

To set a restart policy in docker-compose use restart: unless-stopped
under the service definition.

Memory Limits

Setting mem_limit in docker-compose prevents a single container
from consuming all available host memory. If a container exceeds
its memory limit Docker will kill and restart it with an OOMKilled
status. Always set mem_limit for production containers.

Recommended limits for this lab:
- PostgreSQL: 512m
- MLflow: 512m
- Qdrant: 512m
- Ollama: 6g
- FastAPI apps: 1g
"""


@pytest.fixture(scope="session")
def rag_client():
    return httpx.Client(
        base_url=RAG_URL,
        timeout=120.0,
        headers={"X-API-Key": RAG_KEY}
    )


@pytest.fixture(scope="session")
def agent_client():
    return httpx.Client(
        base_url=AGENT_URL,
        timeout=120.0,
        headers={"X-API-Key": AGENT_KEY}
    )


@pytest.fixture(scope="session", autouse=True)
def ingest_test_document(rag_client):
    print("\nIngesting test document...")
    response = rag_client.post(
        "/ingest",
        files={"file": ("test-doc.txt", TEST_DOCUMENT, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    print(f"Ingested {data['chunks_stored']} chunks")
    time.sleep(2)
    yield
    print("\nTest session complete")
