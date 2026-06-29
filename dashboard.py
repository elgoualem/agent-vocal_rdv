from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
from pyairtable import Api
from typing import Optional
import os

router = APIRouter()


def verify_token(authorization: Optional[str] = Header(None)):
    password = os.getenv("DASHBOARD_PASSWORD", "admin")
    if not authorization or authorization != f"Bearer {password}":
        raise HTTPException(status_code=401, detail="Non autorise")


def get_table():
    api = Api(os.getenv("AIRTABLE_API_KEY"))
    return api.table(
        os.getenv("AIRTABLE_BASE_ID"),
        os.getenv("AIRTABLE_TABLE_NAME", "Rendez-vous")
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return HTMLResponse(DASHBOARD_HTML)


@router.get("/api/appointments")
async def get_appointments(_=Depends(verify_token)):
    try:
        table = get_table()
        records = table.all(sort=["Date RDV"])
        records.reverse()
        return {"records": records, "total": len(records)}
    except Exception as e:
        import traceback
        print(f"[ERREUR /api/appointments] {type(e).__name__}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur Airtable: {str(e)}")


@router.get("/api/debug-airtable")
async def debug_airtable(_=Depends(verify_token)):
    """Endpoint de debug pour diagnostiquer la connexion Airtable."""
    import os
    api_key = os.getenv("AIRTABLE_API_KEY", "")
    base_id = os.getenv("AIRTABLE_BASE_ID", "")
    table_name = os.getenv("AIRTABLE_TABLE_NAME", "Rendez-vous")
    try:
        table = get_table()
        records = table.all()
        return {
            "status": "OK",
            "api_key_prefix": api_key[:15] + "...",
            "base_id": base_id,
            "table_name": table_name,
            "record_count": len(records)
        }
    except Exception as e:
        return {
            "status": "ERREUR",
            "api_key_prefix": api_key[:15] + "..." if api_key else "VIDE",
            "base_id": base_id,
            "table_name": table_name,
            "error": str(e)
        }


@router.patch("/api/appointments/{record_id}/status")
async def update_status(request: Request, record_id: str, _=Depends(verify_token)):
    body = await request.json()
    status = body.get("status")

    table = get_table()
    record = table.get(record_id)
    fields = record.get("fields", {})

    table.update(record_id, {"Statut": status})

    calendar_result = "non concerne"
    if status == "Annule":
        calendar_event_id = fields.get("Calendar Event ID", "")
        print(f"[Cancel] record={record_id} | calendar_event_id='{calendar_event_id}'")
        if calendar_event_id:
            from calendar_service import cancel_event
            ok = cancel_event(calendar_event_id)
            calendar_result = "OK" if ok else "ERREUR"
            print(f"[Cancel] Google Calendar cancel -> {calendar_result}")
        else:
            calendar_result = "Calendar Event ID vide"
            print(f"[Cancel] Calendar Event ID absent pour record {record_id}")

    return {"ok": True, "calendar": calendar_result}


@router.get("/debug/appointment/{record_id}")
async def debug_appointment(record_id: str, _=Depends(verify_token)):
    """Inspecte un record Airtable pour voir le Calendar Event ID."""
    table = get_table()
    record = table.get(record_id)
    fields = record.get("fields", {})
    return {
        "record_id": record_id,
        "Calendar Event ID": fields.get("Calendar Event ID", "VIDE"),
        "Statut": fields.get("Statut"),
        "Prenom": fields.get("Prenom"),
    }


@router.get("/api/availability")
async def get_availability(_=Depends(verify_token)):
    from airtable_service import get_availability_config
    return get_availability_config()


@router.post("/api/availability")
async def save_availability(request: Request, _=Depends(verify_token)):
    from airtable_service import save_availability_config
    slots = await request.json()  # liste de plages
    save_availability_config(slots)
    return {"ok": True}


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard RDV - Agent Vocal</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config = { darkMode: 'class' }</script>
</head>
<body class="bg-gray-950 text-white min-h-screen font-sans">

  <!-- LOGIN -->
  <div id="login-screen" class="fixed inset-0 bg-gray-950 flex items-center justify-center z-50">
    <div class="bg-gray-900 border border-gray-800 rounded-2xl p-10 w-full max-w-sm shadow-2xl">
      <div class="text-center mb-8">
        <div class="text-4xl mb-3">🎙️</div>
        <h1 class="text-2xl font-bold">Dashboard RDV</h1>
        <p class="text-gray-400 text-sm mt-1">Agent Vocal MechaPizzAI</p>
      </div>
      <input id="pwd-input" type="password" placeholder="Mot de passe"
        class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 mb-4 focus:outline-none focus:border-purple-500"
        onkeydown="if(event.key==='Enter') login()">
      <button onclick="login()"
        class="w-full bg-purple-600 hover:bg-purple-500 transition py-3 rounded-lg font-semibold">
        Acceder
      </button>
      <p id="login-error" class="text-red-400 text-sm text-center mt-3 hidden">Mot de passe incorrect</p>
    </div>
  </div>

  <!-- DASHBOARD -->
  <div id="app" class="hidden">

    <!-- Header -->
    <header class="border-b border-gray-800 px-8 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-2xl">🎙️</span>
        <div>
          <h1 class="font-bold text-lg leading-none">Dashboard RDV</h1>
          <p class="text-gray-400 text-xs" id="company-subtitle">Agent Vocal</p>
        </div>
      </div>
      <div class="flex gap-2">
        <button onclick="showTab('rdv')" id="tab-rdv"
          class="text-sm px-4 py-2 rounded-lg transition bg-purple-600">
          Rendez-vous
        </button>
        <button onclick="showTab('dispo')" id="tab-dispo"
          class="text-sm px-4 py-2 rounded-lg transition bg-gray-800 hover:bg-gray-700">
          Disponibilites
        </button>
        <button onclick="loadData()"
          class="text-sm bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg transition">
          Actualiser
        </button>
      </div>
    </header>

    <main class="p-8">

      <!-- Stats -->
      <div id="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"></div>

      <!-- Filters -->
      <div class="flex gap-2 mb-6 flex-wrap">
        <button onclick="setFilter('all')"       id="f-all"      class="filter-btn px-4 py-2 rounded-lg text-sm font-medium transition bg-purple-600">Tous</button>
        <button onclick="setFilter('Confirme')"  id="f-Confirme" class="filter-btn px-4 py-2 rounded-lg text-sm font-medium transition bg-gray-800 hover:bg-gray-700">Confirme</button>
        <button onclick="setFilter('Termine')"   id="f-Termine"  class="filter-btn px-4 py-2 rounded-lg text-sm font-medium transition bg-gray-800 hover:bg-gray-700">Termine</button>
        <button onclick="setFilter('Annule')"    id="f-Annule"   class="filter-btn px-4 py-2 rounded-lg text-sm font-medium transition bg-gray-800 hover:bg-gray-700">Annule</button>
      </div>

      <!-- Table -->
      <div id="section-rdv" class="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wider">
              <th class="px-6 py-4 text-left">Client</th>
              <th class="px-6 py-4 text-left">Email</th>
              <th class="px-6 py-4 text-left">Date RDV</th>
              <th class="px-6 py-4 text-left">Besoin</th>
              <th class="px-6 py-4 text-left">Statut</th>
              <th class="px-6 py-4 text-left">Actions</th>
            </tr>
          </thead>
          <tbody id="table-body">
            <tr><td colspan="6" class="px-6 py-12 text-center text-gray-500">Chargement...</td></tr>
          </tbody>
        </table>
      </div>

      <!-- Section Disponibilites (cachee par defaut) -->
      <div id="section-dispo" class="hidden max-w-2xl">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-bold">Plages de disponibilite</h2>
          <button onclick="addSlot()"
            class="bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg text-sm font-medium transition">
            + Ajouter une plage
          </button>
        </div>
        <div id="slots-container" class="flex flex-col gap-4">
          <p class="text-gray-500 text-sm">Chargement...</p>
        </div>
      </div>

    </main>
  </div>

<script>
  let token = localStorage.getItem('dashboard_token') || '';
  let allRecords = [];
  let currentFilter = 'all';

  function login() {
    token = document.getElementById('pwd-input').value;
    document.getElementById('login-error').classList.add('hidden');
    loadData();
  }

  // Tentative de connexion automatique si token deja en memoire
  if (token) loadData();

  async function loadData() {
    const r = await fetch('/api/appointments', {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (r.status === 401) {
      document.getElementById('login-error').classList.remove('hidden');
      return;
    }
    if (!r.ok) {
      console.error('Erreur API:', r.status);
      document.getElementById('login-error').textContent = 'Erreur serveur. Verifiez les logs Railway.';
      document.getElementById('login-error').classList.remove('hidden');
      return;
    }
    const data = await r.json();
    allRecords = data.records || [];
    localStorage.setItem('dashboard_token', token);
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    renderStats();
    renderTable();
  }

  function renderStats() {
    const total     = allRecords.length;
    const confirmed = allRecords.filter(r => r.fields.Statut === 'Confirme').length;
    const done      = allRecords.filter(r => r.fields.Statut === 'Termine').length;
    const rate      = total > 0 ? Math.round((confirmed + done) / total * 100) : 0;

    const cards = [
      { label: 'Total RDV',         value: total,     color: 'text-white' },
      { label: 'Confirmes',         value: confirmed, color: 'text-green-400' },
      { label: 'Termines',          value: done,      color: 'text-blue-400' },
      { label: 'Taux confirmation', value: rate + '%', color: 'text-purple-400' },
    ];

    document.getElementById('stats').innerHTML = cards.map(c => `
      <div class="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <div class="text-3xl font-bold ${c.color}">${c.value}</div>
        <div class="text-gray-400 text-sm mt-1">${c.label}</div>
      </div>
    `).join('');
  }

  function setFilter(f) {
    currentFilter = f;
    document.querySelectorAll('.filter-btn').forEach(b => {
      b.className = b.className.replace('bg-purple-600', 'bg-gray-800 hover:bg-gray-700');
    });
    document.getElementById('f-' + f).className =
      document.getElementById('f-' + f).className.replace('bg-gray-800 hover:bg-gray-700', 'bg-purple-600');
    renderTable();
  }

  const STATUS_STYLE = {
    'Confirme': 'bg-green-900 text-green-300',
    'Termine':  'bg-blue-900 text-blue-300',
    'Annule':   'bg-red-900 text-red-300',
  };

  function renderTable() {
    const records = currentFilter === 'all'
      ? allRecords
      : allRecords.filter(r => r.fields.Statut === currentFilter);

    if (!records.length) {
      document.getElementById('table-body').innerHTML =
        '<tr><td colspan="6" class="px-6 py-12 text-center text-gray-500">Aucun rendez-vous</td></tr>';
      return;
    }

    document.getElementById('table-body').innerHTML = records.map(r => {
      const f = r.fields;
      const badge = STATUS_STYLE[f.Statut] || 'bg-gray-700 text-gray-300';
      const actions = f.Statut === 'Confirme' ? `
        <button onclick="updateStatus('${r.id}','Termine')"
          class="text-xs bg-blue-800 hover:bg-blue-700 px-3 py-1 rounded mr-1 transition">Termine</button>
        <button onclick="updateStatus('${r.id}','Annule')"
          class="text-xs bg-red-900 hover:bg-red-800 px-3 py-1 rounded transition">Annuler</button>
      ` : '<span class="text-gray-600">—</span>';

      return `
        <tr class="border-t border-gray-800 hover:bg-gray-800/40 transition">
          <td class="px-6 py-4 font-medium">${f.Prenom || ''} ${f.Nom || ''}</td>
          <td class="px-6 py-4 text-gray-300">${f.Email || ''}</td>
          <td class="px-6 py-4 text-gray-300">${f['Date RDV'] || ''}</td>
          <td class="px-6 py-4 text-gray-400 max-w-xs">
            <div class="truncate max-w-[200px]" title="${(f.Besoin||'').replace(/"/g,'')}">${f.Besoin || ''}</div>
          </td>
          <td class="px-6 py-4">
            <span class="px-2 py-1 rounded-md text-xs font-medium ${badge}">${f.Statut || ''}</span>
          </td>
          <td class="px-6 py-4">${actions}</td>
        </tr>`;
    }).join('');
  }

  const JOURS_LABELS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
  const HOURS = [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22];
  let slots = [];
  let editingId = null;

  function showTab(tab) {
    document.getElementById('section-rdv').classList.toggle('hidden', tab !== 'rdv');
    document.getElementById('section-dispo').classList.toggle('hidden', tab !== 'dispo');
    document.getElementById('tab-rdv').className = 'text-sm px-4 py-2 rounded-lg transition ' +
      (tab === 'rdv' ? 'bg-purple-600' : 'bg-gray-800 hover:bg-gray-700');
    document.getElementById('tab-dispo').className = 'text-sm px-4 py-2 rounded-lg transition ' +
      (tab === 'dispo' ? 'bg-purple-600' : 'bg-gray-800 hover:bg-gray-700');
    if (tab === 'dispo') loadAvailability();
  }

  async function loadAvailability() {
    const r = await fetch('/api/availability', { headers: { 'Authorization': 'Bearer ' + token } });
    slots = await r.json();
    renderSlots();
  }

  function renderSlots() {
    const container = document.getElementById('slots-container');
    if (!slots.length) {
      container.innerHTML = '<p class="text-gray-500 text-sm py-4">Aucune plage definie. Cliquez sur "+ Ajouter une plage".</p>';
      return;
    }
    container.innerHTML = slots.map(slot => {
      if (editingId === slot.id) return renderEditForm(slot);
      return renderSlotCard(slot);
    }).join('');
  }

  function renderSlotCard(slot) {
    const chips = JOURS_LABELS
      .filter((_, i) => slot.jours.includes(i))
      .map(j => `<span class="bg-purple-900 text-purple-300 text-xs px-2 py-1 rounded">${j}</span>`)
      .join('');
    return `
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-start justify-between">
        <div>
          <div class="font-semibold mb-2">${slot.label || 'Sans nom'}</div>
          <div class="flex flex-wrap gap-1 mb-2">${chips}</div>
          <div class="text-purple-400 text-sm">${slot.debut}h00 &rarr; ${slot.fin}h00</div>
        </div>
        <div class="flex gap-2 ml-4 shrink-0">
          <button onclick="editSlot('${slot.id}')" class="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded transition">Modifier</button>
          <button onclick="deleteSlot('${slot.id}')" class="text-xs bg-red-900 hover:bg-red-800 px-3 py-1 rounded transition">Supprimer</button>
        </div>
      </div>`;
  }

  function renderEditForm(slot) {
    const dayBoxes = JOURS_LABELS.map((j, i) => `
      <label class="flex items-center gap-1 bg-gray-700 px-3 py-1 rounded-lg cursor-pointer text-sm">
        <input type="checkbox" class="accent-purple-500 eday-${slot.id}" value="${i}" ${slot.jours.includes(i) ? 'checked' : ''}> ${j}
      </label>`).join('');
    const hourOpts = (sel) => HOURS.map(h => `<option value="${h}" ${sel === h ? 'selected' : ''}>${h}h00</option>`).join('');
    return `
      <div class="bg-gray-900 border border-purple-500 rounded-xl p-5">
        <input type="text" id="lbl-${slot.id}" value="${slot.label || ''}" placeholder="Nom de la plage"
          class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 mb-4 focus:outline-none focus:border-purple-500">
        <p class="text-gray-400 text-sm mb-2">Jours</p>
        <div class="flex flex-wrap gap-2 mb-4">${dayBoxes}</div>
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div>
            <p class="text-gray-400 text-sm mb-1">Debut</p>
            <select id="deb-${slot.id}" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2">${hourOpts(slot.debut)}</select>
          </div>
          <div>
            <p class="text-gray-400 text-sm mb-1">Fin</p>
            <select id="fin-${slot.id}" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2">${hourOpts(slot.fin)}</select>
          </div>
        </div>
        <div class="flex gap-2">
          <button onclick="saveSlot('${slot.id}')" class="flex-1 bg-purple-600 hover:bg-purple-500 py-2 rounded-lg text-sm font-medium transition">Enregistrer</button>
          <button onclick="cancelEdit()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition">Annuler</button>
        </div>
      </div>`;
  }

  function addSlot() {
    const id = Date.now().toString();
    slots.push({ id, label: '', jours: [0,1,2,3,4], debut: 9, fin: 17 });
    editingId = id;
    renderSlots();
  }

  function editSlot(id) { editingId = id; renderSlots(); }

  function cancelEdit() {
    slots = slots.filter(s => !(s.id === editingId && s.label === ''));
    editingId = null;
    renderSlots();
  }

  function saveSlot(id) {
    const slot = slots.find(s => s.id === id);
    if (!slot) return;
    slot.label = document.getElementById('lbl-' + id).value || 'Plage';
    slot.jours = Array.from(document.querySelectorAll('.eday-' + id + ':checked')).map(cb => parseInt(cb.value));
    slot.debut = parseInt(document.getElementById('deb-' + id).value);
    slot.fin   = parseInt(document.getElementById('fin-' + id).value);
    if (!slot.jours.length) { alert('Selectionnez au moins un jour.'); return; }
    if (slot.debut >= slot.fin) { alert("L'heure de fin doit etre apres le debut."); return; }
    editingId = null;
    saveAllSlots();
  }

  function deleteSlot(id) {
    if (!confirm('Supprimer cette plage ?')) return;
    slots = slots.filter(s => s.id !== id);
    saveAllSlots();
  }

  async function saveAllSlots() {
    await fetch('/api/availability', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify(slots)
    });
    renderSlots();
  }

  async function updateStatus(id, status) {
    await fetch('/api/appointments/' + id + '/status', {
      method: 'PATCH',
      headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    loadData();
  }
</script>
</body>
</html>"""
