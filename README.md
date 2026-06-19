# Agent Vocal RDV — MechaPizzAI

Agent vocal IA qui répond aux appels téléphoniques, comprend le besoin du client et réserve automatiquement un créneau dans Google Calendar.

**Stack :** VAPI · GPT-4o · Google Calendar · Airtable · FastAPI · Railway

---

## Ce que fait l'agent

1. Répond à l'appel en français
2. Demande le prénom, nom et email du client
3. Pose 2 questions pour comprendre le besoin
4. Consulte ton Google Calendar pour trouver les créneaux libres
5. Laisse le client choisir, puis confirme le RDV
6. Crée l'événement dans Google Calendar + envoie l'invitation par email
7. Enregistre le contact dans Airtable

---

## Comptes à créer (tous gratuits ou freemium)

| Service | Lien | Pourquoi |
|---|---|---|
| VAPI | https://vapi.ai | Agent vocal + numéro de téléphone |
| OpenAI | https://platform.openai.com | GPT-4o pour le cerveau de l'agent |
| Google Cloud | https://console.cloud.google.com | Accès à Google Calendar |
| Airtable | https://airtable.com | Stocker les RDV |
| Railway | https://railway.app | Héberger le serveur |

---

## Installation

### 1. Cloner le projet

```bash
git clone https://github.com/ton-user/agent-vocal-rdv.git
cd agent-vocal-rdv
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Copier le fichier d'environnement

```bash
cp .env.example .env
```

---

## Configuration

### VAPI

1. Crée un compte sur [vapi.ai](https://vapi.ai)
2. Va dans **Settings → API Keys**
3. Copie la **Private Key** et la **Public Key**
4. Ajoute dans `.env` :

```
VAPI_PRIVATE_KEY=ta_cle_privee
VAPI_PUBLIC_KEY=ta_cle_publique
```

---

### OpenAI

1. Va sur [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Crée une nouvelle clé API
3. Ajoute dans `.env` :

```
OPENAI_API_KEY=sk-...
```

---

### Airtable

1. Crée un compte sur [airtable.com](https://airtable.com)
2. Crée une nouvelle **Base** avec une table nommée **Rendez-vous**
3. Ajoute ces colonnes dans la table :

| Nom du champ | Type |
|---|---|
| Prénom | Single line text |
| Nom | Single line text |
| Email | Email |
| Date RDV | Single line text |
| Besoin | Long text |
| Statut | Single select (Confirmé / Annulé / Terminé) |
| Créé le | Single line text |
| Call ID | Single line text |

4. Crée un **Personal Access Token** sur [airtable.com/create/tokens](https://airtable.com/create/tokens)
   - Scopes requis : `schema.bases:read` · `schema.bases:write` · `data.records:write`
5. Récupère le **Base ID** : ouvre ta base → **Help → API documentation** → l'ID commence par `app...`
6. Ajoute dans `.env` :

```
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=app...
AIRTABLE_TABLE_NAME=Rendez-vous
```

---

### Google Calendar

#### Étape 1 — Créer un projet Google Cloud

1. Va sur [console.cloud.google.com](https://console.cloud.google.com)
2. Clique sur **Select a project → New Project**
3. Donne un nom (ex : `Agent Vocal RDV`) et valide

#### Étape 2 — Activer l'API Calendar

1. Dans le menu : **APIs & Services → Library**
2. Recherche **Google Calendar API** → clique dessus → **Enable**

#### Étape 3 — Créer les credentials OAuth

1. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
2. Si demandé, configure le **OAuth Consent Screen** :
   - User Type : **External**
   - App name : ce que tu veux
   - Support email : ton email
   - Sauvegarde (les autres champs ne sont pas obligatoires)
3. Retourne sur **Credentials → Create → OAuth 2.0 Client ID**
   - Application type : **Desktop app**
   - Clique **Create**
4. Clique **Download JSON** → renomme le fichier en `credentials.json` → place-le dans le dossier du projet

#### Étape 4 — Ajouter ton email comme testeur

1. **APIs & Services → OAuth consent screen → Test users**
2. Clique **+ Add Users** → entre ton email Google
3. Sauvegarde

#### Étape 5 — Lancer l'authentification

```bash
python -c "from calendar_service import get_service; get_service()"
```

Un navigateur s'ouvre → connecte-toi avec ton compte Google → clique **Continuer** (l'avertissement "Google n'a pas validé" est normal en mode test) → autorise.

Un fichier `token.json` est créé dans le dossier.

#### Étape 6 — Encoder le token pour Railway

```bash
python encode_token.py
```

Copie la valeur `GOOGLE_TOKEN_JSON=...` affichée — tu en auras besoin dans les variables Railway.

Ajoute également dans `.env` :

```
GOOGLE_CALENDAR_ID=primary
```

> Pour utiliser un calendrier spécifique (pas le principal), remplace `primary` par l'ID du calendrier (visible dans Google Calendar → Settings du calendrier).

---

## Déploiement sur Railway

### Étape 1 — Pousser le code sur GitHub

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/ton-user/agent-vocal-rdv.git
git push -u origin main
```

