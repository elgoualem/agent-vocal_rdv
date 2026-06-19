"""
Crée automatiquement la base Airtable "Agent RDV – MechaPizzAI"
avec la table "Rendez-vous" et tous ses champs.

Prérequis : AIRTABLE_API_KEY dans .env
Token scope requis : schema.bases:write, schema.bases:read
"""
import requests
import os
from dotenv import load_dotenv, set_key

load_dotenv()

API_KEY = os.getenv("AIRTABLE_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def get_first_workspace_id() -> str:
    r = requests.get("https://api.airtable.com/v0/meta/workspaces", headers=HEADERS)
    r.raise_for_status()
    workspaces = r.json().get("workspaces", [])
    if not workspaces:
        raise RuntimeError("Aucun workspace Airtable trouvé.")
    return workspaces[0]["id"]


def create_base(workspace_id: str) -> dict:
    payload = {
        "name": "Agent RDV – MechaPizzAI",
        "workspaceId": workspace_id,
        "tables": [
            {
                "name": "Rendez-vous",
                "fields": [
                    {"name": "Prénom",   "type": "singleLineText"},
                    {"name": "Nom",      "type": "singleLineText"},
                    {"name": "Email",    "type": "email"},
                    {"name": "Date RDV", "type": "singleLineText"},
                    {"name": "Besoin",   "type": "multilineText"},
                    {
                        "name": "Statut",
                        "type": "singleSelect",
                        "options": {
                            "choices": [
                                {"name": "Confirmé", "color": "greenBright"},
                                {"name": "Annulé",   "color": "redBright"},
                                {"name": "Terminé",  "color": "blueBright"},
                            ]
                        },
                    },
                    {"name": "Créé le", "type": "singleLineText"},
                    {"name": "Call ID", "type": "singleLineText"},
                ],
            }
        ],
    }
    r = requests.post("https://api.airtable.com/v0/meta/bases", headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    if not API_KEY:
        print("❌ AIRTABLE_API_KEY manquant dans .env")
        print("   1. Va sur https://airtable.com/create/tokens")
        print("   2. Crée un token avec les scopes : schema.bases:write, schema.bases:read, data.records:write")
        print("   3. Ajoute AIRTABLE_API_KEY=ton_token dans .env")
        raise SystemExit(1)

    print("🗃️  Récupération du workspace…")
    workspace_id = get_first_workspace_id()
    print(f"   Workspace : {workspace_id}")

    print("🗃️  Création de la base Airtable…")
    base = create_base(workspace_id)
    base_id = base["id"]

    print(f"✅ Base créée : {base['name']} (ID : {base_id})")
    set_key(".env", "AIRTABLE_BASE_ID", base_id)
    print("   ✅ AIRTABLE_BASE_ID enregistré dans .env")
