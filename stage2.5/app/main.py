from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import run_agent, docker_status, system_info, rag_search
import httpx
import os

app = FastAPI(
    title="DevOps AI Agent",
    description="ReAct agent with RAG, Docker, and system tools",
    version="1.0.0"
)

RAG_HOST = os.getenv("RAG_HOST", "homelab-rag")
RAG_PORT = os.getenv("RAG_PORT", "8000")

# ─────────────────────────────────────────
# Request/Response models
# ─────────────────────────────────────────
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

# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "DevOps AI Agent",
        "status": "running",
        "tools": ["rag_search", "docker_status", "system_info"]
    }

@app.get("/health")
def health():
    try:
        response = httpx.get(
            f"http://{RAG_HOST}:{RAG_PORT}/health",
            timeout=30.0
        )
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

    return {
        "rag_pipeline": rag_status,
        "docker_tool": docker_tool_status,
        "system_tool": system_tool_status
    }

@app.post("/agent", response_model=AgentResponse)
def ask_agent(request: AgentRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = run_agent(request.question)

    return AgentResponse(
        question=result["question"],
        answer=result["answer"],
        status=result["status"],
        tool_used=result.get("tool_used", "")
    )

@app.get("/tools/docker", response_model=ToolResponse)
def tool_docker():
    return ToolResponse(
        tool="docker_status",
        result=docker_status()
    )

@app.get("/tools/system", response_model=ToolResponse)
def tool_system():
    return ToolResponse(
        tool="system_info",
        result=system_info()
    )

@app.post("/tools/rag", response_model=ToolResponse)
def tool_rag(request: AgentRequest):
    return ToolResponse(
        tool="rag_search",
        result=rag_search(request.question)
    )
