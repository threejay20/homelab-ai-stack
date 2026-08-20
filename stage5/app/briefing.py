import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from armin_tools import get_calendar_events, get_gmail_unread
from memory import save_conversation

logger = logging.getLogger(__name__)

BRIEFING_ENABLED = os.getenv("BRIEFING_ENABLED", "true").lower() == "true"
BRIEFING_HOUR = int(os.getenv("BRIEFING_HOUR_UTC", "20"))
BRIEFING_MINUTE = int(os.getenv("BRIEFING_MINUTE_UTC", "0"))

# Will be set by main.py to broadcast to all WebSocket clients
broadcast_callback = None

def set_broadcast_callback(callback):
    global broadcast_callback
    broadcast_callback = callback

async def generate_morning_briefing() -> str:
    """Generate the daily morning briefing report."""
    now = datetime.now(timezone.utc)
    est_hour = (now.hour - 5) % 24
    date_str = now.strftime("%A, %B %d, %Y")

    sections = []
    sections.append(f"GOOD MORNING — {date_str}")
    sections.append("=" * 40)

    # Calendar
    try:
        calendar = get_calendar_events(days_ahead=1)
        sections.append("TODAY\'S CALENDAR:")
        sections.append(calendar)
    except Exception as e:
        sections.append(f"Calendar unavailable: {e}")

    # Email
    try:
        emails = get_gmail_unread(max_results=3)
        sections.append("\nUNREAD EMAILS:")
        sections.append(emails)
    except Exception as e:
        sections.append(f"Email unavailable: {e}")

    # Infrastructure hint
    sections.append("\nINFRASTRUCTURE:")
    sections.append("Ask Mikasa or Eren for a full health check.")

    sections.append("\nHave a productive day.")
    return "\n".join(sections)

async def run_morning_briefing():
    """Run the morning briefing and broadcast to connected clients."""
    logger.info("Running morning briefing...")
    try:
        briefing = await generate_morning_briefing()

        # Save to memory
        save_conversation(
            task="Morning briefing",
            plan={"scheduled": True},
            final_answer=briefing,
            agents_used=["tribal_chief", "armin"],
            mode="SCHEDULED"
        )

        # Broadcast to all connected WebSocket clients
        if broadcast_callback:
            await broadcast_callback({
                "agent": "tribal_chief",
                "status": "complete",
                "message": "Morning briefing ready.",
                "data": {"final_answer": briefing, "is_briefing": True}
            })
            logger.info("Morning briefing broadcast complete")
        else:
            logger.info("No clients connected for morning briefing")
    except Exception as e:
        logger.error(f"Morning briefing error: {e}")

def create_scheduler():
    """Create and configure the APScheduler instance."""
    scheduler = AsyncIOScheduler(timezone="UTC")
    if BRIEFING_ENABLED:
        scheduler.add_job(
            run_morning_briefing,
            CronTrigger(hour=BRIEFING_HOUR, minute=BRIEFING_MINUTE),
            id="morning_briefing",
            name="Daily Morning Briefing",
            replace_existing=True
        )
        logger.info(f"Morning briefing scheduled at {BRIEFING_HOUR:02d}:{BRIEFING_MINUTE:02d} UTC (8:00 AM EST)")
    return scheduler
