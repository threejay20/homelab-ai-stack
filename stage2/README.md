# Homelab AI Stack — Stage 2: RAG Pipeline

Production-grade Retrieval-Augmented Generation pipeline built on
LangChain, Qdrant, and Ollama. Answers questions grounded in ingested
documents with zero data leaving the local network.

## Architecture

Document (PDF/TXT)
│
▼
Text Splitter (RecursiveCharacterTextSplitter)
chunk_size=500, overlap=50
│
▼
Embedding Model (all-MiniLM-L6-v2, 384 dimensions)
│
▼
Qdrant Vector DB ──────────────────────┐
│
User Question                          │
│                                 │
▼                                 │
Embedding Model                        │
│                                 │
▼                                 ▼
Similarity Search (cosine, k=3) ───► Top 3 chunks
│
▼
Phi-3 Mini (Ollama)
│
▼
Grounded Answer

## Stack

| Service | Version | Purpose |
|---|---|---|
| Qdrant | 1.18.1 | Vector database — stores and searches embeddings |
| LangChain | 0.2.0 | RAG orchestration layer |
| sentence-transformers | 2.7.0 | Local embedding model (all-MiniLM-L6-v2) |
| FastAPI | 0.111.0 | REST API layer |
| Ollama | via Stage 1 | LLM inference (Phi-3 Mini) |

## Design Decisions

**Local embeddings** — `all-MiniLM-L6-v2` runs entirely on CPU with
no external API calls. 384-dimensional vectors, 80MB model size,
strong semantic search quality for a resource-constrained host.

**Cosine similarity** — chosen over dot product because it measures
angular distance between vectors, making it robust to document length
variation. A short chunk and a long chunk covering the same topic
score equally well.

**Chunk overlap** — 50-character overlap between chunks prevents
semantic context from being severed at chunk boundaries. A sentence
split across two chunks remains retrievable by either.

**Embedding model baked into image** — `all-MiniLM-L6-v2` downloads
at Docker build time rather than container startup. Eliminates
30-60 second cold-start delays in production environments.

**Cross-stack networking** — joins the same Docker bridge network as
the LLM stack, allowing direct container-to-container calls by name
without duplicating services or exposing unnecessary ports.

**Healthcheck via TCP probe** — Qdrant's minimal base image ships
without curl or wget. A bash TCP probe against port 6333 provides
reliable readiness detection without modifying the upstream image.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Connectivity check — Qdrant and Ollama |
| POST | /ingest | Upload PDF or TXT for chunking and indexing |
| POST | /query | Natural language query with grounded response |
| GET | /collections | List indexed collections and vector counts |

## Quick Start

```bash
git clone https://github.com/threejay20/homelab-ai-stack.git
cd homelab-ai-stack/stage2
cp .env.example .env
docker compose build
docker compose up -d
```

Ingest a document:
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@./docs/your-document.txt"
```

Query it:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "your question here"}'
```

## Prerequisites

The LLM stack (Stage 1) must be running. This pipeline reuses the
Ollama container for inference rather than running a second LLM
runtime.

## Performance Benchmarks

| Model | Hardware | Embedding Latency | Query Latency |
|---|---|---|---|
| all-MiniLM-L6-v2 | Intel i7-1260P (CPU) | <1s per chunk | — |
| Phi-3 Mini 3.8B | Intel i7-1260P (CPU) | — | ~35-40s |

## AWS Bedrock Equivalent

| Local Component | Bedrock Equivalent |
|---|---|
| Qdrant | Knowledge Bases (OpenSearch Serverless) |
| all-MiniLM-L6-v2 | Titan Embeddings V2 |
| LangChain RAG chain | RetrieveAndGenerate API |
| FastAPI endpoint | Lambda + API Gateway |

