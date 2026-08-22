import os
import httpx
import asyncio
import boto3
import json
import subprocess
from langchain_ollama import OllamaLLM
from memory import save_conversation, load_recent_conversations, format_memory_context
from guardrails import check_input, check_output, GuardrailBlocked
from armin_tools import get_calendar_events, get_gmail_unread, get_drive_recent, get_notion_pages
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
BEDROCK_PLAN_MODEL  = os.getenv("BEDROCK_PLAN_MODEL", "amazon.nova-micro-v1:0")
BEDROCK_SYNTH_MODEL = os.getenv("BEDROCK_SYNTH_MODEL", "anthropic.claude-haiku-4-5-20251001-v1:0")

# ─────────────────────────────────────────
# Agent status enum
# ─────────────────────────────────────────
class AgentStatus(str, Enum):
    IDLE       = "idle"
    THINKING   = "thinking"
    ACTIVE     = "active"
    WAITING    = "waiting"
    PROCESSING = "processing"
    COMPLETE   = "complete"
    ERROR      = "error"

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

def bedrock_nova(prompt: str, model_id: str) -> str:
    client = get_bedrock_client()
    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 1000, "temperature": 0.1}
    }
    response = client.invoke_model(modelId=model_id, body=json.dumps(body))
    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"].strip()

def bedrock_haiku(prompt: str) -> str:
    client = get_bedrock_client()
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = client.invoke_model(modelId=BEDROCK_SYNTH_MODEL, body=json.dumps(body))
    result = json.loads(response["body"].read())
    return result["content"][0]["text"].strip()

def invoke_llm(prompt: str, use_bedrock_model: str = None) -> str:
    if USE_BEDROCK and use_bedrock_model:
        if "haiku" in use_bedrock_model:
            return bedrock_haiku(prompt)
        return bedrock_nova(prompt, use_bedrock_model)
    return llm.invoke(prompt).strip()

# ─────────────────────────────────────────
# Tribal Chief — Planner + Synthesizer
# ─────────────────────────────────────────
async def tribal_chief_plan(task: str) -> dict:
    recent = load_recent_conversations()
    memory_context = format_memory_context(recent)
    memory_section = f"\n\n{memory_context}" if memory_context else ""

    prompt = f"""You are Tribal Chief, a strategic AI planner. Analyze this task and decide which agents are needed.{memory_section}

Task: {task}

Available agents:
- Nezuko: searches internal documents and runbooks for knowledge and procedures
- Mikasa: checks Docker container status and system resource metrics
- Levi: security auditor - checks for security issues, exposed ports, API key health
- Eren: DevOps engineer - checks service health endpoints and deployment pipeline
- Armin: Personal assistant - checks Google Calendar, Gmail, Google Drive, and Notion

Rules:
- If the task mentions health, status, containers, metrics, system, infrastructure -> set needs_mikasa to true
- If the task mentions security, ports, audit, vulnerabilities -> set needs_levi to true
- If the task mentions health check, services, pipeline, deployment, CI/CD -> set needs_eren to true
- If the task mentions documents, runbooks, knowledge, procedures -> set needs_nezuko to true
- For general infrastructure questions, set needs_mikasa and needs_eren both to true
- If the task mentions calendar, schedule, email, gmail, drive, notion, meeting -> set needs_armin to true

Respond in this exact JSON format with no other text:
{{
    "needs_nezuko": false,
    "needs_mikasa": false,
    "needs_levi": false,
    "needs_eren": false,
    "needs_armin": false,
    "nezuko_query": "...",
    "armin_query": "...",
    "mikasa_query": "...",
    "levi_query": "...",
    "eren_query": "...",
    "plan": "one sentence describing approach"
}}"""

    try:
        response = invoke_llm(prompt, BEDROCK_PLAN_MODEL)
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(response[start:end])
            # Fix common LLM typo
            if "needs_ern" in parsed and "needs_eren" not in parsed:
                parsed["needs_eren"] = parsed.pop("needs_ern")

            # Keyword-based routing override — local LLM is unreliable
            task_lower = task.lower()
            security_keywords = ["security", "audit", "vulnerabil", "port", "exposure", "threat", "firewall", "api key", "breach", "hack", "pentest"]
            devops_keywords = ["health check", "service health", "pipeline", "deploy", "ci/cd", "endpoint", "uptime"]
            infra_keywords = ["container", "docker", "memory", "cpu", "disk", "metric", "system"]

            if any(k in task_lower for k in security_keywords):
                parsed["needs_levi"] = True
                parsed["needs_nezuko"] = False
                if not parsed.get("levi_query"):
                    parsed["levi_query"] = f"security audit: {task}"

            if any(k in task_lower for k in devops_keywords):
                parsed["needs_eren"] = True
                parsed["needs_nezuko"] = False
                if not parsed.get("eren_query"):
                    parsed["eren_query"] = f"check service health: {task}"

            if any(k in task_lower for k in infra_keywords):
                parsed["needs_mikasa"] = True
                parsed["needs_nezuko"] = False
                if not parsed.get("mikasa_query"):
                    parsed["mikasa_query"] = f"check infrastructure: {task}"

            personal_keywords = ["calendar", "schedule", "meeting", "email", "gmail", "inbox", "google drive", "notion", "my schedule", "my emails", "my calendar"]
            if any(k in task_lower for k in personal_keywords):
                parsed["needs_armin"] = True
                parsed["needs_eren"] = False
                parsed["needs_mikasa"] = False
                parsed["needs_nezuko"] = False
                if not parsed.get("armin_query"):
                    parsed["armin_query"] = f"personal assistant: {task}"

            return parsed
    except Exception as e:
        print(f"Plan error: {e}")
    return {
        "needs_nezuko": True,
        "needs_mikasa": True,
        "needs_levi": False,
        "needs_eren": False,
        "needs_armin": False,
        "nezuko_query": task,
        "mikasa_query": task,
        "levi_query": "",
        "eren_query": "",
        "armin_query": "",
        "plan": "Gathering information from all available sources"
    }

