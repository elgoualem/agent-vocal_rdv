# -*- coding: utf-8 -*-
"""Trouve le BASE_ID de la base 'agent vocal rdv'"""
import sys
import io
import requests
import os
from dotenv import load_dotenv, set_key

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv()

API_KEY = os.getenv("AIRTABLE_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("=" * 60)
print("RECHERCHE DE LA BASE 'agent vocal rdv'")
print("=" * 60)

# Methode 1: Via l'API meta/bases (necessite schema.bases:read)
print("\nMethode 1: API meta/bases...")
try:
    r = requests.get("https://api.airtable.com/v0/meta/bases", headers=HEADERS)
    if r.status_code == 200:
        bases = r.json().get("bases", [])
        print(f"  {len(bases)} base(s) trouvee(s):")
        for base in bases:
            print(f"    - {base['name']}")
            print(f"      ID: {base['id']}")
            print(f"      Permission: {base.get('permissionLevel', 'N/A')}")

            if "agent vocal rdv" in base['name'].lower():
                print(f"\n  >>> BASE TROUVEE! <<<")
                print(f"      Nom: {base['name']}")
                print(f"      ID: {base['id']}")

                # Mettre a jour le .env
                set_key(".env", "AIRTABLE_BASE_ID", base['id'])
                print(f"\n  OK - AIRTABLE_BASE_ID mis a jour dans .env")
                print(f"\n  Relancez maintenant: python setup_airtable.py")
                sys.exit(0)
    elif r.status_code == 403:
        print(f"  Le token n'a pas la permission 'schema.bases:read'")
    else:
        print(f"  ERREUR {r.status_code}: {r.text}")
except Exception as e:
    print(f"  ERREUR: {e}")

# Methode 2: Demander a l'utilisateur
print("\n" + "=" * 60)
print("BASE NON TROUVEE AUTOMATIQUEMENT")
print("=" * 60)
print("\nPour trouver votre BASE_ID manuellement:")
print("1. Allez sur https://airtable.com")
print("2. Ouvrez la base 'agent vocal rdv'")
print("3. Cliquez sur 'Help' > 'API documentation'")
print("4. Le BASE_ID commence par 'app' et se trouve dans l'URL")
print("   Exemple: https://airtable.com/app9ARpnvh7J82J3O/api/docs")
print("                                    ^^^^^^^^^^^^^^^^^")
print("\nOu recreez un token avec TOUTES les permissions:")
print("  https://airtable.com/create/tokens")
print("  Scopes requis:")
print("    - data.records:read")
print("    - data.records:write")
print("    - schema.bases:read")
print("    - schema.bases:write")
print("\n  IMPORTANT: Selectionnez la base 'agent vocal rdv' dans les permissions!")
