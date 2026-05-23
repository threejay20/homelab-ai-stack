# Multi-Agent Orchestration System

Three specialized AI agents working in coordination to answer
infrastructure questions. ChiChi plans and synthesizes, Nezuko
retrieves knowledge, Mikasa executes infrastructure tools.
Live WebSocket streaming for real-time UI updates.

## Agents

| Agent | Role | Personality |
|---|---|---|
| ChiChi | Planner + Synthesizer | Strategic, calm, delegates and assembles final answers |
| Nezuko | Retriever | Fast, precise, searches the RAG knowledge base |
| Mikasa | Executor | Reliable, direct, runs Docker and system tools |

## Architecture

User Task
│
▼
ChiChi (Planner)
Analyzes task, decides which agents are needed
│
├──► Nezuko (Retriever)
│    Searches RAG pipeline for relevant documents
│
└──► Mikasa (Executor)
Checks container status and system metrics
│
▼
ChiChi (Synthesizer)
Combines all findings into final answer
│
▼
WebSocket stream → Live UI

## WebSocket Protocol

Connect to `ws://localhost:8002/ws` and send:
```json
{"task": "your question here"}
```

Receive a stream of agent events:
```json
{"agent": "chichi", "status": "thinking", "message": "..."}
{"agent": "nezuko", "status": "active", "message": "...", "handoff_to": "mikasa"}
{"agent": "mikasa", "status": "complete", "message": "...", "data": {...}}
{"agent": "chichi", "status": "complete", "message": "...", "data": {"final_answer": "..."}}
{"agent": "system", "status": "done", "message": "Task complete."}
```

## Agent Status Values

| Status | Meaning |
|---|---|
| `idle` | Agent is dormant, waiting |
| `thinking` | Agent is reasoning about the task |
| `active` | Agent is executing its role |
| `complete` | Agent finished, handing off |
| `error` | Agent encountered an error |

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | All agent readiness check |
| POST | /task | Run pipeline via HTTP, returns all events |
| WS | /ws | WebSocket endpoint for live streaming |

## Quick Start

```bash
cd stage5
cp .env.example .env
docker compose build
docker compose up -d
```

Prerequisites: Stage 1, 2, and 2.5 must be running.

## Design Decisions

**Async generator pipeline** — `run_multiagent` is an async generator
that yields events as they happen. FastAPI streams these directly over
WebSocket without buffering the full response. This is what enables
real-time UI updates.

**ChiChi plans in JSON** — The planner returns structured JSON
deciding which agents to invoke. Python handles the routing logic,
not the LLM. Same pattern as Stage 2.5 — reliable routing without
strict format compliance issues.

**Non-blocking handoffs** — Each agent awaits its predecessor before
activating. The pipeline is sequential by design — infrastructure
questions need context from retrieval before execution makes sense.

## AWS Bedrock Equivalent

| Local Component | Bedrock Equivalent |
|---|---|
| ChiChi (Planner) | Bedrock Agents supervisor mode |
| Nezuko (Retriever) | Bedrock Knowledge Bases |
| Mikasa (Executor) | Bedrock Agents action groups |
| WebSocket stream | API Gateway WebSocket API |
