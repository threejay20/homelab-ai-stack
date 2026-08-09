# Stage 2.5 — DevOps AI Agent

Single-agent system with dynamic tool routing. The LLM decides which tools to use, executes them, and synthesizes a grounded answer from real data.

## What It Does

Receives a natural language query, uses the LLM to select the appropriate tools (RAG search, Docker status, system metrics), executes them, and returns a synthesized answer grounded in actual infrastructure data.

## Services

| Service | Port | Purpose |
|---|---|---|
| Agent API | 8001 | FastAPI agent endpoint |
| Socket Proxy | 2375 | Read-only Docker socket proxy |

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| /query | POST | Submit a query to the agent |
| /tools/docker | GET | Docker container status |
| /tools/system | GET | System resource metrics |
| /health | GET | Health check |

## Tools

| Tool | Source | What it returns |
|---|---|---|
| rag_search | Stage 2 RAG API | Knowledge base answers |
| docker_status | Socket proxy | Running containers and status |
| system_info | psutil | CPU, memory, disk metrics |

## Key Design Decisions

**Docker socket proxy instead of raw socket mount** — Mounting `/var/run/docker.sock` directly into a container gives it full Docker daemon access — the ability to start, stop, delete containers, pull images, and escape to the host. The socket proxy (tecnativa/docker-socket-proxy) acts as a firewall, allowing only CONTAINERS, INFO, PING, and VERSION API calls. The agent can see your infrastructure but cannot touch it.

**Two-step LLM routing** — Tool selection and answer synthesis are two separate LLM calls. The first call returns structured JSON (which tool to use, what query to pass). The second call receives the tool output and synthesizes a natural language answer. Separating these improves reliability — a smaller focused prompt for routing, a richer prompt for synthesis.

**DOCKER_HOST in compose environment block** — Setting DOCKER_HOST in the .env file causes build-time errors because Docker tries to use the proxy before it exists. Setting it in the docker-compose.yml environment block means it is only applied at runtime, after the proxy is running.

**phi3:mini for routing** — Tool selection uses phi3:mini (faster, smaller) rather than llama3.2:3b. The routing decision is a simple classification task that does not need a large model. Synthesis uses llama3.2:3b for better quality answers.

## AWS Equivalent

| Local | AWS |
|---|---|
| Agent API | Amazon Bedrock Agents |
| Tool routing | Bedrock Agent action groups |
| RAG search tool | Bedrock Knowledge Base retrieval |
| Docker socket proxy | AWS Systems Manager (read-only) |
| psutil metrics | Amazon CloudWatch agent |

## Quick Start

```bash
docker compose up -d

curl -X POST http://localhost:8001/query \
  -H "X-API-Key: homelab-agent-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many containers are running?"}'
```
