# 🚀 Guide d'installation — Agent Vocal RDV (Version Skool)

Bienvenue ! Ce guide te permet d'installer, configurer et déployer ton agent vocal en moins d'une heure. Toutes les étapes sont dans l'ordre — suis-les dans la séquence indiquée.

---

## Prérequis — Comptes à créer

Crée ces comptes avant de commencer. Tous ont une version gratuite ou trial suffisante pour démarrer.

| Service | URL | Action |
|---|---|---|
| VAPI | vapi.ai | Créer un compte → récupérer Private Key + Public Key |
| OpenAI | platform.openai.com | Créer une clé API |
| ElevenLabs | elevenlabs.io | Créer un compte → récupérer la clé API |
| Google Cloud | console.cloud.google.com | Créer un projet (voir Étape 3) |
| Airtable | airtable.com | Créer un compte → créer une base vide |
| Railway | railway.app | Créer un compte (connexion via GitHub recommandée) |
| GitHub | github.com | Créer un compte (pour Railway) |

---

## Étape 1 — Installation Python

Vérifie que Python 3.10+ est installé :
```bash
python --version
```

Dézippe le projet et installe les dépendances :
```bash
cd agent-vocal-rdv
pip install -r requirements.txt
```

---

## Étape 2 — Configurer le fichier .env

Copie le fichier template :
```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Ouvre `.env` et remplis les variables au fur et à mesure des étapes suivantes.

**Variables de personnalisation (à remplir maintenant) :**
```
COMPANY_NAME=Nom de ta société
COMPANY_DESCRIPTION=description de ton activité en une phrase
AGENT_FIRST_MESSAGE=Bonjour ! Vous êtes sur la ligne de [Ta Société]. Comment puis-je vous aider ?
DASHBOARD_PASSWORD=choisis_un_mot_de_passe_solide
GOOGLE_CALENDAR_ID=primary
AIRTABLE_TABLE_NAME=Rendez-vous
```

---

## Étape 3 — Google Calendar

### 3.1 — Créer les credentials Google Cloud

1. Va sur [console.cloud.google.com](https://console.cloud.google.com)
2. **Select a project → New Project** → donne un nom → Create
3. Menu : **APIs & Services → Library** → recherche `Google Calendar API` → Enable
4. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Si demandé, configure le **OAuth Consent Screen** :
   - User Type : **External**
   - App name : ce que tu veux
   - Support email : ton email
   - Sauvegarde (les autres champs sont optionnels)
6. Retourne sur **Credentials → Create → OAuth 2.0 Client ID**
   - Application type : **Desktop app** → Create
7. Clique **Download JSON** → renomme en `credentials.json` → place dans le dossier du projet

### 3.2 — Ajouter ton email comme testeur

1. **APIs & Services → OAuth consent screen → Test users**
2. **+ Add Users** → entre ton adresse email Google → Save

### 3.3 — Lancer l'authentification

```bash
python -c "from calendar_service import get_service; get_service()"
```

Un navigateur s'ouvre → connecte-toi → clique **Continuer** (l'avertissement "Google n'a pas validé" est normal en mode test) → **Autoriser**.

Le fichier `token.json` est créé dans le dossier.

### 3.4 — Encoder le token pour Railway

```bash
python encode_token.py
```

**Copie** la valeur `GOOGLE_TOKEN_JSON=eyJ...` — tu en auras besoin à l'Étape 6.

Tu dois aussi encoder `credentials.json` :
```bash
python -c "import base64; print('GOOGLE_CREDENTIALS_JSON=' + base64.b64encode(open('credentials.json','rb').read()).decode())"
```

Copie aussi cette valeur.

---

## Étape 4 — Airtable

### 4.1 — Créer le token Airtable

1. Va sur [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. **Create new token** → donne un nom
3. Ajoute ces scopes :
   - `schema.bases:read`
   - `schema.bases:write`
   - `data.records:read`
   - `data.records:write`
4. Access : sélectionne ta base → Create token
5. **Copie le token** (commence par `pat...`) → ajoute dans `.env` :
   ```
   AIRTABLE_API_KEY=pat...
   ```

### 4.2 — Récupérer le Base ID

1. Ouvre ta base Airtable dans le navigateur
2. L'URL ressemble à : `https://airtable.com/appXXXXXXXX/...`
3. Copie la partie `appXXXXXXXX` → ajoute dans `.env` :
   ```
   AIRTABLE_BASE_ID=appXXXXXXXX
   ```

### 4.3 — Créer les tables automatiquement

```bash
python setup_airtable.py
```

Ce script crée automatiquement :
- La table **Rendez-vous** avec tous les champs nécessaires
- La table **Config** avec les plages de disponibilité par défaut (Lun-Ven, 9h-17h)
- Lance un test d'écriture pour valider l'accès

---

## Étape 5 — Pousser sur GitHub et déployer sur Railway

### 5.1 — Créer un repo GitHub