> `.env`, `token.json` et `credentials.json` sont dans `.gitignore` — ils ne seront pas poussés.

### Étape 2 — Créer le projet Railway

1. Va sur [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Sélectionne ton repo
3. Railway détecte automatiquement le `Procfile`

### Étape 3 — Ajouter les variables d'environnement

Dans Railway → ton projet → **Variables**, ajoute toutes les variables de ton `.env` :

```
VAPI_PRIVATE_KEY
VAPI_PUBLIC_KEY
OPENAI_API_KEY
AIRTABLE_API_KEY
AIRTABLE_BASE_ID
AIRTABLE_TABLE_NAME
GOOGLE_CALENDAR_ID
GOOGLE_TOKEN_JSON      ← la valeur obtenue avec encode_token.py
WEBHOOK_URL            ← à remplir à l'étape suivante
```

### Étape 4 — Récupérer l'URL Railway

Dans Railway → ton projet → **Settings → Domains → Generate Domain**

Ton URL ressemble à : `https://ton-app.up.railway.app`

Ajoute dans Railway Variables :

```
WEBHOOK_URL=https://ton-app.up.railway.app/webhook
```

Fais pareil dans ton `.env` local.

---

## Création de l'assistant VAPI

Une fois Railway déployé et `WEBHOOK_URL` rempli :

```bash
python setup_vapi.py
```

Ce script :
- Crée l'assistant VAPI avec le bon prompt et les bons outils
- Achète un numéro de téléphone et l'assigne à l'assistant
- Affiche l'`ASSISTANT_ID` à ajouter dans Railway Variables

Ajoute ensuite dans Railway Variables :

```
VAPI_ASSISTANT_ID=l_id_affiche
```

Railway redéploie automatiquement.

---

## Test

1. Appelle le numéro affiché par `setup_vapi.py`
2. L'agent répond, prend tes infos et propose des créneaux
3. Vérifie dans Google Calendar que le RDV est créé
4. Vérifie dans Airtable que le contact est enregistré

---

## Développement local

Pour tester en local (sans Railway) :

```bash
python launch.py
```

Le serveur démarre sur `http://localhost:8000`.

Pour que VAPI puisse atteindre ton serveur local, utilise un tunnel :
- [ngrok](https://ngrok.com) : `ngrok http 8000` (compte gratuit requis)
- [localtunnel](https://localtunnel.github.io/www/) : `npx localtunnel --port 8000`

Met à jour `WEBHOOK_URL` dans `.env` avec l'URL du tunnel, puis relance `python setup_vapi.py`.

---

## Structure du projet

```
agent-vocal-rdv/
├── main.py                  # Serveur FastAPI — reçoit les webhooks VAPI
├── calendar_service.py      # Google Calendar — créneaux + réservation
├── airtable_service.py      # Airtable — sauvegarde des contacts
├── setup_vapi.py            # Crée l'assistant VAPI (à lancer une fois)
├── encode_token.py          # Encode token.json pour Railway
├── launch.py                # Démarrage local
├── requirements.txt
├── Procfile                 # Démarrage Railway
├── .env.example             # Template des variables
└── .gitignore
```

---

## Variables d'environnement — récapitulatif

| Variable | Description |
|---|---|
| `VAPI_PRIVATE_KEY` | Clé privée VAPI (Settings → API Keys) |
| `VAPI_PUBLIC_KEY` | Clé publique VAPI |
| `VAPI_ASSISTANT_ID` | ID de l'assistant (après setup_vapi.py) |
| `OPENAI_API_KEY` | Clé API OpenAI |
| `AIRTABLE_API_KEY` | Personal Access Token Airtable |
| `AIRTABLE_BASE_ID` | ID de la base Airtable (commence par `app`) |
| `AIRTABLE_TABLE_NAME` | Nom de la table (ex : `Rendez-vous`) |
| `GOOGLE_CALENDAR_ID` | `primary` ou ID du calendrier |
| `GOOGLE_TOKEN_JSON` | Token Google encodé en base64 (encode_token.py) |
| `WEBHOOK_URL` | URL publique + `/webhook` (ex : Railway) |
