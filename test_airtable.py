# -*- coding: utf-8 -*-
"""Test de connexion et permissions Airtable"""
import sys
import io
import requests
import os
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv()

API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("=" * 60)
print("TEST CONNEXION AIRTABLE")
print("=" * 60)
print(f"\nAPI_KEY : {API_KEY[:20]}..." if API_KEY else "API_KEY : MANQUANT")
print(f"BASE_ID : {BASE_ID}")

# Test 1: Lister les workspaces
print("\n1. Test workspaces...")
try:
    r = requests.get("https://api.airtable.com/v0/meta/workspaces", headers=HEADERS)
    if r.status_code == 200:
        workspaces = r.json().get("workspaces", [])
        print(f"   OK - {len(workspaces)} workspace(s) trouve(s)")
        for ws in workspaces:
            print(f"     - {ws['name']} (ID: {ws['id']})")
    else:
        print(f"   ERREUR {r.status_code}: {r.text}")
except Exception as e:
    print(f"   ERREUR: {e}")

# Test 2: Lister les bases
print("\n2. Test bases...")
try:
    r = requests.get("https://api.airtable.com/v0/meta/bases", headers=HEADERS)
    if r.status_code == 200:
        bases = r.json().get("bases", [])
        print(f"   OK - {len(bases)} base(s) trouvee(s)")
        for base in bases:
            print(f"     - {base['name']} (ID: {base['id']})")
            if base['id'] == BASE_ID:
                print(f"       -> BASE TROUVEE dans le compte!")
    else:
        print(f"   ERREUR {r.status_code}: {r.text}")
except Exception as e:
    print(f"   ERREUR: {e}")

# Test 3: Acceder a la base specifique
if BASE_ID:
    print(f"\n3. Test acces a la base {BASE_ID}...")
    try:
        r = requests.get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", headers=HEADERS)
        if r.status_code == 200:
            tables = r.json().get("tables", [])
            print(f"   OK - {len(tables)} table(s) trouvee(s)")
            for table in tables:
                print(f"     - {table['name']} (ID: {table['id']})")
                fields = [f['name'] for f in table.get('fields', [])]
                print(f"       Champs: {', '.join(fields[:5])}")
        elif r.status_code == 403:
            print(f"   ERREUR 403: Permissions insuffisantes")
            print(f"   Le token n'a pas acces a cette base OU la base n'existe pas")
            print(f"\n   Solutions:")
            print(f"   1. Verifier que la base {BASE_ID} existe dans votre compte Airtable")
            print(f"   2. Recreer un token avec les scopes:")
            print(f"      - data.records:read")
            print(f"      - data.records:write")
            print(f"      - schema.bases:read")
            print(f"      - schema.bases:write")
            print(f"   3. Ou lancer: python create_airtable_base.py")
        else:
            print(f"   ERREUR {r.status_code}: {r.text}")
    except Exception as e:
        print(f"   ERREUR: {e}")

print("\n" + "=" * 60)
