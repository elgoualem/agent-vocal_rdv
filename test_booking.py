# -*- coding: utf-8 -*-
"""Test complet du système de réservation"""
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from calendar_service import get_available_slots, book_appointment
from airtable_service import save_appointment
from datetime import datetime
import pytz

print("=" * 60)
print("TEST COMPLET - AGENT VOCAL RDV")
print("=" * 60)

# 1. Récupérer les créneaux disponibles
print("\n1. Recherche de creneaux disponibles...")
slots = get_available_slots(days_ahead=14)
print(f"   OK - {len(slots)} creneaux trouves")

if not slots:
    print("   ERREUR - Aucun creneau disponible. Verifiez votre calendrier.")
    exit(1)

# Afficher les 3 premiers créneaux
print("\n   Premiers creneaux :")
for i, slot in enumerate(slots[:3], 1):
    print(f"   {i}. {slot.strftime('%Y-%m-%d %H:%M')}")

# 2. Réserver le premier créneau
print("\n2. Test de reservation...")
first_slot = slots[0]
date_str = first_slot.strftime("%Y-%m-%d %H:%M")

print(f"   Creneau selectionne : {date_str}")

try:
    event = book_appointment(
        prenom="Claude",
        nom="Test",
        email="test@example.com",
        date_heure=date_str,
        besoin="Test automatique du systeme"
    )

    event_id = event.get("id", "")
    print(f"   OK - Evenement Google Calendar cree (ID: {event_id[:20]}...)")

    # 3. Sauvegarder dans Airtable
    print("\n3. Sauvegarde dans Airtable...")
    save_appointment(
        prenom="Claude",
        nom="Test",
        email="test@example.com",
        date_heure=date_str,
        besoin="Test automatique du systeme",
        call_id="test_001",
        calendar_event_id=event_id
    )
    print("   OK - Contact enregistre dans Airtable")

    print("\n" + "=" * 60)
    print("OK - TEST REUSSI - Tous les composants fonctionnent")
    print("=" * 60)
    print(f"\nVerifiez :")
    print(f"  - Google Calendar : evenement le {first_slot.strftime('%Y-%m-%d %H:%M')}")
    print(f"  - Airtable : nouveau contact Claude Test")

except Exception as e:
    print(f"\n   ERREUR : {e}")
    import traceback
    traceback.print_exc()
