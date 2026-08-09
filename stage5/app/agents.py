import os
import httpx
import asyncio
import boto3
import json
from langchain_ollama import OllamaLLM
from enum import Enum
from pydantic import BaseModel
from typing import Optional

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
USE_BEDROCK   = os.getenv("USE_BEDROCK", "false").lower() == "true"
AWS_REGION    = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_PLAN_MODEL    = os.getenv("BEDROCK_PLAN_MODEL", "amazon.nova-micro-v1:0")
BEDROCK_SYNTH_MODEL   = os.getenv("BEDROCK_SYNTH_MODEL", "anthropic.claude-haiku-4-5-20251001-v1:0")

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
# Event model
# ─────────────────────────────────────────
class AgentEvent(BaseModel):
    agent: str
    status: AgentStatus
    message: str
    data: Optional[dict] = None
    handoff_to: Optional[str] = None

# ─────────────────────────────────────────
# LLM clients
# ─────────────────────────────────────────
llm = OllamaLLM(
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
    model=OLLAMA_MODEL,
    temperature=0.1
)

def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)

# ─────────────────────────────────────────
# Bedrock invoke helpers
# ─────────────────────────────────────────
def bedrock_nova(prompt: str, model_id: str) -> str:
    client = get_bedrock_client()
    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 1000, "temperature": 0.1}
    }
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"].strip()

def bedrock_haiku(prompt: str) -> str:
    client = get_bedrock_client()
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = client.invoke_model(
        modelId=BEDROCK_SYNTH_MODEL,
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"].strip()

# ─────────────────────────────────────────
# Tribal Chief — Planner
# ─────────────────────────────────────────
async def tribal_chief_plan(task: str) -> dict:
    prompt = f"""You are Tribal Chief, a strategic AI planner. Analyze this task and decide which tools are needed.

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

    try:
        if USE_BEDROCK:
            response = bedrock_nova(prompt, BEDROCK_PLAN_MODEL)
        else:
            response = llm.invoke(prompt).strip()
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except Exception as e:
        print(f"Plan error: {e}")
    return {
        "needs_nezuko": True,
        "needs_mikasa": True,
        "nezuko_query": task,
        "mikasa_query": task,
        "plan": "Gathering information from all available sources"
    }

async def tribal_chief_synthesize(task: str, nezuko_result: str, mikasa_result: str) -> str:
    prompt = f"""You are Tribal Chief, a strategic AI assistant. Synthesize these results into a clear, helpful answer.

Original question: {task}

Knowledge base findings (from Nezuko):
{nezuko_result}

Infrastructure status (from Mikasa):
{mikasa_result}

Provide a comprehensive, well-structured answer that directly addresses the question.
Answer:"""

    try:
        if USE_BEDROCK:
            return bedrock_haiku(prompt)
        else:
            return llm.invoke(prompt).strip()
    except Exception as e:
        print(f"Synthesize error: {e}")
        return llm.invoke(prompt).strip()

# ─────────────────────────────────────────
# Nezuko — Retriever
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
# ─────────────────────────────────────────
async def mikasa_execute(query: str) -> str:
    if not query:
        return "No execution required for this task."
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            docker_response = await client.get(
                f"http://{AGENT_HOST}:{AGENT_PORT}/tools/docker",
                headers={"X-API-Key": AGENT_API_KEY}
            )
            docker_data = docker_response.json()
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
# ─────────────────────────────────────────
async def run_multiagent(task: str):
    mode = "BEDROCK" if USE_BEDROCK else "LOCAL"

    yield AgentEvent(
        agent="tribal_chief",
        status=AgentStatus.THINKING,
        message=f"Analyzing your request [{mode}] and forming a plan..."
    )
    await asyncio.sleep(0.5)

    plan = await tribal_chief_plan(task)

    yield AgentEvent(
        agent="tribal_chief",
        status=AgentStatus.ACTIVE,
        message=plan.get("plan", "Planning complete"),
        data=plan,
        handoff_to="nezuko" if plan.get("needs_nezuko") else "mikasa"
    )
    await asyncio.sleep(0.5)

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
            handoff_to="mikasa" if plan.get("needs_mikasa") else "tribal_chief"
        )
        await asyncio.sleep(0.5)

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
            message="Execution complete. Returning results to Tribal Chief.",
            data={"result": mikasa_result[:200] + "..." if len(mikasa_result) > 200 else mikasa_result},
            handoff_to="tribal_chief"
        )
        await asyncio.sleep(0.5)

    yield AgentEvent(
        agent="tribal_chief",
        status=AgentStatus.THINKING,
        message=f"All agents reporting in [{mode}]... synthesizing final answer..."
    )
    await asyncio.sleep(0.5)

    final_answer = await tribal_chief_synthesize(task, nezuko_result, mikasa_result)

    yield AgentEvent(
        agent="tribal_chief",
        status=AgentStatus.COMPLETE,
        message="Analysis complete.",
        data={"final_answer": final_answer}
    )
