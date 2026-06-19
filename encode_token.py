# -*- coding: utf-8 -*-
"""
Apres avoir fait l'auth Google localement (token.json cree),
lancez ce script pour obtenir la valeur a mettre dans Railway.

Usage : python encode_token.py
"""
import base64
import os

TOKEN_FILE = "token.json"

if not os.path.exists(TOKEN_FILE):
    print("[ERREUR] token.json introuvable.")
    print("  Lancez d'abord : python -c \"from calendar_service import get_service; get_service()\"")
    raise SystemExit(1)

with open(TOKEN_FILE, "r") as f:
    content = f.read()

encoded = base64.b64encode(content.encode()).decode()

print("=" * 60)
print("Copiez cette variable dans Railway > Variables :")
print("=" * 60)
print(f"GOOGLE_TOKEN_JSON={encoded}")
print("=" * 60)
