# -*- coding: utf-8 -*-
"""
Lance ce script UNE FOIS pour creer l'assistant VAPI et lui assigner un numero.
Prerequis : WEBHOOK_URL dans .env (ngrok ou URL de prod).
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

VAPI_KEY     = os.getenv("VAPI_PRIVATE_KEY")
WEBHOOK_URL  = os.getenv("WEBHOOK_URL")
BASE_URL     = "https://api.vapi.ai"
HEADERS      = {"Authorization": f"Bearer {VAPI_KEY}", "Content-Type": "application/json"}

COMPANY_NAME  = os.getenv("COMPANY_NAME", "notre societe")
COMPANY_DESC  = os.getenv("COMPANY_DESCRIPTION", "specialiste dans son domaine")
FIRST_MESSAGE = os.getenv(
    "AGENT_FIRST_MESSAGE",
    f"Bonjour ! Vous etes sur la ligne de {COMPANY_NAME}. "
    "Je suis votre assistante pour la prise de rendez-vous. Comment puis-je vous aider ?"
)

SYSTEM_PROMPT = f"""Tu es l'assistante vocale de {COMPANY_NAME}, {COMPANY_DESC}. \
Tu prends les rendez-vous pour des consultations decouverte d'1 heure.

DEROULEMENT :
1. Accueille chaleureusement l'appelant
2. Demande son prenom, puis son nom de famille separement
3. Repete le nom de famille lettre par lettre pour confirmer : "Donc votre nom s'ecrit B-O-N-D, c'est bien ca ?"
4. Pose 2 questions max pour cerner son besoin (IA, automatisation, strategie de contenu ?)
5. Demande l'adresse email en suivant STRICTEMENT la procedure EMAIL ci-dessous
6. Verifie les creneaux dispo en appelant verifier_disponibilites
7. Annonce 3 creneaux et laisse le client choisir
8. Repete la date et l'heure choisies, demande confirmation, puis appelle reserver_creneau
9. Recapitule prenom, nom, email et creneau avant de conclure

PROCEDURE EMAIL (obligatoire, ne jamais sauter ces etapes) :
a) Demande : "Pouvez-vous me donner votre adresse email ?"
b) Quand le client la donne, decompose-la immediatement en 3 parties et repete chaque partie :
   - La partie avant l'arobase : "Donc avant l'arobase j'ai [partie], c'est bien ca ?"
   - Le nom de domaine : "Apres l'arobase j'ai [domaine], c'est bien ca ?"
   - L'extension : "Et l'extension c'est point [extension] ?"
c) Epelle lettre par lettre toute partie qui contient un chiffre, un tiret ou un point
d) Confirme l'email complet : "Votre email complet est donc [email complet], je confirme ?"
e) N'appelle reserver_creneau QU'APRES cette confirmation explicite du client

REGLES :
- Parle toujours en francais
- Sois chaleureux, professionnel et concis
- Pour les noms difficiles, utilise l'alphabet phonetique : A comme Alpha, B comme Bravo, etc.
- Ne propose jamais plus de 3 creneaux a la fois
- Si aucun creneau n'est dispo, propose au client de rappeler sous 24h
- N'invente jamais de creneau - utilise uniquement ceux retournes par verifier_disponibilites
- En cas de doute sur l'email, demande toujours a reepeler plutot que de supposer"""

ASSISTANT_CONFIG = {
    "name": f"Agent RDV - {COMPANY_NAME}",
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "verifier_disponibilites",
                    "description": (
                        "Verifie les creneaux de RDV disponibles (consultations d'1h). "
                        "Appelle cet outil des que le client est pret a choisir une date."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "jours": {
                                "type": "integer",
                                "description": "Nombre de jours a scanner (defaut: 7)",
                            }
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "reserver_creneau",
                    "description": (
                        "Reserve un RDV d'1h sur Google Calendar et envoie une invitation par email. "
                        "N'appelle cet outil qu'apres confirmation explicite du client."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prenom": {"type": "string", "description": "Prenom du client"},
                            "nom": {"type": "string", "description": "Nom du client"},
                            "email": {"type": "string", "description": "Email du client"},
                            "date_heure": {
                                "type": "string",
                                "description": "Date et heure au format YYYY-MM-DD HH:MM (ex : 2025-05-15 14:00)",
                            },
                            "besoin": {
                                "type": "string",
                                "description": "Resume du besoin du client en 1-2 phrases",
                            },
                        },
                        "required": ["prenom", "nom", "email", "date_heure", "besoin"],
                    },
                },
            },
        ],
    },
    "voice": {
        "provider": "11labs",
        "voiceId": "3C1zYzXNXNzrB66ON8rj",
        "model": "eleven_multilingual_v2",
        "stability": 0.5,
        "similarityBoost": 0.75,
    },
    "transcriber": {
        "provider": "deepgram",
        "model": "nova-2",
        "language": "fr",
    },
    "firstMessage": FIRST_MESSAGE,
    "serverUrl": WEBHOOK_URL,
    "endCallMessage": "Merci pour votre appel. A tres bientot !",
    "endCallFunctionEnabled": True,
    "silenceTimeoutSeconds": 30,
    "maxDurationSeconds": 600,
    "recordingEnabled": True,
    "backgroundSound": "off",
}


def create_assistant():
    r = requests.post(f"{BASE_URL}/assistant", headers=HEADERS, json=ASSISTANT_CONFIG)
    if r.status_code == 201:
        a = r.json()
        print(f"[OK] Assistant cree : {a['name']} (ID: {a['id']})")
        return a
    print(f"[ERREUR] {r.status_code} : {r.text}")
    return None


def assign_phone_number(assistant_id: str):
    r = requests.get(f"{BASE_URL}/phone-number", headers=HEADERS)
    existing = r.json() if r.ok else []

    if existing:
        num = existing[0]
        patch = requests.patch(
            f"{BASE_URL}/phone-number/{num['id']}",
            headers=HEADERS,
            json={"assistantId": assistant_id},
        )
        if patch.ok:
            print(f"[OK] Numero {num['number']} assigne a l'assistant")
        return num

    r = requests.post(
        f"{BASE_URL}/phone-number",
        headers=HEADERS,
        json={"provider": "vapi", "assistantId": assistant_id},
    )
    if r.status_code == 201:
        phone = r.json()
        print(f"[OK] Numero achete : {phone.get('number')}")
        return phone

    print(
        "[INFO] Achat automatique indisponible.\n"
        f"  -> Allez sur app.vapi.ai > Phone Numbers > Buy\n"
        f"  -> Assignez l'assistant ID : {assistant_id}"
    )
    return None


if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("[ERREUR] WEBHOOK_URL manquant dans .env")
        print("  Lancez ngrok : ngrok http 8000")
        print("  Puis ajoutez WEBHOOK_URL=https://xxxx.ngrok-free.app/webhook dans .env")
        raise SystemExit(1)

    print("Creation de l'assistant VAPI...")
    assistant = create_assistant()

    if assistant:
        print("Attribution du numero de telephone...")
        phone = assign_phone_number(assistant["id"])

        print("\n" + "=" * 50)
        print("CONFIGURATION TERMINEE")
        print("=" * 50)
        print(f"  Assistant ID : {assistant['id']}")
        if phone:
            print(f"  Numero       : {phone.get('number', 'Voir dashboard')}")
        print(f"  Webhook      : {WEBHOOK_URL}")
        print(f"\n  Ajoutez dans votre .env :")
        print(f"  VAPI_ASSISTANT_ID={assistant['id']}")
