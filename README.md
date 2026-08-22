# AI Command Center

> A production-grade AI infrastructure stack — 6 specialized agents, local LLM serving, RAG pipeline, AWS Bedrock integration, Google Workspace connectivity, and a live animated office UI. Runs locally for free. Deploys to AWS on demand.

![AI Command Center](docs/architecture.png)

Six AI agents collaborate in real time inside an animated isometric office. Speak a query via microphone. Watch Tribal Chief analyze it, walk across the office to the right agent, wait for results, then walk back to synthesize the answer in Claude Haiku's voice.

---

## Agents

| Agent | Role | Color | Capability |
|---|---|---|---|
| Tribal Chief | Director | Blue | Orchestrates tasks, delegates, synthesizes, remembers conversation history |
| Nezuko | Researcher | Pink | Semantic search across a RAG knowledge base |
| Mikasa | Executor | Red | Docker container status and system metrics |
| Levi | Security | Green | Live security audits — ports, API keys, auth enforcement |
| Eren | DevOps | Amber | Service health endpoints and Prometheus targets |
| Armin | Assistant | Purple | Google Calendar, Gmail, Drive, and Notion |

---

## What This Demonstrates

This project implements the full AI infrastructure stack from local LLM serving to multi-agent orchestration, evaluation, observability, Google Workspace integration, AWS Bedrock Guardrails, and a live voice-enabled UI. Every component maps to an AWS managed service:

| Local Implementation | AWS Equivalent |
|---|---|
| Ollama + llama3.2:3b | Bedrock InvokeModel |
| Qdrant + LangChain RAG | Bedrock Knowledge Bases |
| 6-agent async pipeline | Bedrock Agents + Action Groups |
| Bedrock Guardrails | Amazon Bedrock Guardrails |
| pytest + GitHub Actions | SageMaker Pipelines |
| MLflow + PostgreSQL | SageMaker Experiments |
| Prometheus + Grafana | CloudWatch + Managed Grafana |
| Evidently AI | SageMaker Model Monitor |
| APScheduler morning briefing | Amazon EventBridge |
| ECS Fargate + S3 + CloudFront | Production AWS stack |

---

## Architecture

```
+------------------------------------------------------------------+
|                      AI COMMAND CENTER                            |
|                                                                   |
|  +--------------+    WebSocket     +--------------------------+   |
|  |   React UI   |<---------------->|   Multi-Agent Pipeline   |   |
|  |  (Stage 6)   |                  |       (Stage 5)          |   |
|  |              |                  |                          |   |
|  | Isometric    |                  |  Tribal Chief (Director) |   |
|  | office scene |                  |  Nezuko    (Researcher)  |   |
|  | Voice I/O    |                  |  Mikasa    (Executor)    |   |
|  | 6 characters |                  |  Levi      (Security)    |   |
|  +--------------+                  |  Eren      (DevOps)      |   |
|                                    |  Armin     (Assistant)   |   |
|                                    +----------+---------------+   |
|                                               |                   |
|    +------------------------------------------+                  |
|    |              |              |             |                  |
|  +-+----------+ +-+--------+ +--+-------+ +---+----------+       |
|  | RAG        | | Agent    | | Bedrock  | | Google       |       |
|  | Pipeline   | | Tools    | | Guards   | | Workspace    |       |
|  | (Stage 2)  | | (2.5)    | | rails    | | Calendar     |       |
|  | Qdrant     | | Docker   | | Content  | | Gmail        |       |
|  | LangChain  | | Metrics  | | Filter   | | Drive        |       |
|  | FastAPI    | | System   | | PII      | | Notion       |       |
|  +------------+ +----------+ +----------+ +--------------+       |
|                                                                   |
|  +------------+  +----------+  +------------------+              |
|  | Local LLMs |  | MLflow   |  | Observability    |              |
|  | (Stage 1)  |  | Tracking |  | (Stage 4)        |              |
|  | llama3.2   |  | Postgres |  | Prometheus       |              |
|  | phi3:mini  |  |          |  | Grafana          |              |
|  | Ollama     |  |          |  | Evidently AI     |              |
|  +------------+  +----------+  +------------------+              |
|                                                                   |
|  +-------------------------------------------------------------+  |
|  | CI/CD + Security                                            |  |
|  | GitHub Actions * 32 pytest tests * API key auth *           |  |
|  | Docker socket proxy * Bedrock Guardrails * 127.0.0.1        |  |
|  +-------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

---

## Stack

```
Runtime:       Windows 11 + WSL2 (Ubuntu 22.04)
Hardware:      Intel i7-1260P * 16GB RAM * CPU-only inference
LLM (local):   llama3.2:3b + phi3:mini via Ollama
LLM (cloud):   Nova Micro (planning) + Claude Haiku 4.5 (synthesis) via Bedrock
Embeddings:    all-MiniLM-L6-v2 (384-dim) via sentence-transformers
Vector DB:     Qdrant
Orchestration: LangChain + custom async agent pipeline
API:           FastAPI + Pydantic
Streaming:     WebSocket (real-time agent events)
Memory:        PostgreSQL (conversation history)
Tracking:      MLflow 2.11.1 + PostgreSQL
Monitoring:    Prometheus + Grafana + Evidently AI
Scheduler:     APScheduler (morning briefing 8AM EST)
CI/CD:         GitHub Actions (32 pytest evaluation tests)
UI:            React 18 + Vite + Nginx
Voice:         Web Speech API + ElevenLabs TTS
Containers:    Docker Compose (14 services)
Cloud:         ECS Fargate + S3 + CloudFront + ECR
```

---

## Stages

### [Stage 1 — Local AI Serving](./stage1)
Ollama + MLflow + PostgreSQL + Portainer. The foundation layer.

### [Stage 2 — RAG Pipeline](./stage2)
Qdrant + LangChain + sentence-transformers + FastAPI. Document ingestion, semantic search, grounded answers. Prometheus metrics instrumented.

### [Stage 2.5 — DevOps Agent](./stage2.5)
Single-agent tool routing. Docker socket proxy for read-only container inspection.

### [Stage 3 — CI/CD Evaluation](./stage3)
32 pytest tests on GitHub Actions. RAG quality, auth regression, agent routing, response contracts.

### [Security](./security)
API key auth, Docker socket proxy, all management services bound to 127.0.0.1, documented threat model.

### [Stage 4 — Observability](./stage4)
Prometheus + Grafana (auto-provisioned dashboard) + Node Exporter + Evidently AI for RAG quality monitoring.

### [Stage 5 — Multi-Agent Orchestration](./stage5)
Six agents with keyword routing, Bedrock integration, Bedrock Guardrails, conversation memory, Google Workspace integration, automated morning briefing, and Stop functionality.

### [Stage 6 — Live Agent UI](./stage6)
Animated isometric office, 6 character sprites, ElevenLabs voice per agent, walk animations, Slack-style chat panel, Stop button.

---

## Quick Start

### Prerequisites
- Docker Desktop with WSL2 backend
- 8GB+ RAM
- ~10GB disk for models

### Start
```bash
cd ~/homelab
docker compose -f security/docker-compose.yml up -d
docker compose -f stage1/docker-compose.yml up -d
docker compose -f stage2/docker-compose.yml up -d
docker compose -f stage2.5/docker-compose.yml up -d
docker compose -f stage4/docker-compose.yml up -d
docker compose -f stage5/docker-compose.yml up -d
docker compose -f stage6/docker-compose.yml up -d
```

### Verify
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | sort
```

