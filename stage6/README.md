# Stage 6 — Live Agent UI

Animated isometric office environment where AI agents visually collaborate. Tribal Chief walks to Nezuko and Mikasa's desks to hand off tasks. A Slack-style chat panel streams activity in real time. Speak via microphone, hear responses via ElevenLabs TTS.

## What It Does

Renders an isometric office scene with three character sprites positioned at their desks. When a task is submitted, Tribal Chief walks across the floor to delegate to the relevant agent, a glowing orb transfers at the handoff point, and the agent activates with a status indicator. All activity appears in the chat panel. Voice input auto-sends. Voice output speaks only when mic was used.

## Services

| Service | Port | Purpose |
|---|---|---|
| Nginx | 3001 | Static file serving + WebSocket proxy |

## Key Design Decisions

**Sprite images over canvas drawing** — Earlier versions used HTML Canvas to draw characters programmatically. The quality was poor regardless of effort because hand-coded shapes cannot match pre-rendered sprite art. The final implementation uses absolutely-positioned PNG sprites from the Claude-Office open source project over a pre-rendered room background image. This is the same approach used by Gather.town and similar virtual office tools to achieve game-quality visuals in a browser.

**useRoomScale hook** — The room background renders at a fixed 800x600 logical resolution. All furniture and character positions are stored as percentages of that resolution. The useRoomScale hook measures the actual rendered pixel width and computes a scale factor (actualWidth / 800). Every sprite size is multiplied by this factor, keeping furniture and characters correctly sized relative to the room regardless of screen width.

**Animation queue** — Character movement is broken into discrete walk steps. A queue processes one step at a time, waiting for the CSS transition to complete (1050ms) before starting the next. Without the queue, multiple position updates fire simultaneously and the character teleports rather than walks. The queue is a ref not state, so updating it never triggers a React re-render.

**objectFit fill with 75% padding-bottom** — The room container uses paddingBottom: 75% (600/800 = 0.75) to enforce the exact 4:3 aspect ratio. objectFit: fill stretches the background image to fill this container exactly. This ensures percentage-based positions always map correctly to the same floor tiles regardless of container width.

**Voice fires only on mic input** — A usedVoiceRef flag is set when the speech recognition API produces a final transcript and cleared when the task completes. The speak() function checks this flag before calling ElevenLabs. Typed input is always silent. Voice input always triggers voice response.

**Nginx WebSocket proxy** — The browser connects to a single host on port 3001. Nginx proxies /ws to the Stage 5 agent backend on the internal Docker network. The browser never needs to know the backend port, and CORS is handled transparently.

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
docker compose build
docker compose up -d
```

Open http://localhost:3001 in Chrome.

Click the microphone button to speak. Toggle voice on/off with the header button.

Prerequisites: Stage 5 must be running (homelab-chichi on port 8002).
