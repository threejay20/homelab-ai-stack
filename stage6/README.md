# AI Command Center — Live Agent UI

Real-time web interface for the multi-agent orchestration system.
Visualizes ChiChi, Nezuko, and Mikasa working in an isometric office
environment with live WebSocket streaming of agent activity.

## Architecture

Browser (React + Canvas)
│
│ WebSocket ws://localhost:3001/ws
│
Nginx (port 3001)
│
├── /ws  → proxy → Stage 5 (homelab-chichi:8002)
└── /*   → React app (static build)

## Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend | React 18 + HTML Canvas | Isometric office scene + agent UI |
| Server | Nginx Alpine | Static file serving + WebSocket proxy |
| Build | Vite 5 + Node 20 | Production bundle |
| Container | Docker multi-stage build | Node builder → Nginx runtime |

## Design Decisions

**HTML Canvas over DOM** — the isometric office scene requires
per-frame depth sorting of furniture and characters. Canvas gives
direct control over draw order and smooth 60fps animation without
DOM reflow overhead.

**Nginx WebSocket proxy** — the UI connects to a single host on
port 3001. Nginx proxies `/ws` to the Stage 5 agent backend on the
internal Docker network. The browser never needs to know the backend
port, and CORS is handled transparently.

**Multi-stage Docker build** — Node 20 Alpine builds the React app,
Nginx Alpine serves the static output. Final image is ~25MB with no
Node runtime in production.

**requestAnimationFrame game loop** — agent state is stored in a
ref (not React state) so canvas redraws don't trigger React
re-renders. Only the activity feed and final answer panel use React
state since those are DOM elements.

## Live Features

- Isometric office with ChiChi's glass-walled director office
- Nezuko and Mikasa at their desks on the operations floor
- ChiChi walks to agent desks to hand off tasks
- Data orb animation on handoff
- Real-time activity feed via WebSocket
- Final answer panel with ChiChi's synthesized report

## Quick Start

```bash
cd stage6
docker compose build
docker compose up -d
```

Open: http://localhost:3001

Prerequisites: Stage 5 must be running (homelab-chichi on port 8002).

## AWS Equivalent

| Local Component | AWS Equivalent |
|---|---|
| React + Canvas UI | CloudFront + S3 static hosting |
| Nginx WebSocket proxy | API Gateway WebSocket API |
| Docker container | ECS Fargate task |
