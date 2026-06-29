# 🔴 PROBLÈME DASHBOARD RAILWAY

## Diagnostic

- ✅ Serveur Railway actif
- ✅ Endpoint `/debug/calendar` fonctionne  
- ✅ Endpoint `/api/availability` fonctionne avec mot de passe
- ❌ Endpoint `/api/appointments` → Erreur 500

## Cause probable

Le **token Airtable sur Railway n'a pas accès à la base** "agent vocal rdv".

## Solution

### Étape 1 : Vérifier le token Airtable sur Railway

Va sur : https://railway.com/project/8787da03-ba86-4caf-bd77-78744368d937/service/0a161fd1-8391-4d93-8834-bdfc179c3fd0/variables

**Cherche la variable :**
```
AIRTABLE_API_KEY
```

### Étape 2 : Vérifier que c'est le BON token

Le token doit commencer par `pat` et doit être **le même que celui qui fonctionne en local**.

**Token en local (qui fonctionne) :**
```
AIRTABLE_API_KEY=pat****** (voir fichier .env local)
```

### Étape 3 : Si le token est différent

1. **Supprime** l'ancienne variable `AIRTABLE_API_KEY` sur Railway
2. **Ajoute** la nouvelle avec la valeur ci-dessus
3. Railway va redéployer automatiquement (attendre ~30 secondes)

### Étape 4 : Re-tester

Une fois le token mis à jour, teste à nouveau :

```bash
# Dans PowerShell
$headers = @{ "Authorization" = "Bearer Cpjnjzb3" }
Invoke-RestMethod -Uri https://web-production-ca95d.up.railway.app/api/appointments -Headers $headers
```

Devrait retourner la liste des RDV au lieu d'une erreur 500.

## Alternative : Créer un nouveau token Airtable

Si le token actuel ne fonctionne pas, crée un nouveau token sur https://airtable.com/create/tokens avec :

**Scopes requis :**
- ✅ `data.records:read`
- ✅ `data.records:write`  
- ✅ `schema.bases:read`
- ✅ `schema.bases:write`

**IMPORTANT :** Dans la section "Access", clique sur "Add a base" et sélectionne **"agent vocal rdv"**

Puis copie ce nouveau token dans Railway.

## Test en local

Le dashboard local fonctionne parfaitement :
- URL : http://localhost:8000/dashboard
- Mot de passe : `Cpjnjzb3`

Utilise-le en attendant que Railway soit fixé.
