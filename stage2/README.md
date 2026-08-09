# Stage 2 — RAG Pipeline

Production-grade Retrieval-Augmented Generation pipeline. Ask questions, get answers grounded in your actual documents.

## What It Does

Ingests documents into a vector database, embeds queries using the same model, retrieves semantically similar chunks, and passes them as context to the local LLM to generate grounded answers.

## Services

| Service | Port | Purpose |
|---|---|---|
| RAG API | 8000 | FastAPI ingestion and query endpoints |
| Qdrant | 6333 | Vector database |

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| /ingest | POST | Upload and chunk a document |
| /query | POST | Semantic search + LLM answer |
| /collections | GET | List vector collections |
| /health | GET | Health check |
| /metrics | GET | Prometheus metrics |

## Key Design Decisions

**Embeddings baked into Docker image** — sentence-transformers downloads the all-MiniLM-L6-v2 model (~90MB) on first use. In a container this happens at startup, adding 30-60 seconds to cold start and requiring internet access. The model is downloaded during `docker build` instead, so the container starts instantly and runs fully air-gapped.

**API key authentication** — Every endpoint except /health requires an `X-API-Key` header. Health is intentionally public so orchestration tools and load balancers can probe it without credentials. All other endpoints are protected.

**Prometheus metrics instrumented** — Three custom metrics: `rag_requests_total` (counter by endpoint and status), `rag_request_duration_seconds` (histogram with p50/p95 buckets), `rag_chunks_ingested_total` (counter). These feed directly into the Grafana dashboard in Stage 4.

**Non-blocking Evidently logging** — Every query result is logged to Evidently AI for quality monitoring. This is done as a fire-and-forget background task so it never adds latency to the query response.

**Chunk size 500, overlap 50** — Tuned for technical documentation. Larger chunks preserve more context per retrieval, overlap prevents answers from being split across chunk boundaries.

## AWS Equivalent

| Local | AWS |
|---|---|
| Qdrant | Amazon OpenSearch Serverless (vector engine) |
| LangChain RAG | Amazon Bedrock Knowledge Bases |
| all-MiniLM-L6-v2 | Amazon Titan Embeddings v2 |
| FastAPI | Amazon API Gateway + Lambda |
| Evidently AI | Amazon SageMaker Model Monitor |

## Quick Start

```bash
docker compose up -d

# Ingest a document
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: homelab-rag-key-2024" \
  -F "file=@your_document.txt;type=text/plain"

# Query the knowledge base
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: homelab-rag-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"question": "your question here"}'
```

## Authentication

All requests require the API key header:
