# Stage 1 — Local AI Serving Stack

The foundation layer. Everything else in the lab depends on this stage being healthy.

## What It Does

Serves two local LLMs via Ollama, tracks experiments via MLflow backed by PostgreSQL, and provides container management via Portainer. No cloud dependency — all inference runs on CPU.

## Services

| Service | Port | Purpose |
|---|---|---|
| Ollama | 11434 | LLM inference server |
| MLflow | 5000 | Experiment tracking UI + API |
| PostgreSQL | 5432 | MLflow backend store |
| Portainer | 9000 | Container management UI |

## Models

| Model | Size | Use case |
|---|---|---|
| llama3.2:3b | 2.0GB | Primary reasoning, synthesis |
| phi3:mini | 2.3GB | Fast routing, tool selection |

## Key Design Decisions

**Custom MLflow Dockerfile** — The official MLflow image does not include psycopg2 (PostgreSQL driver). Rather than installing it at runtime, it is baked into a custom image at build time. This means the container starts in seconds rather than downloading packages on every restart.

**Named volumes over bind mounts** — Ollama models (~4GB) and PostgreSQL data persist in named Docker volumes. This means `docker compose down` does not destroy data, only `docker compose down -v` does. Intentional tradeoff documented.

**Healthcheck on PostgreSQL** — MLflow will fail to start if PostgreSQL is not ready. A healthcheck on the postgres service combined with `depends_on: condition: service_healthy` on MLflow ensures correct startup order without arbitrary sleep timers.

**CPU-only inference** — The lab hardware (Intel i7-1260P, 16GB RAM) has no discrete GPU. Ollama is configured for CPU inference. llama3.2:3b produces responses in 15-30 seconds on this hardware, which is acceptable for agentic workflows where the bottleneck is usually I/O not generation speed.

## AWS Equivalent

| Local | AWS |
|---|---|
| Ollama + llama3.2:3b | Amazon Bedrock InvokeModel (Llama, Claude) |
| MLflow tracking | Amazon SageMaker Experiments |
| PostgreSQL backend | Amazon RDS PostgreSQL |
| Portainer | Amazon ECS console / AWS Systems Manager |

## Quick Start

```bash
docker compose up -d
docker compose ps
```

Pull models (first run only):
```bash
docker exec homelab-ollama ollama pull llama3.2:3b
docker exec homelab-ollama ollama pull phi3:mini
```

Verify inference:
```bash
curl http://localhost:11434/api/generate \
  -d '{"model":"llama3.2:3b","prompt":"Hello","stream":false}'
```
