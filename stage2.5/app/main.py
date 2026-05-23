from fastapi import FastAPI, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from agent import run_agent, docker_status, system_info, rag_search
import httpx
import time
import os

app = FastAPI(title="DevOps AI Agent", description="AI agent with RAG, Docker, and system tools", version="1.0.0")

RAG_HOST = os.getenv("RAG_HOST", "homelab-rag")
RAG_PORT = os.getenv("RAG_PORT", "8000")

API_KEY = os.getenv("API_KEY", "")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not API_KEY:
        return
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key

AGENT_REQUEST_COUNT = Counter("agent_requests_total", "Total agent requests", ["status"])
AGENT_LATENCY = Histogram("agent_request_duration_seconds", "Agent request latency")
TOOL_USAGE = Counter("agent_tool_usage_total", "Tool usage by name", ["tool"])

class AgentRequest(BaseModel):
    question: str

class AgentResponse(BaseModel):
    question: str
    answer: str
    status: str
    tool_used: str = ""

class ToolResponse(BaseModel):
    tool: str
    result: str

@app.get("/")
def root():
    return {"service": "DevOps AI Agent", "status": "running", "tools": ["rag_search", "docker_status", "system_info"]}

@app.get("/health")
def health():
    try:
        response = httpx.get(f"http://{RAG_HOST}:{RAG_PORT}/health", timeout=30.0)
        rag_status = "ok" if response.status_code == 200 else "error"
    except Exception as e:
        rag_status = f"error: {str(e)}"
    try:
        docker_result = docker_status()
        docker_tool_status = "ok" if "error" not in docker_result.lower() else "error"
    except Exception as e:
        docker_tool_status = f"error: {str(e)}"
    try:
        system_result = system_info()
        system_tool_status = "ok" if "error" not in system_result.lower() else "error"
    except Exception as e:
        system_tool_status = f"error: {str(e)}"
    return {"rag_pipeline": rag_status, "docker_tool": docker_tool_status, "system_tool": system_tool_status}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/agent", response_model=AgentResponse, dependencies=[Depends(verify_api_key)])
def ask_agent(request: AgentRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    start_time = time.time()
    result = run_agent(request.question)
    AGENT_LATENCY.observe(time.time() - start_time)
    if result["status"] == "success":
        AGENT_REQUEST_COUNT.labels(status="success").inc()
        TOOL_USAGE.labels(tool=result.get("tool_used", "unknown")).inc()
    else:
        AGENT_REQUEST_COUNT.labels(status="error").inc()
    return AgentResponse(
        question=result["question"],
        answer=result["answer"],
        status=result["status"],
        tool_used=result.get("tool_used", "")
    )

@app.get("/tools/docker", response_model=ToolResponse, dependencies=[Depends(verify_api_key)])
def tool_docker():
    return ToolResponse(tool="docker_status", result=docker_status())

@app.get("/tools/system", response_model=ToolResponse, dependencies=[Depends(verify_api_key)])
def tool_system():
    return ToolResponse(tool="system_info", result=system_info())

@app.post("/tools/rag", response_model=ToolResponse, dependencies=[Depends(verify_api_key)])
def tool_rag(request: AgentRequest):
    return ToolResponse(tool="rag_search", result=rag_search(request.question))