async def tribal_chief_synthesize(task: str, results: dict) -> str:
    sections = []
    if results.get("nezuko"):
        sections.append(f"Knowledge base findings (Nezuko):\n{results['nezuko']}")
    if results.get("mikasa"):
        sections.append(f"Infrastructure status (Mikasa):\n{results['mikasa']}")
    if results.get("levi"):
        sections.append(f"Security audit (Levi):\n{results['levi']}")
    if results.get("eren"):
        sections.append(f"DevOps status (Eren):\n{results['eren']}")
    if results.get("armin"):
        sections.append(f"Personal workspace (Armin):\n{results['armin']}")

    combined = "\n\n".join(sections) if sections else "No results gathered."

    prompt = f"""You are Tribal Chief, a strategic AI assistant. Synthesize these agent results into a clear, helpful answer.

Original question: {task}

{combined}

Provide a comprehensive, well-structured answer that directly addresses the question. Use plain text only - no markdown, no asterisks, no bullet points with asterisks. Use numbered lists or dashes instead.
Answer:"""

    return invoke_llm(prompt, BEDROCK_SYNTH_MODEL)

# ─────────────────────────────────────────
# Nezuko — Retriever
# ─────────────────────────────────────────
async def nezuko_search(query: str) -> str:
    if not query:
        return "No search required."
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
        return "No execution required."
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
# Levi — Security Auditor
# Checks security posture of the homelab
# ─────────────────────────────────────────
async def levi_audit(query: str) -> str:
    if not query:
        return "No security audit required."
    try:
        findings = []

        # Check exposed ports via docker
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                docker_response = await client.get(
                    f"http://{AGENT_HOST}:{AGENT_PORT}/tools/docker",
                    headers={"X-API-Key": AGENT_API_KEY}
                )
                docker_data = docker_response.json()
                findings.append(f"Container exposure:\n{docker_data.get('result', 'unavailable')}")
            except Exception as e:
                findings.append(f"Container check failed: {e}")

        # Check API key health
        api_checks = [
            ("RAG Pipeline", f"http://{RAG_HOST}:{RAG_PORT}/health", None),
            ("Agent API", f"http://{AGENT_HOST}:{AGENT_PORT}/health", None),
        ]
        for name, url, key in api_checks:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(url)
                    findings.append(f"{name}: HTTP {r.status_code} - {'OK' if r.status_code == 200 else 'ISSUE'}")
            except Exception as e:
                findings.append(f"{name}: Unreachable - {e}")

        # Auth check — verify endpoints reject bad keys
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"http://{RAG_HOST}:{RAG_PORT}/query",
                    json={"question": "test"},
                    headers={"X-API-Key": "bad-key"}
                )
                if r.status_code == 403:
                    findings.append("API auth enforcement: PASS - unauthorized requests rejected")
                else:
                    findings.append(f"API auth enforcement: WARN - returned {r.status_code} for bad key")
        except Exception as e:
            findings.append(f"Auth check failed: {e}")

        # Use LLM to analyze findings
        findings_text = "\n".join(findings)
        prompt = f"""You are Levi, a security auditor for a local development homelab stack. Analyze these security findings:

{findings_text}

Query: {query}

IMPORTANT CONTEXT: This is a LOCAL homelab running on WSL2 behind a home router NAT. Services bound to 0.0.0.0 are accessible on the LOCAL NETWORK ONLY - they are NOT exposed to the internet unless ports are explicitly forwarded through the router. Do not describe local services as "internet-exposed" or "publicly accessible".

Provide a concise security assessment focused on actual risks in this local context. Acknowledge what is working well before listing concerns."""

        analysis = invoke_llm(prompt, BEDROCK_PLAN_MODEL)
        return f"Security Findings:\n{findings_text}\n\nAnalysis:\n{analysis}"

    except Exception as e:
        return f"Security audit error: {str(e)}"

