import os
import subprocess
import httpx
import psutil
from langchain_ollama import OllamaLLM

# ─────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────
OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_PORT    = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
RAG_HOST       = os.getenv("RAG_HOST", "homelab-rag")
RAG_PORT       = os.getenv("RAG_PORT", "8000")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 10))

# ─────────────────────────────────────────
# LLM
# ─────────────────────────────────────────
llm = OllamaLLM(
    base_url=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
    model=OLLAMA_MODEL,
    temperature=0.1
)

# ─────────────────────────────────────────
# Tools
# ─────────────────────────────────────────
def rag_search(question: str) -> str:
    try:
        response = httpx.post(
            f"http://{RAG_HOST}:{RAG_PORT}/query",
            json={"question": question},
            timeout=120.0
        )
        data = response.json()
        return data.get("answer", "No answer found in documents")
    except Exception as e:
        return f"RAG search error: {str(e)}"


def docker_status(input: str = "") -> str:
    try:
        result = subprocess.run(
            ["docker", "ps", "--format",
             "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout if result.stdout else "No containers running"
        return f"Docker error: {result.stderr}"
    except Exception as e:
        return f"Docker status error: {str(e)}"


def system_info(input: str = "") -> str:
    try:
        cpu  = psutil.cpu_percent(interval=1)
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return (
            f"CPU usage: {cpu}%\n"
            f"Memory: {mem.used / (1024**3):.1f}GB used "
            f"of {mem.total / (1024**3):.1f}GB ({mem.percent}%)\n"
            f"Disk: {disk.used / (1024**3):.1f}GB used "
            f"of {disk.total / (1024**3):.1f}GB ({disk.percent}%)"
        )
    except Exception as e:
        return f"System info error: {str(e)}"


# ─────────────────────────────────────────
# Tool registry
# ─────────────────────────────────────────
TOOLS = {
    "rag_search": {
        "func": rag_search,
        "description": "Search internal documents and runbooks for procedures and guidance"
    },
    "docker_status": {
        "func": docker_status,
        "description": "Get the current status of all running Docker containers"
    },
    "system_info": {
        "func": system_info,
        "description": "Get current CPU, memory, and disk usage of the host system"
    }
}

# ─────────────────────────────────────────
# Step 1 — Route: LLM picks the right tool
# ─────────────────────────────────────────
def select_tool(question: str) -> str:
    tool_list = "\n".join(
        f"- {name}: {info['description']}"
        for name, info in TOOLS.items()
    )
    prompt = f"""You are a routing assistant. Given a question, select the best tool to answer it.

Available tools:
{tool_list}

Question: {question}

Respond with ONLY the tool name, nothing else. Choose from: {', '.join(TOOLS.keys())}
Tool:"""

    response = llm.invoke(prompt).strip().lower()

    # Extract tool name from response
    for tool_name in TOOLS.keys():
        if tool_name in response:
            return tool_name

    # Default fallback
    return "rag_search"


# ─────────────────────────────────────────
# Step 2 — Execute: run the selected tool
# ─────────────────────────────────────────
def execute_tool(tool_name: str, question: str) -> str:
    tool = TOOLS.get(tool_name)
    if not tool:
        return f"Unknown tool: {tool_name}"

    print(f"[Agent] Selected tool: {tool_name}")

    if tool_name == "rag_search":
        return tool["func"](question)
    else:
        return tool["func"]()


# ─────────────────────────────────────────
# Step 3 — Synthesize: LLM formats final answer
# ─────────────────────────────────────────
def synthesize_answer(question: str, tool_name: str, tool_result: str) -> str:
    prompt = f"""You are a DevOps assistant. Using the information below, answer the question clearly and concisely.

Question: {question}

Information from {tool_name}:
{tool_result}

Answer:"""

    return llm.invoke(prompt).strip()


# ─────────────────────────────────────────
# Main agent runner
# ─────────────────────────────────────────
def run_agent(question: str) -> dict:
    try:
        print(f"\n[Agent] Question: {question}")

        # Step 1 — select tool
        tool_name = select_tool(question)
        print(f"[Agent] Routing to: {tool_name}")

        # Step 2 — execute tool
        tool_result = execute_tool(tool_name, question)
        print(f"[Agent] Tool result: {tool_result[:200]}...")

        # Step 3 — synthesize answer
        answer = synthesize_answer(question, tool_name, tool_result)
        print(f"[Agent] Final answer: {answer[:200]}...")

        return {
            "question": question,
            "tool_used": tool_name,
            "answer": answer,
            "status": "success"
        }

    except Exception as e:
        return {
            "question": question,
            "tool_used": "none",
            "answer": f"Agent error: {str(e)}",
            "status": "error"
        }
