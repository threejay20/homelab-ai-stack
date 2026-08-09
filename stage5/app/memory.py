import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Optional

MEMORY_DB_URL = os.getenv("MEMORY_DB_URL", "")
MEMORY_ENABLED = os.getenv("MEMORY_ENABLED", "false").lower() == "true"
MEMORY_MAX_HISTORY = int(os.getenv("MEMORY_MAX_HISTORY", "5"))

def get_conn():
    return psycopg2.connect(MEMORY_DB_URL)

def save_conversation(task: str, plan: dict, final_answer: str, agents_used: list, mode: str):
    if not MEMORY_ENABLED or not MEMORY_DB_URL:
        return
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO conversations (task, plan, final_answer, agents_used, mode)
            VALUES (%s, %s, %s, %s, %s)
        """, (task, json.dumps(plan), final_answer, agents_used, mode))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Memory save error: {e}")

def load_recent_conversations(limit: int = None) -> list:
    if not MEMORY_ENABLED or not MEMORY_DB_URL:
        return []
    try:
        limit = limit or MEMORY_MAX_HISTORY
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT task, final_answer, agents_used, mode, created_at
            FROM conversations
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Memory load error: {e}")
        return []

def format_memory_context(conversations: list) -> str:
    if not conversations:
        return ""
    lines = ["Recent conversation history (most recent first):"]
    for i, c in enumerate(conversations, 1):
        ts = c["created_at"].strftime("%Y-%m-%d %H:%M") if c.get("created_at") else "unknown"
        agents = ", ".join(c.get("agents_used") or [])
        lines.append(f"{i}. [{ts}] Task: {c['task']}")
        if c.get("final_answer"):
            summary = c["final_answer"][:150] + "..." if len(c["final_answer"]) > 150 else c["final_answer"]
            lines.append(f"   Answer summary: {summary}")
        if agents:
            lines.append(f"   Agents used: {agents}")
    return "\n".join(lines)
