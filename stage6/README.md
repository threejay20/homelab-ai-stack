# Stage 6 — Live Agent UI

Animated isometric office environment where six AI agents visually collaborate. Tribal Chief walks to agent desks to hand off tasks. A Slack-style chat panel streams activity in real time. Speak via microphone, hear responses via ElevenLabs TTS.

## What It Does

Renders an isometric office scene with six character sprites at their desks. When a task is submitted, Tribal Chief walks across the floor to delegate to the relevant agent, a glowing orb transfers at the handoff point, and the agent activates with a status indicator. All activity appears in the chat panel. Voice input auto-sends. Voice output speaks only when mic was used.

## Services

| Service | Port | Purpose |
|---|---|---|
| Nginx | 3001 | Static file serving + WebSocket proxy |

## Characters

| Agent | Sprite | Color | Voice (ElevenLabs) | Position |
|---|---|---|---|---|
| Tribal Chief | Claude-1 | Blue | Brian — Deep, Resonant | Center desk |
| Nezuko | employee-2 | Pink | Sarah — Mature, Reassuring | Left cluster |
| Mikasa | security-audit-1 | Red | Alice — Clear, Engaging | Right cluster |
| Levi | dev-1 | Green | George — Warm, Captivating | Left cluster rear |
| Eren | explore-1 | Amber | Charlie — Deep, Confident | Right cluster rear |
| Armin | dev-2 | Purple | Jessica — Playful, Warm | Right side desk |

## Agent Status Flow

| Status | Badge | Meaning |
|---|---|---|
| idle | none | Standing by at desk |
| thinking | THINKING... | Processing the task |
| active/working | WORKING | Executing tools or searching |
| waiting | WAITING... | Tribal Chief waiting for agents |
| processing | PROCESSING... | Tribal Chief synthesizing final answer |
| complete | green glow | Task finished |

## Voice System

- **Mic button** — click to speak, populates input box (no auto-send)
- **Enter or Send button** — confirms and sends the task
- **Voice output** — ElevenLabs TTS fires only when mic was used to send
- **Silent on typed input** — typing never triggers voice response
- **Voice ON/OFF toggle** — header button mutes all speech synthesis
- **Per-agent voices** — each agent speaks in a distinct voice

Voice key stored in `VITE_ELEVEN_API_KEY` environment variable. Never committed to git.

## Stop Button

A red STOP button appears while a task is running. Clicking it:
- Clears the animation queue immediately
- Resets all agent statuses to idle
- Returns all characters to their desks
- Logs "Task stopped by user" in the chat panel

## Key Design Decisions

**Sprite images over canvas drawing** — Pre-rendered PNG sprites from the Claude-Office open source project over a rendered room background. Same approach used by Gather.town.

**useRoomScale hook** — Room renders at 800x600 logical resolution. All positions are percentages of that resolution. The hook measures actual rendered width and computes a scale factor (actualWidth / 800). Every sprite size multiplies by this factor.

**Animation queue** — Character movement is broken into discrete walk steps. A queue processes one step at a time, waiting for the CSS transition (1050ms) before starting the next. Without the queue, multiple position updates fire simultaneously and the character teleports.

**tribalChiefWaitingRef** — Protects Tribal Chief's WAITING status while agents are working. React state batching can cause the WAITING status to be overwritten before re-rendering.

**Voice fires only on mic input** — usedVoiceRef flag is set when speech recognition produces a final transcript and cleared when the task completes. Typed input is always silent.

**No auto-send on voice** — Speech recognition populates the input box. The user must press Enter or the Send button to confirm. This prevents accidental sends from background noise or incomplete sentences.

**Nginx WebSocket proxy** — Browser connects to a single host on port 3001. Nginx proxies /ws to the Stage 5 agent backend on the internal Docker network.

## AWS Equivalent

| Local | AWS |
|---|---|
| React + Nginx static | CloudFront + S3 static hosting |
| Nginx WebSocket proxy | API Gateway WebSocket API |
| ElevenLabs TTS | Amazon Polly |
| Web Speech API | Amazon Transcribe Streaming |
| Docker multi-stage build | ECS Fargate task |

## Quick Start

```bash
# Create env file with ElevenLabs key
echo "VITE_ELEVEN_API_KEY=your_key_here" > ui/.env.local

docker compose build
docker compose up -d
```

Open http://localhost:3001 in Chrome.

Prerequisites: Stage 5 must be running (homelab-chichi on port 8002).

## Re-ingest Knowledge Base

After a fresh start, re-ingest documents so Nezuko has current knowledge:

```bash
bash ../scripts/ingest_knowledge.sh
```
