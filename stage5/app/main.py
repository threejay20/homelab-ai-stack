import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import run_multiagent, AgentEvent, AgentStatus

app = FastAPI(
    title="Homelab Multi-Agent Orchestrator",
    description="Tribal Chief, Nezuko, and Mikasa",
    version="1.0.0"
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

active_connections: list[WebSocket] = []

@app.get("/")
def root():
    return {
        "service": "Homelab Multi-Agent Orchestrator",
        "agents": ["Tribal Chief", "Nezuko", "Mikasa"],
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "agents": {
            "tribal_chief": "ready",
            "nezuko": "ready",
            "mikasa": "ready"
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
            "message": "Connected to Homelab AI Command Center. Tribal Chief, Nezuko, and Mikasa are standing by."
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
