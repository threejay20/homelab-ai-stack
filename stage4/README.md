# Stage 4 — Monitoring + Observability

Full observability stack for the AI system. Prometheus scrapes metrics, Grafana visualizes them, Node Exporter reports host health, and Evidently AI monitors RAG answer quality.

## What It Does

Collects metrics from the RAG pipeline and agent, stores them in Prometheus, displays them in a pre-built Grafana dashboard, and runs continuous quality monitoring on RAG outputs via Evidently AI.

## Services

| Service | Port | Purpose |
|---|---|---|
| Prometheus | 9090 | Metrics collection and storage |
| Grafana | 3000 | Visualization dashboard |
| Node Exporter | 9100 | Host CPU, memory, disk metrics |
| Evidently AI | 8050 | RAG quality monitoring |

## Prometheus Targets

| Target | What it scrapes |
|---|---|
| homelab-rag:8000/metrics | RAG request rates, latency, chunks ingested |
| homelab-agent:8001/metrics | Agent query rates and tool usage |
| node-exporter:9100 | Host CPU, memory, disk, network |
| prometheus:9090 | Prometheus self-metrics |

## Key Design Decisions

**Grafana dashboard auto-provisioned** — The dashboard JSON is mounted into the container at build time via a provisioning config. Grafana loads it automatically on startup. There is no manual import step. This means the dashboard is version-controlled and reproducible across environments.

**15-day Prometheus retention** — Default Prometheus retention is 15 days. For a homelab this is sufficient. The retention flag is set explicitly in the compose file rather than relying on defaults, making the behaviour predictable.

**Evidently AI for RAG quality** — Standard infrastructure metrics tell you if the system is up. They do not tell you if the answers are good. Evidently AI receives every query and answer pair, tracks semantic similarity scores over time, and flags when answer quality drifts. This is the AI-specific observability layer that infrastructure monitoring cannot provide.

**Non-blocking quality logging** — Evidently logging in the RAG pipeline is fire-and-forget. It never blocks the query response path.

## AWS Equivalent

| Local | AWS |
|---|---|
| Prometheus | Amazon Managed Service for Prometheus |
| Grafana | Amazon Managed Grafana |
| Node Exporter | Amazon CloudWatch agent |
| Evidently AI | Amazon SageMaker Model Monitor |

## Quick Start

```bash
docker compose up -d
```

Access Grafana at http://localhost:3000 with admin / homelab123.
The homelab dashboard loads automatically.
