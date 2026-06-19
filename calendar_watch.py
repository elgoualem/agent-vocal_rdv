import uuid
import os
from datetime import datetime, timedelta
from calendar_service import get_service
from airtable_service import update_status_by_event_id
import pytz

TIMEZONE = "Europe/Paris"
WATCH_TTL_DAYS = 29


def register_watch(webhook_url: str) -> dict:
    """Enregistre un push notification watch sur Google Calendar."""
    service = get_service()
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    expiration_ms = int(
        (datetime.now(pytz.UTC) + timedelta(days=WATCH_TTL_DAYS)).timestamp() * 1000
    )

    body = {
        "id": str(uuid.uuid4()),
        "type": "web_hook",
        "address": webhook_url,
        "expiration": expiration_ms,
    }

    result = service.events().watch(calendarId=calendar_id, body=body).execute()
    print(f"[Calendar Watch] Enregistre jusqu'au {datetime.fromtimestamp(expiration_ms / 1000)}")
    return result


def handle_calendar_change() -> int:
    """
    Appelee quand Google notifie un changement.
    Recupere les events modifies dans les 10 dernières minutes
    et met a jour Airtable si un event est annule.
    """
    service = get_service()
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    tz = pytz.timezone(TIMEZONE)

    updated_min = (datetime.now(pytz.UTC) - timedelta(minutes=10)).isoformat()

    events_result = service.events().list(
        calendarId=calendar_id,
        updatedMin=updated_min,
        showDeleted=True,
        singleEvents=True,
        maxResults=50,
    ).execute()

    cancelled = 0
    for event in events_result.get("items", []):
        if event.get("status") == "cancelled":
            event_id = event.get("id", "")
            if event_id:
                updated = update_status_by_event_id(event_id, "Annule")
                if updated:
                    print(f"[Calendar Watch] RDV annule dans Airtable : {event_id}")
                    cancelled += 1

    return cancelled