# ─────────────────────────────────────────
# Eren — DevOps Engineer
# Checks CI/CD, git, deployment health
# ─────────────────────────────────────────
async def eren_check(query: str) -> str:
    if not query:
        return "No DevOps check required."
    try:
        findings = []

        # Check all service health endpoints
        services = [
            ("RAG Pipeline",  f"http://{RAG_HOST}:{RAG_PORT}/health",  RAG_API_KEY),
            ("Agent API",     f"http://{AGENT_HOST}:{AGENT_PORT}/health", AGENT_API_KEY),
            ("Orchestrator",  f"http://localhost:8002/health", None),
        ]

        async with httpx.AsyncClient(timeout=10.0) as client:
            for name, url, key in services:
                try:
                    headers = {"X-API-Key": key} if key else {}
                    r = await client.get(url, headers=headers)
                    findings.append(f"{name}: {'HEALTHY' if r.status_code == 200 else 'DEGRADED'} (HTTP {r.status_code})")
                except Exception as e:
                    findings.append(f"{name}: UNREACHABLE - {e}")

        # Check Prometheus targets
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get("http://homelab-prometheus:9090/api/v1/targets")
                if r.status_code == 200:
                    data = r.json()
                    active = data.get("data", {}).get("activeTargets", [])
                    up = sum(1 for t in active if t.get("health") == "up")
                    total = len(active)
                    findings.append(f"Prometheus targets: {up}/{total} UP")
                else:
                    findings.append("Prometheus: unreachable")
        except Exception as e:
            findings.append(f"Prometheus check failed: {e}")

        # Check system resources for DevOps concerns
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.get(
                    f"http://{AGENT_HOST}:{AGENT_PORT}/tools/system",
                    headers={"X-API-Key": AGENT_API_KEY}
                )
                system_data = r.json()
                findings.append(f"System resources:\n{system_data.get('result', 'unavailable')}")
            except Exception as e:
                findings.append(f"System check failed: {e}")

        findings_text = "\n".join(findings)
        prompt = f"""You are Eren, a DevOps engineer. Analyze these infrastructure findings:

{findings_text}

Query: {query}

Provide a concise DevOps status report with any issues and recommended actions."""

        analysis = invoke_llm(prompt, BEDROCK_PLAN_MODEL)
        return f"DevOps Findings:\n{findings_text}\n\nAnalysis:\n{analysis}"

    except Exception as e:
        return f"DevOps check error: {str(e)}"

