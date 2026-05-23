import pytest
import httpx

AGENT_URL = "http://localhost:8001"


class TestAgentHealth:
    """Verify agent and all tool dependencies are reachable."""

    def test_health_endpoint_returns_ok(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        assert response.status_code == 200

    def test_rag_pipeline_connected(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        data = response.json()
        assert data["rag_pipeline"] == "ok", \
            f"RAG pipeline not healthy: {data}"

    def test_docker_tool_connected(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        data = response.json()
        assert data["docker_tool"] == "ok", \
            f"Docker tool not healthy: {data}"

    def test_system_tool_connected(self):
        response = httpx.get(f"{AGENT_URL}/health", timeout=30.0)
        data = response.json()
        assert data["system_tool"] == "ok", \
            f"System tool not healthy: {data}"


class TestToolRouting:
    """
    Verify the agent routes questions to the correct tool.
    This is the most critical test — wrong routing means
    wrong answers regardless of tool quality.
    """

    def test_docker_question_routes_to_docker_tool(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What Docker containers are currently running?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "docker_status", \
            f"Expected docker_status, got: {data['tool_used']}"

    def test_system_question_routes_to_system_tool(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "How much memory is the system currently using?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "system_info", \
            f"Expected system_info, got: {data['tool_used']}"

    def test_runbook_question_routes_to_rag(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What should I do if a container keeps restarting?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "rag_search", \
            f"Expected rag_search, got: {data['tool_used']}"

    def test_cpu_question_routes_to_system_tool(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What is the current CPU usage?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool_used"] == "system_info", \
            f"Expected system_info, got: {data['tool_used']}"


class TestAgentResponse:
    """Verify agent response structure and answer quality."""

    def test_response_contains_required_fields(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What containers are running?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert "status" in data
        assert "tool_used" in data

    def test_response_status_is_success(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What containers are running?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_answer_is_not_empty(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What containers are running?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 10, \
            f"Answer too short: {data['answer']}"

    def test_docker_answer_contains_container_names(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": "What Docker containers are running?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        answer = data["answer"].lower()
        assert "homelab" in answer, \
            f"Expected container names in answer: {answer[:200]}"

    def test_empty_question_rejected(self):
        response = httpx.post(
            f"{AGENT_URL}/agent",
            json={"question": ""},
            timeout=30.0
        )
        assert response.status_code == 400


class TestDirectToolEndpoints:
    """Verify individual tool endpoints work independently of the agent."""

    def test_docker_tool_endpoint(self):
        response = httpx.get(f"{AGENT_URL}/tools/docker", timeout=30.0)
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "docker_status"
        assert len(data["result"]) > 0

    def test_system_tool_endpoint(self):
        response = httpx.get(f"{AGENT_URL}/tools/system", timeout=30.0)
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "system_info"
        assert "memory" in data["result"].lower()

    def test_rag_tool_endpoint(self):
        response = httpx.post(
            f"{AGENT_URL}/tools/rag",
            json={"question": "What is a restart policy?"},
            timeout=120.0
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tool"] == "rag_search"
        assert len(data["result"]) > 10
