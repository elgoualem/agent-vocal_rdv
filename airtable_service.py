from pyairtable import Api
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_AVAILABILITY = [
    {"id": "default", "label": "Semaine", "jours": [0, 1, 2, 3, 4], "debut": 9, "fin": 17}
]


def _config_table():
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    return api.table(os.getenv("AIRTABLE_BASE_ID"), "Config")


def get_availability_config() -> list:
    try:
        records = _config_table().all(formula="{Cle}='disponibilites'")
        if records:
            data = json.loads(records[0]["fields"].get("Valeur", "[]"))
            # Migration : ancien format dict -> nouveau format liste
            if isinstance(data, dict):
                data = [{"id": "default", "label": "Semaine", **data}]
            return data
    except Exception as e:
        print(f"[Config] Erreur lecture : {e}")
    return DEFAULT_AVAILABILITY.copy()


def save_availability_config(slots: list):
    table = _config_table()
    records = table.all(formula="{Cle}='disponibilites'")
    valeur = json.dumps(slots)
    if records:
        table.update(records[0]["id"], {"Valeur": valeur})
    else:
        table.create({"Cle": "disponibilites", "Valeur": valeur})


def save_appointment(
    prenom: str,
    nom: str,
    email: str,
    date_heure: str,
    besoin: str,
    call_id: str = "",
    calendar_event_id: str = "",
) -> dict:
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.table(
        os.getenv("AIRTABLE_BASE_ID"),
        os.getenv("AIRTABLE_TABLE_NAME", "Rendez-vous"),
    )

    return table.create({
        "Prenom": prenom,
        "Nom": nom,
        "Email": email,
        "Date RDV": date_heure,
        "Besoin": besoin,
        "Statut": "Confirme",
        "Cree le": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Call ID": call_id,
        "Calendar Event ID": calendar_event_id,
    })


def update_status_by_event_id(calendar_event_id: str, status: str) -> bool:
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.table(
        os.getenv("AIRTABLE_BASE_ID"),
        os.getenv("AIRTABLE_TABLE_NAME", "Rendez-vous"),
    )
    formula = f"{{Calendar Event ID}} = '{calendar_event_id}'"
    records = table.all(formula=formula)
    if not records:
        return False
    table.update(records[0]["id"], {"Statut": status})
    return True
