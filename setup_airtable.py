import requests, os
from dotenv import load_dotenv
load_dotenv()

API_KEY   = os.getenv("AIRTABLE_API_KEY")
BASE_ID   = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Rendez-vous")
HEADERS   = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

REQUIRED_FIELDS = [
    {"name": "Prenom",    "type": "singleLineText"},
    {"name": "Nom",       "type": "singleLineText"},
    {"name": "Email",     "type": "email"},
    {"name": "Date RDV",  "type": "singleLineText"},
    {"name": "Besoin",    "type": "multilineText"},
    {"name": "Statut",    "type": "singleSelect", "options": {"choices": [
        {"name": "Confirme", "color": "greenBright"},
        {"name": "Annule",   "color": "redBright"},
        {"name": "Termine",  "color": "blueBright"},
    ]}},
    {"name": "Cree le",             "type": "singleLineText"},
    {"name": "Call ID",             "type": "singleLineText"},
    {"name": "Calendar Event ID",   "type": "singleLineText"},
]

def get_table_schema():
    r = requests.get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", headers=HEADERS)
    r.raise_for_status()
    tables = r.json().get("tables", [])
    for t in tables:
        if t["name"] == TABLE_NAME:
            return t
    return None

def get_table_id(table):
    return table["id"]

def create_field(table_id, field):
    r = requests.post(
        f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}/fields",
        headers=HEADERS,
        json=field
    )
    return r.status_code, r.json()

def test_write(table_id):
    r = requests.post(
        f"https://api.airtable.com/v0/{BASE_ID}/{table_id}",
        headers=HEADERS,
        json={"fields": {
            "Prenom": "TEST",
            "Nom": "TEST",
            "Email": "test@test.com",
            "Date RDV": "2026-01-01 09:00",
            "Besoin": "Test acces",
            "Statut": "Confirme",
            "Cree le": "2026-01-01 09:00",
            "Call ID": "test-call"
        }}
    )
    return r.status_code, r.json()

def delete_test_record(record_id):
    r = requests.delete(
        f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}",
        headers=HEADERS
    )
    return r.status_code

def rename_table(table_id, new_name):
    r = requests.patch(
        f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}",
        headers=HEADERS,
        json={"name": new_name}
    )
    return r.status_code, r.json()

if __name__ == "__main__":
    print(f"Base ID    : {BASE_ID}")
    print(f"Table      : {TABLE_NAME}")
    print()

    # 1. Recupere le schema
    print("[1/4] Recuperation du schema de la table...")
    r = requests.get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", headers=HEADERS)
    all_tables = r.json().get("tables", [])
    table = next((t for t in all_tables if t["name"] == TABLE_NAME), None)

    if not table:
        # Renomme la premiere table existante
        first = all_tables[0] if all_tables else None
        if first:
            print(f"      Table '{TABLE_NAME}' absente — renommage de '{first['name']}'...")
            status, resp = rename_table(first["id"], TABLE_NAME)
            if status == 200:
                table = resp
                print(f"      [OK] Table renommee en '{TABLE_NAME}'")
            else:
                print(f"      [ERREUR] {status} : {resp}")
                raise SystemExit(1)
        else:
            print("[ERREUR] Aucune table trouvee dans la base.")
            raise SystemExit(1)

    table_id = get_table_id(table)
    existing = {f["name"] for f in table.get("fields", [])}
    print(f"      Champs existants : {existing}")

    # 2. Cree les champs manquants
    print("\n[2/4] Verification et creation des champs manquants...")
    for field in REQUIRED_FIELDS:
        if field["name"] in existing:
            print(f"      [OK] '{field['name']}' existe deja")
        else:
            status, resp = create_field(table_id, field)
            if status == 200:
                print(f"      [CREE] '{field['name']}'")
            else:
                print(f"      [ERREUR] '{field['name']}' : {resp}")

    # 3. Test d'ecriture
    print("\n[3/4] Test d'ecriture dans Airtable...")
    status, resp = test_write(table_id)
    if status == 200:
        record_id = resp["id"]
        delete_test_record(record_id)
        print(f"      [OK] Ecriture et suppression reussies")
    else:
        print(f"      [ERREUR] {status} : {resp}")

    # 4. Rafraichit le schema pour lister les champs finaux
    print("\n[4/4] Schema final de la table...")
    r2 = requests.get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", headers=HEADERS)
    final_table = next((t for t in r2.json().get("tables", []) if t["name"] == TABLE_NAME), None)
    if final_table:
        champs = [f["name"] for f in final_table.get("fields", [])]
        print(f"      Champs : {champs}")

    # 5. Cree la table Config si absente
    print("\n[5/5] Table Config (disponibilites)...")
    r3 = requests.get(f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables", headers=HEADERS)
    all_tables_now = r3.json().get("tables", [])
    config_table = next((t for t in all_tables_now if t["name"] == "Config"), None)

    if config_table:
        print("      [OK] Table 'Config' existe deja")
    else:
        rc = requests.post(
            f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables",
            headers=HEADERS,
            json={
                "name": "Config",
                "fields": [
                    {"name": "Cle",    "type": "singleLineText"},
                    {"name": "Valeur", "type": "multilineText"},
                ]
            }
        )
        if rc.status_code == 200:
            print("      [CREE] Table 'Config'")
            config_table = rc.json()
        else:
            print(f"      [ERREUR] {rc.text}")

    # Insere la config par defaut
    if config_table:
        import json
        api_url = f"https://api.airtable.com/v0/{BASE_ID}/Config"
        existing = requests.get(api_url, headers=HEADERS,
                                params={"filterByFormula": "{Cle}='disponibilites'"}).json()
        if not existing.get("records"):
            default = {"jours": [0, 1, 2, 3, 4], "debut": 9, "fin": 17}
            requests.post(api_url, headers=HEADERS, json={
                "fields": {"Cle": "disponibilites", "Valeur": json.dumps(default)}
            })
            print(f"      [OK] Config par defaut inseree : {default}")
        else:
            print("      [OK] Config par defaut existe deja")

    print("\n[OK] Airtable pret !")
