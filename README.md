# Homelab AI Command Center

> A production-grade local AI infrastructure stack implementing enterprise MLOps and LLMOps patterns — fully air-gapped, zero cloud dependency, built from scratch.

![Architecture](docs/architecture.png)

**Live multi-agent system** where three specialized AI agents — Tribal Chief (Director), Nezuko (Researcher), and Mikasa (Executor) — collaborate in real time to answer questions, search knowledge bases, and inspect infrastructure. Speak to them via voice. Watch them walk across an animated office to hand off tasks.

---

## What This Demonstrates

Most engineers understand AI concepts. Few have built the full stack that runs them in production. This project implements the complete picture:

| Capability | Implementation | AWS Equivalent |
|---|---|---|
| LLM serving | Ollama + llama3.2:3b + phi3:mini | Bedrock InvokeModel |
| Vector search + RAG | Qdrant + LangChain + sentence-transformers | Bedrock Knowledge Bases |
| Multi-agent orchestration | Custom async agent pipeline + WebSocket streaming | Bedrock Agents + Action Groups |
| AI evaluation pipeline | pytest + 32 eval tests + GitHub Actions | SageMaker Pipelines |
| Experiment tracking | MLflow 2.11.1 + PostgreSQL | SageMaker Experiments |
| Observability | Prometheus + Grafana + Evidently AI | CloudWatch + Managed Grafana |
| Security | API key auth + Docker socket proxy + threat model | IAM + API Gateway |
| Voice interface | Web Speech API + ElevenLabs TTS | Lex + Polly |
| Live UI | React + isometric office + animated agents | CloudFront + S3 |

Built entirely on open-source tools. Runs on a laptop. Maps directly to AWS managed services.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOMELAB AI COMMAND CENTER                     │
│                                                                  │
│  ┌──────────────┐    WebSocket     ┌──────────────────────────┐  │
│  │   React UI   │◄────────────────►│   Multi-Agent Pipeline   │  │
│  │  (Stage 6)   │                  │       (Stage 5)          │  │
│  │              │                  │                          │  │
│  │ Isometric    │                  │  Tribal Chief (Planner)  │  │
│  │ office scene │                  │  Nezuko    (Retriever)   │  │
│  │ Voice I/O    │                  │  Mikasa    (Executor)    │  │
│  └──────────────┘                  └────────┬─────────────────┘  │
│                                             │                    │
│              ┌──────────────────────────────┼──────────────────┐ │
│              │                             │                   │ │
│    ┌─────────▼──────┐           ┌──────────▼──────┐           │ │
│    │  RAG Pipeline  │           │   Agent Tools   │           │ │
│    │   (Stage 2)    │           │  (Stage 2.5)    │           │ │
│    │                │           │                 │           │ │
│    │ Qdrant vectors │           │ Docker status   │           │ │
│    │ LangChain      │           │ System metrics  │           │ │
│    │ FastAPI        │           │ Socket proxy    │           │ │
│    └───────┬────────┘           └─────────────────┘           │ │
│            │                                                   │ │
│    ┌───────▼────────┐  ┌─────────────┐  ┌──────────────────┐  │ │
│    │  Local LLMs    │  │   MLflow    │  │  Observability   │  │ │
│    │   (Stage 1)    │  │  (Stage 1)  │  │   (Stage 4)      │  │ │
│    │                │  │             │  │                  │  │ │
│    │ llama3.2:3b    │  │ Experiment  │  │ Prometheus       │  │ │
│    │ phi3:mini      │  │ tracking    │  │ Grafana          │  │ │
│    │ Ollama         │  │ PostgreSQL  │  │ Evidently AI     │  │ │
│    └────────────────┘  └─────────────┘  └──────────────────┘  │ │
│                                                                 │ │
│    ┌────────────────────────────────────────────────────────┐  │ │
│    │              CI/CD + Security (Stage 3 + Security)     │  │ │
│    │  GitHub Actions · pytest 32 tests · API key auth ·     │  │ │
│    │  Docker socket proxy · Threat model documented         │  │ │
│    └────────────────────────────────────────────────────────┘  │ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stack at a Glance

