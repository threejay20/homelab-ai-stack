import os
import re
import json
import asyncio
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from agents import run_multiagent, AgentEvent, AgentStatus
from briefing import create_scheduler, set_broadcast_callback

app = FastAPI(
    title="AI Command Center — Multi-Agent Orchestrator",
    description="Tribal Chief, Nezuko, Mikasa, Levi, Eren and Armin",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task: str

class SpeechRequest(BaseModel):
    text: str
    voice_id: str

# The ElevenLabs key lives only here, in the server's environment (stage5/.env).
# The browser never sees it: the UI calls /tts and this server calls ElevenLabs.
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")
ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
VOICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{10,40}$")
MAX_SPEECH_CHARS = 500

active_connections: list[WebSocket] = []

async def broadcast_to_all(message: dict):
    """Send a message to all connected WebSocket clients."""
    import json
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        active_connections.remove(ws)

@app.on_event("startup")
async def startup_event():
    set_broadcast_callback(broadcast_to_all)
    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()

@app.get("/")
def root():
    return {
        "service": "AI Command Center — Multi-Agent Orchestrator",
        "agents": ["Tribal Chief", "Nezuko", "Mikasa", "Levi", "Eren", "Armin"],
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "agents": {
            "tribal_chief": "ready",
            "nezuko": "ready",
            "mikasa": "ready",
            "levi": "ready",
            "eren": "ready",
            "armin": "ready"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await websocket.send_text(json.dumps({
            "agent": "system",
            "status": "connected",
            "message": "Connected to AI Command Center. Tribal Chief, Nezuko, Mikasa, Levi, Eren and Armin are standing by."
        }))
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                task = payload.get("task", "").strip()
                if not task:
                    await websocket.send_text(json.dumps({
                        "agent": "system",
                        "status": "error",
                        "message": "Please provide a task."
                    }))
                    continue
                await websocket.send_text(json.dumps({
                    "agent": "system",
                    "status": "started",
                    "message": f"Task received: {task}"
                }))
                async for event in run_multiagent(task):
                    await websocket.send_text(event.model_dump_json())
                    await asyncio.sleep(0.1)
                await websocket.send_text(json.dumps({
                    "agent": "system",
                    "status": "done",
                    "message": "Task complete."
                }))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "agent": "system",
                    "status": "error",
                    "message": "Invalid message format."
                }))
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.post("/tts")
async def text_to_speech(request: SpeechRequest):
    """Turn agent text into speech without exposing the ElevenLabs key to the browser."""
    if not ELEVEN_API_KEY:
        raise HTTPException(status_code=503, detail="Voice is not configured on the server.")
    if not VOICE_ID_PATTERN.match(request.voice_id):
        raise HTTPException(status_code=400, detail="Invalid voice ID.")
    text = request.text.strip()[:MAX_SPEECH_CHARS]
    if not text:
        raise HTTPException(status_code=400, detail="No text to speak.")

    async with httpx.AsyncClient(timeout=30) as client:
        upstream = await client.post(
            ELEVEN_TTS_URL.format(voice_id=request.voice_id),
            headers={"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )
    if upstream.status_code != 200:
        raise HTTPException(status_code=502, detail="The voice service did not return audio.")
    return Response(content=upstream.content, media_type="audio/mpeg")

@app.post("/task")
async def run_task_http(request: TaskRequest):
    events = []
    async for event in run_multiagent(request.task):
        events.append(event.model_dump())
    final = next(
        (e for e in reversed(events)
         if e["agent"] == "tribal_chief" and e["status"] == "complete"),
        None
    )
    return {
        "task": request.task,
        "events": events,
        "answer": final["data"]["final_answer"] if final and final.get("data") else "No answer generated"
    }
