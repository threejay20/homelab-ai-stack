# Security Model

Documentation of security controls, threat model, and intentional
tradeoffs for this local AI infrastructure stack.

## Controls in Place

### API Authentication
All functional endpoints on the RAG pipeline (port 8000) and Agent
API (port 8001) require a valid `X-API-Key` header. Requests without
a valid key return 403. Health endpoints are intentionally public to
support monitoring systems that check service availability without
credentials.

### Docker Socket Proxy
The agent container accesses host container state via a restricted
socket proxy (tecnativa/docker-socket-proxy) rather than a raw socket
mount. The proxy permits only read-only Docker API endpoints:
`CONTAINERS`, `INFO`, `PING`, `VERSION`. All write operations —
create, stop, delete, exec, build — are denied at the proxy level
regardless of what the agent attempts.

Raw socket mount (`/var/run/docker.sock`) would grant full root-level
access to the host. The proxy reduces this to read-only container
inspection.

### Network Isolation
All services communicate over a dedicated Docker bridge network
(`homelab-network`). No service is exposed to external interfaces
beyond explicitly mapped localhost ports. PostgreSQL (5432) and
Qdrant internal gRPC (6334) are not mapped to the host.

### Secret Management
Credentials are stored in `.env` files excluded from version control
via `.gitignore`. A `.env.example` template documents required
variables without exposing values. No secrets appear in committed
code, Dockerfiles, or compose files.

## Threat Model

| Threat | Likelihood | Mitigation |
|---|---|---|
| Unauthorized API access from local network | Low | API key authentication on all endpoints |
| Container escape via Docker socket | Low | Socket proxy — read-only access only |
| Secret exposure via git | Low | .gitignore on all .env files |
| LLM prompt injection via documents | Medium | Mitigated in Stage 5 via guardrails |
| Lateral movement between containers | Low | Isolated bridge network |

## Intentional Tradeoffs

**No TLS on localhost** —