```
Runtime:      Windows 11 + WSL2 (Ubuntu 22.04)
Hardware:     Intel i7-1260P · 16GB RAM · CPU-only inference
LLM:          llama3.2:3b + phi3:mini via Ollama
Embeddings:   all-MiniLM-L6-v2 (384-dim) via sentence-transformers
Vector DB:    Qdrant
Orchestration: LangChain + custom async agent pipeline
API:          FastAPI + Pydantic
Streaming:    WebSocket (real-time agent events)
Tracking:     MLflow 2.11.1 + PostgreSQL
Monitoring:   Prometheus + Grafana + Evidently AI
CI/CD:        GitHub Actions (build + eval pipeline)
Testing:      pytest (32 tests, 100% passing)
UI:           React 18 + Vite + Nginx
Voice:        Web Speech API + ElevenLabs TTS
Containers:   Docker Compose (14 services)
```

---

## Stages

### [Stage 1 — Local AI Serving Stack](./stage1)
Ollama serving llama3.2:3b and phi3:mini with MLflow experiment tracking backed by PostgreSQL. The foundation everything else builds on.

**Key decisions:** Named Docker volumes for data persistence, custom MLflow image with psycopg2, healthcheck patterns on all services, Portainer for container management.

### [Stage 2 — RAG Pipeline](./stage2)
Production-grade Retrieval-Augmented Generation pipeline. Documents are chunked, embedded, and stored in Qdrant. Queries are semantically searched and answered by the local LLM with retrieved context.

**Key decisions:** all-MiniLM-L6-v2 baked into the Docker image at build time (no runtime downloads), API key authentication on all endpoints, Prometheus metrics instrumented (request counters, latency histograms, chunks ingested), Evidently AI integration for answer quality monitoring.

**Endpoints:** `/ingest` · `/query` · `/collections` · `/health` · `/metrics`

### [Stage 2.5 — DevOps AI Agent](./stage2.5)
Single-agent system with tool routing. The LLM selects which tool to invoke (RAG search, Docker inspection, system metrics), executes it, and synthesizes a grounded answer.

**Key decisions:** Docker socket proxy instead of raw socket mount — agent can inspect containers but cannot control them. Two-step LLM routing pattern: `select_tool()` → `execute_tool()` → `synthesize_answer()`.

### [Stage 3 — CI/CD Evaluation Pipeline](./stage3)
32 pytest tests covering RAG retrieval quality, authentication regression, agent tool routing correctness, and response contract validation. GitHub Actions runs build validation and test suite on every push.

**Key decisions:** CI runs syntax validation only (no LLM inference on CI), local runs execute full eval against live endpoints, tests structured as regression guards not unit tests.

**Test coverage:** RAG health · auth regression · ingestion · retrieval quality · agent routing · response contracts

### [Security](./security)
API key authentication on all FastAPI endpoints, Docker socket proxy restricting agent access to read-only container operations, documented threat model with attack surface analysis and intentional tradeoffs.

### [Stage 4 — Monitoring + Observability](./stage4)
Prometheus scraping four targets with 15-day retention, Grafana dashboard auto-provisioned from JSON on startup, Node Exporter for host metrics, Evidently AI for RAG answer quality drift detection.

**Ports:** Prometheus :9090 · Grafana :3000 · Evidently :8050 · Node Exporter :9100

### [Stage 5 — Multi-Agent Orchestration](./stage5)
Three-agent system with specialized roles, real-time WebSocket streaming, and live handoff coordination. Tribal Chief plans and synthesizes. Nezuko retrieves from the knowledge base. Mikasa executes infrastructure tools.

**Key decisions:** Async generator pipeline yields AgentEvents for streaming. Each agent has a distinct system prompt, toolset, and responsibility boundary. WebSocket enables real-time UI updates without polling.

