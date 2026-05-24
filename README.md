# Homelab AI Stack

Local AI infrastructure built on Docker and WSL2, designed to mirror
enterprise MLOps and LLMOps deployment patterns. Each stage is
independently deployable and builds on the previous.

## Stages

| Stage | Description | Stack |
|---|---|---|
| [stage1](./stage1) | Local AI serving stack | Ollama · MLflow · PostgreSQL · Portainer |
| [stage2](./stage2) | RAG pipeline | Qdrant · LangChain · FastAPI |
| [stage2.5](./stage2.5) | DevOps AI agent | LangChain · llama3.2:3b · Docker socket |
| [stage3](./stage3) | CI/CD for AI | GitHub Actions · pytest · eval pipeline |
| [stage4](./stage4) | Monitoring + observability | Prometheus · Grafana · Evidently AI |
| [stage5](./stage5) | Multi-agent orchestration | ChiChi · Nezuko · Mikasa · WebSocket |
| [stage6](./stage6) | Live agent UI | React · Canvas · Nginx · WebSocket proxy |
| [security](./security) | Security hardening | API key auth · Docker socket proxy |

## Prerequisites

- Windows 11 with WSL2 (Ubuntu 22.04)
- Docker Desktop 27+
- 16GB RAM minimum

## Quick Start

```bash
docker network create homelab-network
cd stage1 && docker compose up -d
cd ../stage2 && docker compose build && docker compose up -d
```
