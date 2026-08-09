# Stage 5 — Multi-Agent Orchestration

Three specialized AI agents collaborate in real time to answer questions. Tribal Chief plans and synthesizes. Nezuko searches the knowledge base. Mikasa inspects infrastructure. All activity streams live to the UI via WebSocket.

## What It Does

Receives a task, uses Tribal Chief to create an execution plan, delegates to Nezuko and Mikasa in parallel or sequence based on the plan, and synthesizes a final answer from all results. Every step streams as a typed event to connected WebSocket clients.

## Services

| Service | Port | Purpose |
|---|---|---|
| Agent Orchestrator | 8002 | WebSocket + HTTP task endpoint |

## Agents

| Agent | Role | Tools |
|---|---|---|
| Tribal Chief | Planner + Synthesizer | Plans task, delegates, synthesizes final answer |
| Nezuko | Retriever | Queries RAG knowledge base |
| Mikasa | Executor | Docker status, system metrics |

## Endpoints

| Endpoint | Protocol | Purpose |
|---|---|---|
| /ws | WebSocket | Real-time agent event streaming |
| /task | POST HTTP | Submit task, receive all events |
| /health | GET HTTP | Agent readiness check |

## Key Design Decisions

**Async generator pipeline** — The orchestrator is an async generator function that yields AgentEvent objects. The WebSocket handler iterates over this generator and sends each event as it is produced. This means the UI receives updates in real time as each agent activates, rather than waiting for the full pipeline to complete.

**Typed AgentEvent model** — Every event has a defined schema: agent name, status (thinking/active/complete/error), message, optional data payload, and optional handoff_to field. The UI uses handoff_to to trigger character walking animations. Typed events make the contract between backend and frontend explicit and testable.

**Separate system prompts per agent** — Each agent has a distinct system prompt that defines its role, constraints, and output format. Tribal Chief is instructed to return structured JSON for the plan. Nezuko is instructed to summarize retrieved context concisely. Mikasa is instructed to report infrastructure facts without interpretation.

**Responsibility boundaries** — Tribal Chief never calls tools directly. Mikasa never synthesizes or interprets. Nezuko never executes. These boundaries are enforced by prompt design and make the system easier to debug — if retrieval is wrong, the problem is in Nezuko's prompt or the knowledge base, not elsewhere.

## AWS Equivalent

| Local | AWS |
|---|---|
| Tribal Chief | Bedrock Agent (orchestrator) |
| Nezuko | Bedrock Knowledge Base retrieval action |
| Mikasa | Bedrock Agent action group + Lambda |
| WebSocket streaming | API Gateway WebSocket API |
| AgentEvent schema | Bedrock agent trace events |

## Quick Start

```bash
docker compose up -d

# Test via HTTP
curl -X POST http://localhost:8002/task \
  -H "Content-Type: application/json" \
  -d '{"task": "How is my infrastructure doing?"}'

# Test via WebSocket (requires wscat)
wscat -c ws://localhost:8002/ws
```
