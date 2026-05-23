# DevOps AI Agent

Autonomous agent that routes natural language questions to specialized
tools and synthesizes grounded answers. Designed for infrastructure
operations use cases — container status, system resources, and
internal runbook retrieval.

## Architecture

User Question
│
▼
LLM Router (llama3.2:3b)
Reads question intent,
selects best tool
│
├──► rag_search ──► RAG Pipeline (Stage 2) ──► Document answer
│
├──► docker_status ──► Docker socket ──► Container state
│
└──► system_info ──► psutil ──► CPU / memory / disk
│
▼
LLM Synthesizer
Formats tool output
into a clean answer
│
▼
Final Answer

## Tools

| Tool | Trigger | Data Source |
|---|---|---|
| `rag_search` | Procedural questions, how-to, troubleshooting | Stage 2 RAG pipeline |
| `docker_status` | Container state, running services, ports | Host Docker socket |
| `system_info` | CPU, memory, disk usage | psutil host metrics |

## Design Decisions

**Two-step LLM pattern** — the agent makes two LLM calls per request:
one to route (select the right tool) and one to synthesize (format
the answer). Separating these concerns produces more reliable routing
and cleaner output than asking a single prompt to do both.

**Python routing over ReAct** — smaller local models (3-8B parameters)
struggle with strict ReAct format compliance. Handling tool selection
in Python and reserving LLM calls for reasoning tasks produces
consistent results on CPU-only hardware without requiring larger
models or external APIs.

**Docker-out-of-Docker** — the agent container accesses host container
state via a Unix socket mount (`/var/run/docker.sock`). No separate
Docker daemon runs inside the container — it borrows the host daemon
directly. Same pattern used by Portainer.

**RAG as a microservice** — the agent calls the Stage 2 RAG pipeline
over HTTP rather than embedding retrieval logic directly. This keeps
each service independently deployable and testable, and allows the
RAG pipeline to be upgraded without rebuilding the agent.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Tool connectivity check |
| POST | /agent | Natural language question → grounded answer |
| GET | /tools/docker | Call docker_status directly |
| GET | /tools/system | Call system_info directly |
| POST | /tools/rag | Call rag_search directly |

## Quick Start

```bash
# Stage 1 and Stage 2 must be running first
cd stage2.5
cp .env.example .env
docker compose build
docker compose up -d
```

```bash
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/json" \
  -d '{"question": "What containers are running and how is memory usage?"}'
```

## Prerequisites

- Stage 1 running — provides Ollama LLM inference
- Stage 2 running — provides RAG pipeline for document search

## Performance

| Operation | Model | Latency |
|---|---|---|
| Tool routing | llama3.2:3b (CPU) | ~5-10s |
| RAG retrieval + synthesis | llama3.2:3b + phi3:mini (CPU) | ~60-80s |
| Docker/system tools | llama3.2:3b (CPU) | ~10-15s |

## AWS Bedrock Equivalent

| Local Component | Bedrock Equivalent |
|---|---|
| LLM router (llama3.2:3b) | Bedrock InvokeModel — Claude Haiku |
| rag_search tool | Bedrock Knowledge Bases RetrieveAndGenerate |
| docker_status tool | Lambda function + ECS DescribeTasks API |
| system_info tool | Lambda function + CloudWatch GetMetricData |
| Agent orchestration | Bedrock Agents + Action Groups |
