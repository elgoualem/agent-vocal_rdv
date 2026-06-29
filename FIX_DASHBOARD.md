# 🔧 SOLUTION : Dashboard ne s'ouvre pas sur Railway

## 🎯 Problème identifié

Railway n'a **PAS le code à jour**. Les modifications que vous avez faites à `dashboard.py` (notamment l'endpoint `/api/debug-airtable`) ne sont pas déployées.

## ✅ Solution : Pusher le code sur Railway

### Étape 1 : Commit les changements

```bash
git add .
git commit -m "Update dashboard with debug endpoints"
```

### Étape 2 : Push vers Railway

```bash
git push origin main
```

Railway va automatiquement :
1. Détecter le push
2. Redéployer l'application (~1-2 minutes)
3. Utiliser le nouveau code

### Étape 3 : Attendre le redéploiement

1. Va sur : https://railway.com/project/8787da03-ba86-4caf-bd77-78744368d937/service/0a161fd1-8391-4d93-8834-bdfc179c3fd0/deployments
2. Attends que le nouveau déploiement soit "Active" (cercle vert)
3. Vérifie les logs pour confirmer : "Application startup complete"

### Étape 4 : Tester le dashboard

URL : https://web-production-ca95d.up.railway.app/dashboard
Mot de passe : `Cpjnjzb3`

---

## 🔍 Diagnostic supplémentaire

### Si le dashboard affiche "Mot de passe incorrect" :

Teste avec `admin` au lieu de `Cpjnjzb3`. Cela signifie que la variable `DASHBOARD_PASSWORD` n'est pas définie sur Railway.

### Si vous voyez "Chargement..." qui ne finit jamais :

1. Ouvrez la console du navigateur (F12)
2. Regardez l'onglet "Network"
3. Identifiez l'erreur sur `/api/appointments`
4. Si c'est une erreur 500, c'est un problème Airtable

### Pour vérifier Airtable sur Railway :

```bash
# PowerShell
$headers = @{ "Authorization" = "Bearer Cpjnjzb3" }
Invoke-RestMethod -Uri https://web-production-ca95d.up.railway.app/api/debug-airtable -Headers $headers
```

Devrait retourner :
```json
{
  "status": "OK",
  "api_key_prefix": "patHhlbdHDBAmbA...",
  "base_id": "app9ARpnvh7J82J3O",
  "table_name": "Rendez-vous",
  "record_count": X
}
```

---

## 📝 Checklist variables Railway

Vérifiez que TOUTES ces variables sont sur Railway :

- ✅ `COMPANY_NAME=topup`
- ✅ `DASHBOARD_PASSWORD=Cpjnjzb3`
- ✅ `AIRTABLE_API_KEY=patHhlbdHDBAmbA0f...`
- ✅ `AIRTABLE_BASE_ID=app9ARpnvh7J82J3O`
- ✅ `AIRTABLE_TABLE_NAME=Rendez-vous`
- ✅ `GOOGLE_TOKEN_JSON=eyJ0b2tlbiI6...`
- ✅ `VAPI_ASSISTANT_ID=b74867fb-8dd0-4ff5-9d3f-985e2873f8a5`
- ✅ `WEBHOOK_URL=https://web-production-ca95d.up.railway.app/webhook`

---

## 🚀 Après le fix

Le dashboard devrait afficher :
- 📊 Statistiques des RDV
- 📋 Liste des rendez-vous
- ⚙️ Section Disponibilités
- ✅ Actions (Terminé, Annuler)