# ─────────────────────────────────────────
# Armin — Personal Assistant
# Handles calendar, email, drive, notion
# ─────────────────────────────────────────
async def armin_assist(query: str) -> str:
    if not query:
        return "No personal assistant query required."
    try:
        results = []
        query_lower = query.lower()

        if any(k in query_lower for k in ["calendar", "schedule", "meeting", "event", "today", "tomorrow", "week"]):
            days = 1 if "today" in query_lower else 2 if "tomorrow" in query_lower else 7
            results.append(get_calendar_events(days_ahead=days))

        if any(k in query_lower for k in ["email", "gmail", "inbox", "unread", "message"]):
            results.append(get_gmail_unread())

        if any(k in query_lower for k in ["drive", "file", "document", "sheet", "doc"]):
            results.append(get_drive_recent())

        if any(k in query_lower for k in ["notion", "note", "page", "wiki"]):
            results.append(get_notion_pages(NOTION_TOKEN))

        if not results:
            results.append(get_calendar_events(days_ahead=7))
            results.append(get_gmail_unread())

        return "\n\n".join(results)
    except Exception as e:
        return f"Assistant error: {str(e)}"

# ─────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────
async def run_multiagent(task: str):
    mode = "BEDROCK" if USE_BEDROCK else "LOCAL"

    # Apply guardrail to user input before processing
    try:
        task = check_input(task)
    except GuardrailBlocked as e:
        yield AgentEvent(
            agent="tribal_chief",
            status=AgentStatus.ERROR,
            message=e.message
        )
        return

    yield AgentEvent(
        agent="tribal_chief",
        status=AgentStatus.THINKING,
        message=f"Analyzing your request [{mode}] and forming a plan..."
    )
    await asyncio.sleep(0.5)

    plan = await tribal_chief_plan(task)
    results = {}

    first_agent = ("nezuko" if plan.get("needs_nezuko") else
                   "mikasa" if plan.get("needs_mikasa") else
                   "levi" if plan.get("needs_levi") else
                   "eren" if plan.get("needs_eren") else
                   "armin" if plan.get("needs_armin") else "tribal_chief")

    yield AgentEvent(
        agent="tribal_chief",
        status=AgentStatus.ACTIVE,
        message=plan.get("plan", "Planning complete"),
        data=plan,
        handoff_to=first_agent
    )
    await asyncio.sleep(0.5)

    if first_agent != "tribal_chief":
        yield AgentEvent(
            agent="tribal_chief",
            status=AgentStatus.WAITING,
            message="Delegated. Waiting for agents to report back..."
        )
        await asyncio.sleep(0.3)

    # Nezuko
    if plan.get("needs_nezuko") and plan.get("nezuko_query"):
        yield AgentEvent(agent="nezuko", status=AgentStatus.THINKING,
            message="Entering the archive... searching knowledge base...")
        await asyncio.sleep(0.5)
        yield AgentEvent(agent="nezuko", status=AgentStatus.ACTIVE,
            message=f"Searching for: {plan['nezuko_query']}")
        results["nezuko"] = await nezuko_search(plan["nezuko_query"])
        next_agent = "mikasa" if plan.get("needs_mikasa") else "levi" if plan.get("needs_levi") else "eren" if plan.get("needs_eren") else "tribal_chief"
        yield AgentEvent(agent="nezuko", status=AgentStatus.COMPLETE,
            message="Search complete. Passing findings forward.",
            data={"result": results["nezuko"][:200] + "..." if len(results["nezuko"]) > 200 else results["nezuko"]},
            handoff_to=next_agent)
        await asyncio.sleep(0.5)

    # Mikasa
    if plan.get("needs_mikasa") and plan.get("mikasa_query"):
        yield AgentEvent(agent="mikasa", status=AgentStatus.THINKING,
            message="Entering the operations bay... running infrastructure checks...")
        await asyncio.sleep(0.5)
        yield AgentEvent(agent="mikasa", status=AgentStatus.ACTIVE,
            message="Checking container status and system metrics...")
        results["mikasa"] = await mikasa_execute(plan["mikasa_query"])
        next_agent = "levi" if plan.get("needs_levi") else "eren" if plan.get("needs_eren") else "tribal_chief"
        yield AgentEvent(agent="mikasa", status=AgentStatus.COMPLETE,
            message="Execution complete. Passing results forward.",
            data={"result": results["mikasa"][:200] + "..." if len(results["mikasa"]) > 200 else results["mikasa"]},
            handoff_to=next_agent)
        await asyncio.sleep(0.5)

    # Levi
    if plan.get("needs_levi") and plan.get("levi_query"):
        yield AgentEvent(agent="levi", status=AgentStatus.THINKING,
            message="Initiating security audit... scanning the perimeter...")
        await asyncio.sleep(0.5)
        yield AgentEvent(agent="levi", status=AgentStatus.ACTIVE,
            message=f"Auditing: {plan['levi_query']}")
        results["levi"] = await levi_audit(plan["levi_query"])
        next_agent = "eren" if plan.get("needs_eren") else "tribal_chief"
        yield AgentEvent(agent="levi", status=AgentStatus.COMPLETE,
            message="Security audit complete. Reporting to Tribal Chief.",
            data={"result": results["levi"][:200] + "..." if len(results["levi"]) > 200 else results["levi"]},
            handoff_to=next_agent)
        await asyncio.sleep(0.5)

    # Eren
    if plan.get("needs_eren") and plan.get("eren_query"):
        yield AgentEvent(agent="eren", status=AgentStatus.THINKING,
            message="Checking deployment pipeline... reviewing infrastructure health...")
        await asyncio.sleep(0.5)
        yield AgentEvent(agent="eren", status=AgentStatus.ACTIVE,
            message=f"Checking: {plan['eren_query']}")
        results["eren"] = await eren_check(plan["eren_query"])
        yield AgentEvent(agent="eren", status=AgentStatus.COMPLETE,
            message="DevOps check complete. Reporting to Tribal Chief.",
            data={"result": results["eren"][:200] + "..." if len(results["eren"]) > 200 else results["eren"]},
            handoff_to="tribal_chief")
        await asyncio.sleep(0.5)

    # Armin
    if plan.get("needs_armin") and plan.get("armin_query"):
        yield AgentEvent(agent="armin", status=AgentStatus.THINKING,
            message="Checking your calendar, email and workspace...")
        await asyncio.sleep(0.5)
        yield AgentEvent(agent="armin", status=AgentStatus.ACTIVE,
            message=f"Fetching: {plan['armin_query']}")
        results["armin"] = await armin_assist(plan["armin_query"])
        yield AgentEvent(agent="armin", status=AgentStatus.COMPLETE,
            message="Workspace data retrieved. Reporting to Tribal Chief.",
            data={"result": results["armin"][:200] + "..." if len(results["armin"]) > 200 else results["armin"]},
            handoff_to="tribal_chief")
        await asyncio.sleep(0.5)

    # Tribal Chief synthesizes
    yield AgentEvent(agent="tribal_chief", status=AgentStatus.PROCESSING,
        message=f"All agents reporting in [{mode}]... synthesizing final answer...")
    await asyncio.sleep(0.5)

    final_answer = await tribal_chief_synthesize(task, results)

    # Apply guardrail to output
    try:
        final_answer = check_output(final_answer)
    except GuardrailBlocked as e:
        final_answer = e.message

    # Save to memory
    agents_used = [k for k, v in results.items() if v and v != "No search performed." and v != "No execution required." and v != "No security audit required." and v != "No DevOps check required."]
    agents_used = ["tribal_chief"] + agents_used
    save_conversation(task, plan, final_answer, agents_used, mode)

    yield AgentEvent(agent="tribal_chief", status=AgentStatus.COMPLETE,
        message="Analysis complete.",
        data={"final_answer": final_answer})
