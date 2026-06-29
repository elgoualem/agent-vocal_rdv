# -*- coding: utf-8 -*-
"""Test complet du systeme Agent Vocal RDV"""
import sys
import io
import os
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv()

print("=" * 70)
print("ETAT DU SYSTEME - AGENT VOCAL RDV")
print("=" * 70)

# 1. Configuration
print("\n1. CONFIGURATION")
print("-" * 70)

config = {
    "COMPANY_NAME": os.getenv("COMPANY_NAME"),
    "VAPI_PRIVATE_KEY": os.getenv("VAPI_PRIVATE_KEY", "")[:20] + "..." if os.getenv("VAPI_PRIVATE_KEY") else None,
    "VAPI_ASSISTANT_ID": os.getenv("VAPI_ASSISTANT_ID") or "NON DEFINI",
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")[:20] + "..." if os.getenv("OPENAI_API_KEY") else None,
    "AIRTABLE_API_KEY": os.getenv("AIRTABLE_API_KEY", "")[:20] + "..." if os.getenv("AIRTABLE_API_KEY") else None,
    "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID"),
    "GOOGLE_CALENDAR_ID": os.getenv("GOOGLE_CALENDAR_ID"),
    "WEBHOOK_URL": os.getenv("WEBHOOK_URL"),
}

for key, value in config.items():
    status = "OK" if value and "NON DEFINI" not in str(value) else "MANQUANT"
    symbol = "[+]" if status == "OK" else "[X]"
    print(f"  {symbol} {key}: {value}")

# 2. Google Calendar
print("\n2. GOOGLE CALENDAR")
print("-" * 70)
try:
    from calendar_service import get_service, get_available_slots
    service = get_service()
    slots = get_available_slots(7)
    print(f"  [+] Connexion reussie")
    print(f"  [+] {len(slots)} creneaux disponibles sur 7 jours")
    if slots:
        print(f"      Premier creneau: {slots[0].strftime('%Y-%m-%d %H:%M')}")
except Exception as e:
    print(f"  [X] ERREUR: {e}")

# 3. Airtable
print("\n3. AIRTABLE")
print("-" * 70)
try:
    import requests
    headers = {"Authorization": f"Bearer {os.getenv('AIRTABLE_API_KEY')}"}
    r = requests.get(
        f"https://api.airtable.com/v0/meta/bases/{os.getenv('AIRTABLE_BASE_ID')}/tables",
        headers=headers
    )
    if r.status_code == 200:
        tables = r.json().get("tables", [])
        print(f"  [+] Connexion reussie")
        print(f"  [+] {len(tables)} table(s) trouvee(s)")
        for table in tables:
            print(f"      - {table['name']}")
    else:
        print(f"  [X] ERREUR {r.status_code}")
except Exception as e:
    print(f"  [X] ERREUR: {e}")

# 4. Serveur FastAPI
print("\n4. SERVEUR FASTAPI")
print("-" * 70)
try:
    import requests
    r = requests.get("http://localhost:8000/", timeout=2)
    if r.status_code == 200:
        print(f"  [+] Serveur actif sur http://localhost:8000")
        print(f"      Status: {r.json().get('status')}")
    else:
        print(f"  [X] Serveur repond mais erreur {r.status_code}")
except:
    print(f"  [-] Serveur non demarre (lancez: python launch.py)")

# 5. VAPI
print("\n5. VAPI")
print("-" * 70)
assistant_id = os.getenv("VAPI_ASSISTANT_ID")
if assistant_id and "NON DEFINI" not in assistant_id:
    print(f"  [+] Assistant configure: {assistant_id}")
    print(f"  [+] Pour tester: appelez le numero VAPI")
else:
    print(f"  [-] Assistant non configure")
    print(f"      Action: python setup_vapi.py")

# Résumé
print("\n" + "=" * 70)
print("RESUME")
print("=" * 70)

ready = all([
    config["VAPI_PRIVATE_KEY"],
    config["OPENAI_API_KEY"],
    config["AIRTABLE_API_KEY"],
    config["AIRTABLE_BASE_ID"],
    config["GOOGLE_CALENDAR_ID"],
])

if ready:
    print("  [+] Systeme pret a fonctionner!")
    if "NON DEFINI" in str(config["VAPI_ASSISTANT_ID"]):
        print("\n  Prochaine etape:")
        print("    1. Deployer sur Railway (ou ngrok pour test local)")
        print("    2. Lancer: python setup_vapi.py")
        print("    3. Appeler le numero VAPI pour tester")
    else:
        print("\n  Systeme 100% operationnel!")
        print("    - Appelez le numero VAPI pour prendre un RDV")
        print("    - Dashboard: http://localhost:8000/dashboard")
else:
    print("  [X] Configuration incomplete")
    print("  Verifiez les elements manquants ci-dessus")

print("=" * 70)
