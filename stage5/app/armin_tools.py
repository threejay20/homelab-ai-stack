import os
import json
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "/app/google-token.json")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "/app/google-credentials.json")

def get_google_creds():
    """Load and refresh Google credentials."""
    if not os.path.exists(TOKEN_PATH):
        return None
    try:
        with open(TOKEN_PATH) as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        return creds
    except Exception as e:
        print(f"Google auth error: {e}")
        return None

def get_calendar_events(days_ahead: int = 7) -> str:
    """Get upcoming calendar events."""
    creds = get_google_creds()
    if not creds:
        return "Google Calendar not configured."
    try:
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)
        events = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        items = events.get("items", [])
        if not items:
            return f"No events in the next {days_ahead} days."
        lines = [f"Upcoming events (next {days_ahead} days):"]
        for e in items:
            start = e["start"].get("dateTime", e["start"].get("date"))
            title = e.get("summary", "Untitled")
            location = e.get("location", "")
            loc_str = f" @ {location}" if location else ""
            lines.append(f"  {start}: {title}{loc_str}")
        return "\n".join(lines)
    except Exception as e:
        return f"Calendar error: {str(e)}"

def get_gmail_unread(max_results: int = 5) -> str:
    """Get unread Gmail messages."""
    creds = get_google_creds()
    if not creds:
        return "Gmail not configured."
    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            labelIds=["INBOX", "UNREAD"]
        ).execute()
        messages = results.get("messages", [])
        if not messages:
            return "No unread messages in inbox."
        lines = [f"Unread emails ({len(messages)} found):"]
        for m in messages:
            msg = service.users().messages().get(
                userId="me", id=m["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            sender = headers.get("From", "unknown")[:50]
            subject = headers.get("Subject", "no subject")[:70]
            lines.append(f"  From: {sender}")
            lines.append(f"  Subject: {subject}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Gmail error: {str(e)}"

def get_drive_recent(max_results: int = 5) -> str:
    """Get recently modified Drive files."""
    creds = get_google_creds()
    if not creds:
        return "Google Drive not configured."
    try:
        service = build("drive", "v3", credentials=creds)
        results = service.files().list(
            pageSize=max_results,
            orderBy="modifiedTime desc",
            fields="files(name,mimeType,modifiedTime,webViewLink)"
        ).execute()
        files = results.get("files", [])
        if not files:
            return "No recent Drive files found."
        lines = ["Recent Google Drive files:"]
        for f in files:
            name = f.get("name", "unknown")
            modified = f.get("modifiedTime", "")[:10]
            mime = f.get("mimeType", "").split(".")[-1]
            lines.append(f"  [{modified}] {name} ({mime})")
        return "\n".join(lines)
    except Exception as e:
        return f"Drive error: {str(e)}"

def get_notion_pages(token: str = None) -> str:
    """Get recent Notion pages."""
    notion_token = token or os.getenv("NOTION_TOKEN", "")
    if not notion_token:
        return "Notion not configured. Set NOTION_TOKEN in .env"
    try:
        from notion_client import Client
        notion = Client(auth=notion_token)
        results = notion.search(
            filter={"property": "object", "value": "page"},
            sort={"direction": "descending", "timestamp": "last_edited_time"},
            page_size=5
        ).get("results", [])
        if not results:
            return "No Notion pages found."
        lines = ["Recent Notion pages:"]
        for page in results:
            title = "Untitled"
            props = page.get("properties", {})
            for prop in props.values():
                if prop.get("type") == "title":
                    title_parts = prop.get("title", [])
                    if title_parts:
                        title = title_parts[0].get("plain_text", "Untitled")
                        break
            edited = page.get("last_edited_time", "")[:10]
            lines.append(f"  [{edited}] {title}")
        return "\n".join(lines)
    except Exception as e:
        return f"Notion error: {str(e)}"