### Access
| Service | URL | Credentials |
|---|---|---|
| AI Command Center UI | http://localhost:3001 | — |
| Grafana | http://localhost:3000 | admin / homelab123 |
| MLflow | http://localhost:5000 | — |
| Portainer | http://localhost:9000 | — |
| Prometheus | http://localhost:9090 | — |

### Ingest Knowledge Base
```bash
bash scripts/ingest_knowledge.sh
```

---

## AWS Deployment

```bash
# Deploy for demos
bash scripts/aws-deploy.sh

# Tear down to stop charges
bash scripts/aws-teardown.sh
```

Estimated cost: ~$0.05-0.10/hour while running. Tear down after demos.

---

## AWS Bedrock

```bash
# Enable cloud LLM (Nova Micro + Claude Haiku 4.5)
sed -i 's/USE_BEDROCK=false/USE_BEDROCK=true/' stage5/.env
cd stage5 && docker compose up -d

# Disable (back to local Ollama)
sed -i 's/USE_BEDROCK=true/USE_BEDROCK=false/' stage5/.env
cd stage5 && docker compose up -d
```

Cost: ~$0.002 per query. Estimated $1-3/month for daily use.

---

## CI/CD

[![AI Eval Pipeline](https://github.com/threejay20/homelab-ai-stack/actions/workflows/ai-eval.yml/badge.svg)](https://github.com/threejay20/homelab-ai-stack/actions/workflows/ai-eval.yml)

---

## Security

| Control | Implementation |
|---|---|
| API authentication | X-API-Key header on all endpoints |
| Container isolation | Docker socket proxy — read-only |
| Content safety | AWS Bedrock Guardrails |
| Port binding | Management services on 127.0.0.1 only |
| Secret management | .env gitignored, .env.example provided |
| Threat model | Documented in SECURITY.md |

---

## Certifications

Built as preparation for:
- AWS Cloud Practitioner ✅
- AWS Solutions Architect Associate SAA-C03 ✅
- AWS Certified Generative AI Developer Professional AIP-C01 🎯

---

## Author

**Justin** — Senior DevOps Engineer * Founder of Thirdmark
AWS Certified (CCP, SAA-C03)

[GitHub](https://github.com/threejay20) * [LinkedIn](https://linkedin.com/in/justinjjohnson1)
