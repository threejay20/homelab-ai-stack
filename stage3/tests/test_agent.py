import pytest
import httpx

AGENT_URL = "http://localhost:8001"
AGENT_KEY = "homelab-agent-key-2024"
HEADERS = {"X-API-Key": AGENT_KEY}


class TestAgentHealth:
    def test_health_endpoint_returns_ok(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        assert response.status_code == 200

    def test_rag_pipeline_connected(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        data = response.json()
        assert data["rag_pipeline"] == "ok"

    def test_docker_tool_connected(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        data = response.json()
        assert data["docker_tool"] == "ok"

    def test_system_tool_connected(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        data = response.json()
        assert data["system_tool"] == "ok"


class TestAgentAuth:
    def test_agent_rejected_without_api_key(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "test"},
            timeout=30.0
        )
        assert response.status_code == 403

    def test_tools_rejected_without_api_key(self):
        response = httpx.get(f"{AGENT_URL}/tools/docker", timeout=30.0)
        assert response.status_code == 403

    def test_agent_accepted_with_api_key(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What containers are running?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200


class TestToolRouting:
    def test_docker_question_routes_to_docker_tool(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What Docker containers are currently running?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "docker_status"

    def test_system_question_routes_to_system_tool(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "How much memory is the system currently using?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "system_info"

    def test_runbook_question_routes_to_rag(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What is the procedure for backing up PostgreSQL data?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "rag_search"

    def test_cpu_question_routes_to_system_tool(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What is the current CPU usage?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "system_info"


class TestAgentResponse:
    def test_response_contains_required_fields(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What containers are running?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert "status" in data
        assert "tool_used" in data

    def test_answer_is_not_empty(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What containers are running?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 10

    def test_docker_answer_contains_container_names(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What Docker containers are running?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "homelab" in data["answer"].lower()

    def test_empty_question_rejected(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": ""},
            headers=HEADERS,
            timeout=30.0
        )
        assert response.status_code == 400


class TestDirectToolEndpoints:
    def test_docker_tool_endpoint(self):
        response = httpx.get(
            f"{AGENT_URL}/tools/docker",
            headers=HEADERS,
            timeout=30.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "docker_status"

    def test_system_tool_endpoint(self):
        response = httpx.get(
            f"{AGENT_URL}/tools/system",
            headers=HEADERS,
            timeout=30.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "memory" in data["result"].lower()

    def test_rag_tool_endpoint(self):
        response = httpx.post(
            f"{AGENT_URL}/tools/rag",
            json={"question": "What is a restart policy?"},
            headers=HEADERS,
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["result"]) > 10
