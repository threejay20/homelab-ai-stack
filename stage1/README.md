# Local AI Infrastructure Stack

Production-grade local AI infrastructure built on Docker and WSL2,
designed to mirror enterprise MLOps deployment patterns at reduced scale.

## Architecture

┌─────────────────────────────────────────────┐
│              Docker Network                  │
│                                             │
│  ┌──────────┐    ┌─────────────────────┐   │
│  │  Ollama  │    │       MLflow        │   │
│  │ phi3:mini│    │  Experiment Tracker │   │
│  │ port 11434    │  Model Registry     │   │
│  └──────────┘    │  port 5000          │   │
│                  └──────────┬──────────┘   │
│  ┌──────────┐               │              │
│  │Portainer │    ┌──────────▼──────────┐   │
│  │Dashboard │    │     PostgreSQL      │   │
│  │port 9000 │    │   MLflow Backend    │   │
│  └──────────┘    │   port 5432         │   │
│                  └─────────────────────┘   │
└─────────────────────────────────────────────┘
## Stack

| Service | Version | Purpose |
|---|---|---|
| Ollama | 0.24.0 | Local LLM runtime — CPU inference |
| MLflow | 2.11.1 | Experiment tracking and model registry |
| PostgreSQL | 15 | MLflow persistence backend |
| Portainer CE | 2.39.2 | Container orchestration dashboard |

## Design Decisions

**Custom MLflow image** — Base MLflow image does not include the
psycopg2 PostgreSQL driver. A Dockerfile extending the base image
installs the dependency at build time, keeping the compose file clean.

**Healthcheck-gated startup** — MLflow depends on PostgreSQL with
a healthcheck condition, preventing connection failures during
cold starts.

**Memory limits per container** — Explicit `mem_limit` constraints
prevent any single service from exhausting available RAM on a
resource-constrained host.

**Named Docker network** — Services communicate by container name
over an isolated bridge network, eliminating hardcoded IPs.

## Prerequisites

- WSL2 (Ubuntu 22.04) on Windows 11
- Docker Desktop 27+
- 16GB RAM minimum recommended

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/homelab-ai-stack.git
cd homelab-ai-stack/stage1
cp .env.example .env
docker network create homelab-network
docker compose build
docker compose up -d
docker exec -it homelab-ollama ollama pull phi3:mini
```

## Service Endpoints

| Service | URL |
|---|---|
| MLflow UI | http://localhost:5000 |
| Portainer | http://localhost:9000 |
| Ollama API | http://localhost:11434 |

## Inference Benchmark

| Model | Parameters | Size | Hardware | Throughput |
|---|---|---|---|---|
| Phi-3 Mini | 3.8B | 2.2GB | Intel i7-1260P (CPU) | ~15 tok/s |

## Roadmap

- Stage 2 — RAG pipeline with Qdrant and LangChain
- Stage 3 — CI/CD pipeline for model deployment
- Stage 4 — Prometheus + Grafana + Evidently AI observability
- Stage 5 — Multi-agent orchestration with CrewAI
