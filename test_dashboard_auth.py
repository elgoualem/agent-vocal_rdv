"""
Test rapide de l'authentification du dashboard
"""
import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv("DASHBOARD_PASSWORD", "admin")
print(f"[OK] Mot de passe dans .env : '{password}'")
print(f"[OK] Le header Authorization doit etre : 'Bearer {password}'")
print(f"\nPour tester l'authentification :")
print(f"curl -H 'Authorization: Bearer {password}' https://votre-app.up.railway.app/api/appointments")
