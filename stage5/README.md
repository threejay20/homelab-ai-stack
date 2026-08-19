# Stage 5 — Multi-Agent Orchestration

Six specialized AI agents collaborate in real time to answer questions, audit security, check infrastructure, manage personal productivity, and remember previous conversations. Every agent activation streams live to the UI via WebSocket.

## What It Does

Receives a task, uses Tribal Chief to create an execution plan with intelligent keyword routing, delegates to specialized agents, synthesizes a final answer from all results, and saves the conversation to PostgreSQL for future context. Every step streams as a typed event to connected WebSocket clients.

## Services

| Service | Port | Purpose |
|---|---|---|
| Agent Orchestrator | 8002 | WebSocket + HTTP task endpoint |

## Agents

| Agent | Role | Sprite | Tools | Voice |
|---|---|---|---|---|
| Tribal Chief | Planner + Synthesizer | Claude-1 | Plans, delegates, synthesizes, remembers | Brian (deep) |
| Nezuko | Researcher | employee-2 | RAG knowledge base search | Sarah (warm) |
| Mikasa | Executor | security-audit-1 | Docker status, system metrics | Alice (clear) |
| Levi | Security Auditor | dev-1 | Port exposure, API key health, auth checks | George (captivating) |
| Eren | DevOps Engineer | explore-1 | Service health endpoints, Prometheus targets | Charlie (energetic) |
| Armin | Personal Assistant | dev-2 | Google Calendar, Gmail, Google Drive, Notion | Jessica (warm) |

## Endpoints

| Endpoint | Protocol | Purpose |
|---|---|---|
| /ws | WebSocket | Real-time agent event streaming |
| /task | POST HTTP | Submit task, receive all events |
| /health | GET HTTP | Agent readiness check |

## Intelligent Routing

Tribal Chief uses keyword-based routing to decide which agents to activate:

| Keywords in task | Agents activated |
|---|---|
| health check, service health, pipeline, deploy | Eren |
| security, audit, port, vulnerability | Levi |
| container, docker, memory, cpu | Mikasa |
| documents, runbooks, procedures | Nezuko |
| calendar, schedule, meeting, email, gmail, notion | Armin |

The local LLM handles general routing. Python keyword overrides ensure reliability for infrastructure, security, and personal queries.

## Conversation Memory

Every completed conversation is saved to PostgreSQL (`homelab` database, `conversations` table). Tribal Chief loads the last 5 conversations before planning each new task, enabling responses like "Last time you asked about X, here's what changed."

Memory schema:
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    task TEXT NOT NULL,
    plan JSONB,
    final_answer TEXT,
    agents_used TEXT[],
    mode VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Bedrock Guardrails

All LLM calls are protected by AWS Bedrock Guardrails when `USE_BEDROCK=true`:

| Filter | Strength | Coverage |
|---|---|---|
| Harmful content | HIGH | Violence, hate speech, illegal activities |
| Sexual content | HIGH | Input and output |
| Prompt attacks | HIGH | Input only |
| Insults/Misconduct | MEDIUM | Input and output |
| PII detection | ANONYMIZE | Email, phone, name |

Harmful queries are blocked before any agents activate. The guardrail response replaces the normal pipeline output.

## AWS Bedrock Integration

Set `USE_BEDROCK=true` in `.env` to route LLM calls to AWS instead of local Ollama:

| Step | Local (free) | Bedrock (~$0.002/query) |
|---|---|---|
| Planning | llama3.2:3b via Ollama | Nova Micro (us.amazon.nova-micro-v1:0) |
| Synthesis | llama3.2:3b via Ollama | Claude Haiku 4.5 (us.anthropic.claude-haiku-4-5-20251001-v1:0) |

```bash
# Enable Bedrock
sed -i 's/USE_BEDROCK=false/USE_BEDROCK=true/' .env
docker compose up -d

# Disable Bedrock (back to local)
sed -i 's/USE_BEDROCK=true/USE_BEDROCK=false/' .env
docker compose up -d
```

Note: Bedrock requires inference profile IDs (prefixed with `us.`) not direct model IDs.

## Google Workspace Integration

Armin connects to Google Calendar, Gmail, and Drive via OAuth2. Setup:

1. Create Google Cloud project and enable Calendar, Gmail, Drive APIs
2. Create OAuth2 Desktop credentials and download `credentials.json`
3. Run auth flow: `python3 scripts/auth_google.py`
4. Copy token to app directory: `cp scripts/google-token.json stage5/app/`

Token auto-refreshes using the stored refresh token. Credentials and tokens are gitignored.

## Notion Integration

Armin connects to Notion via an Internal Integration Token:

1. Go to https://www.notion.so/my-integrations
2. Create new integration with Access Token auth
3. Add token to `.env`: `NOTION_TOKEN=ntn_...`

## Agent Status Flow

```
Tribal Chief: THINKING → ACTIVE → WAITING → PROCESSING → COMPLETE
Agents:       THINKING → ACTIVE → COMPLETE
```

## Key Design Decisions

**Async generator pipeline** — The orchestrator yields AgentEvent objects. The WebSocket handler streams each event as it is produced. The UI receives updates in real time as each agent activates.

**Typed AgentEvent model** — Every event has a defined schema: agent name, status, message, optional data payload, and optional handoff_to field. The UI uses handoff_to to trigger character walking animations.

**Keyword routing override** — The local llama3.2:3b model is unreliable at routing complex multi-agent queries. Python keyword matching runs after the LLM plan and corrects missed agent activations.

**Responsibility boundaries** — Tribal Chief never calls tools directly. Each agent has a single domain of responsibility enforced by prompt design.

**PostgreSQL for memory** — Uses the existing homelab-postgres container with a separate `homelab` database. Memory is non-blocking — a save failure never interrupts the agent pipeline.

**Bedrock as optional premium tier** — `USE_BEDROCK` flag toggles between local free inference and AWS managed models. The code path is identical — only the LLM client changes.

**Guardrails on input and output** — Input is checked before any agents activate. Output is checked before returning to the user. Failures fall open (return original text) so a guardrail error never breaks the pipeline.

## AWS Equivalent

| Local | AWS |
|---|---|
| Tribal Chief | Bedrock Agent (orchestrator) |
| Nezuko | Bedrock Knowledge Base retrieval action |
| Mikasa | Bedrock Agent action group + Lambda |
| Levi | Bedrock Agent + AWS Security Hub integration |
| Eren | Bedrock Agent + CloudWatch health checks |
| Armin | Bedrock Agent + Google Workspace connector |
| WebSocket streaming | API Gateway WebSocket API |
| PostgreSQL memory | Amazon DynamoDB conversation history |
| Bedrock Guardrails | Amazon Bedrock Guardrails (same service) |
| Nova Micro | us.amazon.nova-micro-v1:0 (same model) |
| Claude Haiku | us.anthropic.claude-haiku-4-5-20251001-v1:0 (same model) |

## Quick Start

```bash
docker compose up -d

# Test via HTTP
curl -X POST http://localhost:8002/task \
  -H "Content-Type: application/json" \
  -d '{"task": "How is my infrastructure doing?"}'

# Check conversation memory
docker exec homelab-postgres psql -U mlflow -d homelab \
  -c "SELECT task, agents_used, created_at FROM conversations ORDER BY created_at DESC LIMIT 5;"
```

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| USE_BEDROCK | false | Route LLM calls to AWS Bedrock |
| AWS_REGION | us-east-1 | Bedrock region |
| BEDROCK_PLAN_MODEL | us.amazon.nova-micro-v1:0 | Model for planning |
| BEDROCK_SYNTH_MODEL | us.anthropic.claude-haiku-4-5-20251001-v1:0 | Model for synthesis |
| MEMORY_ENABLED | true | Enable PostgreSQL conversation memory |
| MEMORY_MAX_HISTORY | 5 | Number of past conversations to load |
| MEMORY_DB_URL | postgresql://... | PostgreSQL connection string |
| GUARDRAIL_ID | bonfxsfr5yq3 | Bedrock Guardrail ID |
| GUARDRAIL_VERSION | 1 | Guardrail version |
| GUARDRAILS_ENABLED | true | Enable content filtering |
| GOOGLE_TOKEN_PATH | /app/google-token.json | OAuth token for Google APIs |
| NOTION_TOKEN | | Notion integration token |
