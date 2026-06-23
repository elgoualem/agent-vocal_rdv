from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import json
import os
import re
import pytz
from dotenv import load_dotenv

from calendar_service import get_available_slots, format_slots_for_agent, book_appointment
from airtable_service import save_appointment
from dashboard import router as dashboard_router
from calendar_watch import register_watch, handle_calendar_change

load_dotenv()

DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS_FR = [
    "", "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre"
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Enregistre le watch Google Calendar au demarrage
    webhook_url = os.getenv("WEBHOOK_URL", "").replace("/webhook", "/google-calendar-webhook")
    if webhook_url:
        try:
            register_watch(webhook_url)
        except Exception as e:
            print(f"[Calendar Watch] Erreur enregistrement : {e}")
    yield


app = FastAPI(title="Agent Vocal RDV", lifespan=lifespan)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    return {"status": "Agent Vocal RDV actif"}


@app.get("/debug/calendar")
async def debug_calendar():
    env_status = {
        "GOOGLE_TOKEN_JSON": "OK" if os.getenv("GOOGLE_TOKEN_JSON") else "MANQUANT",
        "GOOGLE_CREDENTIALS_JSON": "OK" if os.getenv("GOOGLE_CREDENTIALS_JSON") else "MANQUANT",
        "GOOGLE_CALENDAR_ID": os.getenv("GOOGLE_CALENDAR_ID", "non defini"),
        "token_json_exists": os.path.exists("token.json"),
        "credentials_json_exists": os.path.exists("credentials.json"),
    }
    try:
        slots = get_available_slots(days_ahead=7)
        return {"ok": True, "slots": len(slots), "env": env_status}
    except Exception as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__, "env": env_status}


@app.get("/debug/airtable")
async def debug_airtable():
    env_status = {
        "AIRTABLE_API_KEY": "OK" if os.getenv("AIRTABLE_API_KEY") else "MANQUANT",
        "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID", "non defini"),
        "AIRTABLE_TABLE_NAME": os.getenv("AIRTABLE_TABLE_NAME", "non defini"),
    }
    try:
        from pyairtable import Api
        api = Api(os.getenv("AIRTABLE_API_KEY"))
        table = api.table(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_TABLE_NAME", "Rendez-vous"))
        records = table.all(max_records=1)
        return {"ok": True, "records_count": len(records), "env": env_status}
    except Exception as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__, "env": env_status}


# ── Webhook VAPI ─────────────────────────────────────────────────

@app.post("/webhook")
async def vapi_webhook(request: Request):
    body = await request.json()
    message = body.get("message", {})
    msg_type = message.get("type")

    if msg_type == "tool-calls":
        tool_calls = message.get("toolCallList", [])
        results = []
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            args_raw = func.get("arguments", "{}")
            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except json.JSONDecodeError:
                args = {}
            result = await dispatch_tool(name, args, message)
            results.append({"toolCallId": tc["id"], "result": result})
        return JSONResponse({"results": results})

    elif msg_type == "end-of-call-report":
        call = message.get("call", {})
        print(f"\n[FIN APPEL] ID: {call.get('id')} | Duree: {call.get('duration')}s")
        print(f"Transcript:\n{message.get('transcript', '')[:800]}\n{'-'*40}")

    return JSONResponse({"ok": True})


async def dispatch_tool(name: str, args: dict, message: dict) -> str:
    call_id = message.get("call", {}).get("id", "")

    if name == "verifier_disponibilites":
        try:
            slots = get_available_slots(days_ahead=int(args.get("jours", 7)))
            if not slots:
                return "Aucun creneau disponible dans les prochains jours. Proposez au client de rappeler sous 24h."
            return format_slots_for_agent(slots)
        except Exception as e:
            print(f"[ERREUR calendar] {e}")
            return "Impossible de consulter le calendrier. Proposez au client de rappeler sous quelques minutes."

    elif name == "reserver_creneau":
        prenom    = args.get("prenom", "")
        nom       = args.get("nom", "")
        email     = args.get("email", "")
        date_heure = args.get("date_heure", "")
        besoin    = args.get("besoin", "")

        if not all([prenom, nom, email, date_heure]):
            return "Informations manquantes. Verifiez prenom, nom, email et date_heure."

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return f"L'adresse email '{email}' semble incorrecte. Demandez au client de reepeler son email lettre par lettre."

        try:
            event = book_appointment(prenom, nom, email, date_heure, besoin)
            calendar_event_id = event.get("id", "")
            save_appointment(prenom, nom, email, date_heure, besoin, call_id, calendar_event_id)
        except ValueError as e:
            return f"Erreur de date : {e}"
        except Exception as e:
            return f"Erreur lors de la reservation : {e}"

        tz = pytz.timezone("Europe/Paris")
        dt = datetime.fromisoformat(event["start"]["dateTime"]).astimezone(tz)

        return (
            f"Rendez-vous confirme ! {prenom}, votre consultation est reservee "
            f"le {DAYS_FR[dt.weekday()]} {dt.day} {MONTHS_FR[dt.month]} a {dt.hour}h. "
            f"Une invitation Google Calendar a ete envoyee a {email}."
        )

    return f"Outil '{name}' non reconnu."


# ── Webhook Google Calendar ───────────────────────────────────────

@app.post("/google-calendar-webhook")
async def google_calendar_webhook(request: Request):
    resource_state = request.headers.get("X-Goog-Resource-State", "")

    # Premier message de sync — juste confirmer la reception
    if resource_state == "sync":
        return Response(status_code=200)

    # Notification de changement — verifier les annulations
    if resource_state == "exists":
        try:
            cancelled = handle_calendar_change()
            if cancelled:
                print(f"[Calendar Watch] {cancelled} RDV annule(s) dans Airtable")
        except Exception as e:
            print(f"[Calendar Watch] Erreur traitement : {e}")

    return Response(status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