**Endpoints:** `WS /ws` · `POST /task` · `GET /health`

### [Stage 6 — Live Agent UI](./stage6)
React frontend with an animated isometric office environment. Characters walk between desks to hand off tasks. Slack-style chat panel streams agent activity in real time. Voice input via Web Speech API, voice output via ElevenLabs TTS (fires only when mic is used).

**Key decisions:** HTML Canvas abandoned in favour of absolutely-positioned sprite images over a pre-rendered background — this is how games like Gather.town achieve quality at this fidelity. `useRoomScale` hook scales all elements proportionally. Animation queue processes walk steps sequentially so transitions complete before the next step begins.

---

## Quick Start

### Prerequisites
- Docker Desktop with WSL2 backend
- 8GB+ RAM available to Docker
- ~10GB disk for models

### Start sequence
```bash
# Security and foundation first
docker compose -f security/docker-compose.yml up -d
docker compose -f stage1/docker-compose.yml up -d

# AI services
docker compose -f stage2/docker-compose.yml up -d
docker compose -f stage2.5/docker-compose.yml up -d

# Observability
docker compose -f stage4/docker-compose.yml up -d

# Agents and UI
docker compose -f stage5/docker-compose.yml up -d
docker compose -f stage6/docker-compose.yml up -d
```

### Verify all 14 containers are running
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | sort
```

### Access points
| Service | URL | Credentials |
|---|---|---|
| Agent UI | http://localhost:3001 | — |
| Grafana | http://localhost:3000 | admin / homelab123 |
| MLflow | http://localhost:5000 | — |
| Portainer | http://localhost:9000 | — |
| Prometheus | http://localhost:9090 | — |
| Evidently | http://localhost:8050 | — |

### Ingest knowledge base
```bash
bash scripts/ingest_knowledge.sh
```

---

## CI/CD

[![AI Eval Pipeline](https://github.com/threejay20/homelab-ai-stack/actions/workflows/ai-eval.yml/badge.svg)](https://github.com/threejay20/homelab-ai-stack/actions/workflows/ai-eval.yml)

Every push to `main` triggers:
1. **Build validation** — Docker images build successfully
2. **Eval suite** — 32 pytest tests covering RAG quality, auth, agent routing, and response contracts

```bash
# Run full eval suite locally (requires all containers running)
cd stage3
pytest tests/ -v
```

---

## Security Model

| Control | Implementation |
|---|---|
| API authentication | API key via `X-API-Key` header on all endpoints |
| Container isolation | Docker socket proxy — read-only, no raw socket mount |
| Secret management | `.env` files gitignored, `.env.example` templates provided |
| Network isolation | Services communicate by name on internal Docker network |
| Threat model | Documented in [SECURITY.md](./SECURITY.md) |

---

## Roadmap

- [ ] AWS Bedrock integration — route complex queries to Claude, compare local vs cloud
- [ ] Bedrock Knowledge Bases — replicate RAG pipeline on managed AWS service
- [ ] Bedrock Guardrails — responsible AI content filtering
- [ ] Additional agents — Levi (Security), Eren (DevOps), Armin (Strategy)
- [ ] Conversation memory — persist context across sessions in PostgreSQL
- [ ] AWS deployment — ECS + API Gateway + CloudFront

---

## Certifications

Built as hands-on preparation for:
- ✅ AWS Cloud Practitioner
- ✅ AWS Solutions Architect Associate (SAA-C03)
- 🎯 AWS Certified Generative AI Developer — Professional (AIP-C01)

Every component maps to an AIP-C01 exam domain. The lab is the study guide.

---

## Author

**Justin** — Senior DevOps Engineer at CallTek · Founder of Thirdmark  
AWS Certified (CCP, SAA-C03) · Pivoting to MLOps / AI Platform Engineering

[GitHub](https://github.com/threejay20) · [LinkedIn](https://linkedin.com/in/justin-jjohnson)
