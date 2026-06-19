from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "Europe/Paris"
SLOT_DURATION_H = 1

DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS_FR = [
    "", "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre"
]


def _restore_token_from_env():
    """En production (Railway), restaure token.json et credentials.json depuis les variables d'env."""
    import base64

    if not os.path.exists("token.json"):
        encoded = os.getenv("GOOGLE_TOKEN_JSON", "")
        if encoded:
            with open("token.json", "w") as f:
                f.write(base64.b64decode(encoded).decode())

    if not os.path.exists("credentials.json"):
        encoded = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
        if encoded:
            with open("credentials.json", "w") as f:
                f.write(base64.b64decode(encoded).decode())


def get_service():
    _restore_token_from_env()

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER"):
            raise RuntimeError(
                "Pas de token Google valide sur le serveur. "
                "Verifiez que GOOGLE_TOKEN_JSON est bien defini dans les variables Railway."
            )
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def _in_availability(cursor, availability_slots: list) -> bool:
    """Retourne True si le curseur tombe dans une des plages de dispo."""
    day = cursor.weekday()
    hour = cursor.hour
    return any(
        day in s.get("jours", []) and s.get("debut", 9) <= hour < s.get("fin", 17)
        for s in availability_slots
    )


def get_available_slots(days_ahead: int = 7) -> list:
    from airtable_service import get_availability_config
    availability = get_availability_config()  # liste de plages

    service = get_service()
    tz = pytz.timezone(TIMEZONE)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    now = datetime.now(tz)
    end_window = now + timedelta(days=days_ahead)

    freebusy = service.freebusy().query(body={
        "timeMin": now.isoformat(),
        "timeMax": end_window.isoformat(),
        "items": [{"id": calendar_id}]
    }).execute()

    busy_raw = freebusy["calendars"][calendar_id]["busy"]
    busy_intervals = [
        (
            datetime.fromisoformat(b["start"].replace("Z", "+00:00")).astimezone(tz),
            datetime.fromisoformat(b["end"].replace("Z", "+00:00")).astimezone(tz),
        )
        for b in busy_raw
    ]

    slots = []
    cursor = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    while cursor < end_window and len(slots) < 8:
        if not _in_availability(cursor, availability):
            cursor += timedelta(hours=1)
            continue

        slot_end = cursor + timedelta(hours=SLOT_DURATION_H)
        is_free = all(cursor >= b_end or slot_end <= b_start for b_start, b_end in busy_intervals)

        if is_free:
            slots.append(cursor)

        cursor += timedelta(hours=1)

    return slots


def format_slots_for_agent(slots: list) -> str:
    """Retourne les créneaux lisibles à voix haute + format machine pour la réservation."""
    lines = [
        "Créneaux disponibles (annoncez-les au client, "
        "utilisez le format entre parenthèses pour reserver_creneau) :"
    ]
    for i, slot in enumerate(slots[:3], 1):
        human = f"{DAYS_FR[slot.weekday()]} {slot.day} {MONTHS_FR[slot.month]} à {slot.hour}h"
        machine = slot.strftime("%Y-%m-%d %H:%M")
        lines.append(f"{i}. {human.capitalize()} ({machine})")
    return "\n".join(lines)


def cancel_event(calendar_event_id: str) -> bool:
    """Annule un evenement Google Calendar."""
    try:
        service = get_service()
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        service.events().delete(calendarId=calendar_id, eventId=calendar_event_id).execute()
        return True
    except Exception as e:
        print(f"[Calendar] Erreur annulation event {calendar_event_id}: {e}")
        return False


def book_appointment(prenom: str, nom: str, email: str, date_heure: str, besoin: str) -> dict:
    service = get_service()
    tz = pytz.timezone(TIMEZONE)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    start_dt = None
    for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M"]:
        try:
            start_dt = tz.localize(datetime.strptime(date_heure, fmt))
            break
        except ValueError:
            continue

    if start_dt is None:
        raise ValueError(f"Format de date non reconnu : {date_heure}")

    end_dt = start_dt + timedelta(hours=SLOT_DURATION_H)

    event = {
        "summary": f"Consultation découverte – {prenom} {nom}",
        "description": f"Besoin : {besoin}\nContact : {email}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
        "attendees": [{"email": email}],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 30},
            ],
        },
    }

    return service.events().insert(
        calendarId=calendar_id,
        body=event,
        sendUpdates="all"
    ).execute()