1. Va sur [github.com/new](https://github.com/new)
2. Nom : `agent-vocal-rdv` → **Private** → Create
3. Dans le dossier du projet :
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/ton-user/agent-vocal-rdv.git
   git push -u origin main
   ```

> ⚠️ `.env`, `token.json` et `credentials.json` sont dans `.gitignore` — ils ne seront jamais poussés.

### 5.2 — Créer le projet Railway

1. Va sur [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Sélectionne ton repo `agent-vocal-rdv`
3. Railway détecte le `Procfile` et commence le déploiement

### 5.3 — Ajouter les variables d'environnement

Dans Railway → ton service → **Variables**, ajoute :

```
COMPANY_NAME
COMPANY_DESCRIPTION
AGENT_FIRST_MESSAGE
DASHBOARD_PASSWORD
VAPI_PRIVATE_KEY
VAPI_PUBLIC_KEY
OPENAI_API_KEY
ELEVENLABS_API_KEY
AIRTABLE_API_KEY
AIRTABLE_BASE_ID
AIRTABLE_TABLE_NAME
GOOGLE_CALENDAR_ID
GOOGLE_TOKEN_JSON          ← valeur obtenue à l'Étape 3.4
GOOGLE_CREDENTIALS_JSON    ← valeur obtenue à l'Étape 3.4
```

### 5.4 — Récupérer l'URL Railway

1. Railway → ton service → **Settings → Networking → Generate Domain**
2. Ton URL ressemble à `https://ton-app.up.railway.app`
3. Ajoute dans Railway Variables :
   ```
   WEBHOOK_URL=https://ton-app.up.railway.app/webhook
   ```
4. Railway redéploie automatiquement

### 5.5 — Vérifier que le serveur fonctionne

Ouvre dans ton navigateur :
```
https://ton-app.up.railway.app/
```
Tu dois voir : `{"status": "Agent Vocal RDV actif"}`

Teste le calendrier :
```
https://ton-app.up.railway.app/debug/calendar
```
Tu dois voir : `{"ok": true, "slots": N, ...}`

---

## Étape 6 — Créer l'assistant VAPI

Assure-toi que `WEBHOOK_URL` est bien dans ton `.env` local, puis lance :

```bash
python setup_vapi.py
```

Ce script :
- Crée l'assistant VAPI avec ton nom de société et ton prompt
- Configure la voix ElevenLabs (multilingue)
- Configure Deepgram en français
- Affiche l'`ASSISTANT_ID` à copier

Ajoute dans Railway Variables :
```
VAPI_ASSISTANT_ID=l-id-affiché
```

---

## Étape 7 — Acheter un numéro de téléphone

1. Va sur [app.vapi.ai](https://app.vapi.ai) → **Phone Numbers → Create Phone Number**
2. Choisis **Free Vapi Number**
3. Entre un area code US (ex: `415`, `212`, `646`)
4. Scroll vers le bas → section **Assistant** → sélectionne **"Agent RDV - Ta Société"**
5. Sauvegarde

> Pour un numéro français (+33), utilise **Import Telnyx** avec un numéro acheté sur telnyx.com (~1€/mois).

---

## Étape 8 — Accéder au dashboard

Ouvre dans ton navigateur :
```
https://ton-app.up.railway.app/dashboard
```

Entre le `DASHBOARD_PASSWORD` que tu as défini → tu accèdes au dashboard.

**Première chose à faire dans le dashboard :**
1. Clique sur l'onglet **Disponibilités**
2. Modifie les jours et horaires disponibles selon ton agenda
3. Tu peux créer plusieurs plages (ex: Lun-Ven 9h-17h + Sam 10h-12h)

---

## Étape 9 — Premier test

1. Appelle ton numéro VAPI depuis ton téléphone
2. L'agent répond avec ton message de bienvenue personnalisé
3. Donne ton prénom, nom et email
4. L'agent te propose des créneaux
5. Confirme un créneau
6. Vérifie dans Google Calendar que l'événement est créé
7. Vérifie dans Airtable qu'un enregistrement est apparu
8. Vérifie dans le dashboard que le RDV est visible

---

## Récapitulatif des URLs importantes

| URL | Description |
|---|---|
| `https://ton-app.up.railway.app/` | Status du serveur |
| `https://ton-app.up.railway.app/dashboard` | Dashboard RDV |
| `https://ton-app.up.railway.app/debug/calendar` | Test Google Calendar |
| `https://ton-app.up.railway.app/webhook` | Webhook VAPI (ne pas ouvrir directement) |

---

## Résolution des problèmes fréquents

### Le calendrier ne fonctionne pas sur Railway
→ Vérifie que `GOOGLE_TOKEN_JSON` ET `GOOGLE_CREDENTIALS_JSON` sont bien définis dans Railway Variables.

### L'agent ne répond pas
→ Vérifie que le numéro est bien assigné à l'assistant dans le dashboard VAPI.
→ Vérifie que `WEBHOOK_URL` pointe vers ton URL Railway.

### Airtable refus d'écriture
→ Vérifie les scopes du token (doivent inclure `data.records:write`).

### Le token Railway expire (après 30 jours)
→ Relance `python encode_token.py` en local et mets à jour `GOOGLE_TOKEN_JSON` dans Railway.

---

## Personnalisation avancée

**Changer la voix :** Modifie `voiceId` dans `setup_vapi.py`, puis relance le script.

**Modifier le prompt :** Modifie `SYSTEM_PROMPT` dans `setup_vapi.py`, puis relance le script.

**Changer la durée des RDV :** Modifie `SLOT_DURATION_H` dans `calendar_service.py`.

**Changer le modèle LLM :** Modifie `"model": "gpt-4o"` dans `setup_vapi.py` (ex: `gpt-4o-mini` pour réduire les coûts).

---

## Renouvellement mensuel

Le watch Google Calendar expire après 29 jours. Il se renouvelle automatiquement à chaque redéploiement Railway. Pour forcer un renouvellement sans redéployer, redémarre le service depuis Railway.

---

👉 [Communauté MechaPizzAI sur Skool](https://www.skool.com/mechapizzai/about)
