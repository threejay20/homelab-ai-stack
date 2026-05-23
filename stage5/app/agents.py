import os
import httpx
import asyncio
from langchain_ollama import OllamaLLM
from enum import Enum
from pydantic import BaseModel
from typing import Optional
import json

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
OLLAMA_HOST   = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_PORT   = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
RAG_HOST      = os.getenv("RAG_HOST", "homelab-rag")
RAG_PORT      = os.getenv("RAG_PORT", "8000")
RAG_API_KEY   = os.getenv("RAG_API_KEY", "")
AGENT_HOST    = os.getenv("AGENT_HOST", "homelab-agent")
AGENT_PORT    = os.getenv("AGENT_PORT", "8001")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")

# ─────────────────────────────────────────
# Agent status enum
# ─────────────────────────────────────────
class AgentStatus(str, Enum):
    IDLE     = "idle"
    THINKING = "thinking"
    ACTIVE   = "active"
    COMPLETE = "complete"
    ERROR    = "error"

# ─────────────────────────────────────────
# Event model — streamed to UI via WebSocket
# ─────────────────────────────────────────
class AgentEvent(BaseModel):
    agent: str
    status: AgentStatus
    message: str
    data: Optional[dict] = None
    handoff_to: Optional[str] = None

# ─────────────────────────────────────────
# LLM
# ─────────────────────────────────────────
llm = OllamaLLM(
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
    model=OLLAMA_MODEL,
    temperature=0.1
)

# ─────────────────────────────────────────
# ChiChi — Planner
# Receives task, creates execution plan,
# delegates to Nezuko and Mikasa,
# synthesizes final answer
# ─────────────────────────────────────────
async def chichi_plan(task: str) -> dict:
    prompt = f"""You are ChiChi, a strategic AI planner. Analyze this task and decide which tools are needed.

Task: {task}

Available agents:
- Nezuko: searches internal documents and runbooks for procedures and knowledge
- Mikasa: checks Docker container status and system resource metrics

Respond in this exact JSON format, nothing else:
{{
    "needs_nezuko": true or false,
    "needs_mikasa": true or false,
    "nezuko_query": "what to search for, or empty string",
    "mikasa_query": "what to check, or empty string",
    "plan": "one sentence describing your approach"
}}"""

    response = llm.invoke(prompt).strip()
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except Exception:
        pass
    return {
        "needs_nezuko": True,
        "needs_mikasa": True,
        "nezuko_query": task,
        "mikasa_query": task,
        "plan": "Gathering information from all available sources"
    }

async def chichi_synthesize(task: str, nezuko_result: str, mikasa_result: str) -> str:
    prompt = f"""You are ChiChi, a strategic AI assistant. Synthesize these results into a clear, helpful answer.

Original question: {task}

Knowledge base findings (from Nezuko):
{nezuko_result}

Infrastructure status (from Mikasa):
{mikasa_result}

Provide a comprehensive, well-structured answer that directly addresses the question.
Answer:"""

    return llm.invoke(prompt).strip()

# ─────────────────────────────────────────
# Nezuko — Retriever
# Searches RAG knowledge base
# ─────────────────────────────────────────
async def nezuko_search(query: str) -> str:
    if not query:
        return "No search required for this task."
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"http://{RAG_HOST}:{RAG_PORT}/query",
                json={"question": query},
                headers={"X-API-Key": RAG_API_KEY}
            )
            data = response.json()
            return data.get("answer", "No relevant documents found.")
    except Exception as e:
        return f"Search unavailable: {str(e)}"

# ─────────────────────────────────────────
# Mikasa — Executor
# Runs infrastructure tools
# ─────────────────────────────────────────
async def mikasa_execute(query: str) -> str:
    if not query:
        return "No execution required for this task."
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get docker status
            docker_response = await client.get(
                f"http://{AGENT_HOST}:{AGENT_PORT}/tools/docker",
                headers={"X-API-Key": AGENT_API_KEY}
            )
            docker_data = docker_response.json()

            # Get system info
            system_response = await client.get(
                f"http://{AGENT_HOST}:{AGENT_PORT}/tools/system",
                headers={"X-API-Key": AGENT_API_KEY}
            )
            system_data = system_response.json()

            return f"Container Status:\n{docker_data.get('result', 'unavailable')}\n\nSystem Metrics:\n{system_data.get('result', 'unavailable')}"
    except Exception as e:
        return f"Execution unavailable: {str(e)}"

# ─────────────────────────────────────────
# Main orchestrator
# Runs the full multi-agent pipeline
# Yields AgentEvents for WebSocket streaming
# ─────────────────────────────────────────
async def run_multiagent(task: str):
    # ── ChiChi Plans ──
    yield AgentEvent(
        agent="chichi",
        status=AgentStatus.THINKING,
        message="Analyzing your request and forming a plan..."
    )
    await asyncio.sleep(0.5)

    plan = await chichi_plan(task)

    yield AgentEvent(
        agent="chichi",
        status=AgentStatus.ACTIVE,
        message=plan.get("plan", "Planning complete"),
        data=plan,
        handoff_to="nezuko" if plan.get("needs_nezuko") else "mikasa"
    )
    await asyncio.sleep(0.5)

    # ── Nezuko Retrieves ──
    nezuko_result = "No search performed."
    if plan.get("needs_nezuko") and plan.get("nezuko_query"):
        yield AgentEvent(
            agent="nezuko",
            status=AgentStatus.THINKING,
            message="Entering the archive... searching knowledge base..."
        )
        await asyncio.sleep(0.5)

        yield AgentEvent(
            agent="nezuko",
            status=AgentStatus.ACTIVE,
            message=f"Searching for: {plan['nezuko_query']}"
        )

        nezuko_result = await nezuko_search(plan["nezuko_query"])

        yield AgentEvent(
            agent="nezuko",
            status=AgentStatus.COMPLETE,
            message="Search complete. Handing findings to Mikasa.",
            data={"result": nezuko_result[:200] + "..." if len(nezuko_result) > 200 else nezuko_result},
            handoff_to="mikasa" if plan.get("needs_mikasa") else "chichi"
        )
        await asyncio.sleep(0.5)

    # ── Mikasa Executes ──
    mikasa_result = "No execution performed."
    if plan.get("needs_mikasa") and plan.get("mikasa_query"):
        yield AgentEvent(
            agent="mikasa",
            status=AgentStatus.THINKING,
            message="Entering the operations bay... running infrastructure checks..."
        )
        await asyncio.sleep(0.5)

        yield AgentEvent(
            agent="mikasa",
            status=AgentStatus.ACTIVE,
            message="Checking container status and system metrics..."
        )

        mikasa_result = await mikasa_execute(plan["mikasa_query"])

        yield AgentEvent(
            agent="mikasa",
            status=AgentStatus.COMPLETE,
            message="Execution complete. Returning results to ChiChi.",
            data={"result": mikasa_result[:200] + "..." if len(mikasa_result) > 200 else mikasa_result},
            handoff_to="chichi"
        )
        await asyncio.sleep(0.5)

    # ── ChiChi Synthesizes ──
    yield AgentEvent(
        agent="chichi",
        status=AgentStatus.THINKING,
        message="All agents reporting in... synthesizing final answer..."
    )
    await asyncio.sleep(0.5)

    final_answer = await chichi_synthesize(task, nezuko_result, mikasa_result)

    yield AgentEvent(
        agent="chichi",
        status=AgentStatus.COMPLETE,
        message="Analysis complete.",
        data={"final_answer": final_answer}
    )
