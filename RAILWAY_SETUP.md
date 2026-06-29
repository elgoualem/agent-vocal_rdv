# Configuration Railway - Agent Vocal RDV

## Variables à ajouter dans Railway

Va sur : https://railway.com/project/8787da03-ba86-4caf-bd77-78744368d937/service/0a161fd1-8391-4d93-8834-bdfc179c3fd0/variables

Et ajoute **TOUTES** ces variables :

```bash
# ── SOCIETE ──────────────────────────────────────────
COMPANY_NAME=topup
COMPANY_DESCRIPTION=expert en automatisation et intelligence artificielle
AGENT_FIRST_MESSAGE=Bonjour ! Vous etes sur la ligne de topup. Je suis votre assistante pour la prise de rendez-vous. Comment puis-je vous aider ?

# ── VAPI ────────────────────────────────────────────
VAPI_PRIVATE_KEY=75688645-b7dc-4782-9ae3-32a273ddc94e
VAPI_PUBLIC_KEY=621af185-4bd2-407e-a3de-9f0e23d9a912
VAPI_ASSISTANT_ID=b74867fb-8dd0-4ff5-9d3f-985e2873f8a5

# ── GOOGLE CALENDAR ─────────────────────────────────
GOOGLE_CALENDAR_ID=primary
GOOGLE_TOKEN_JSON=eyJ0b2tlbiI6ICJ5YTI5LmEwQVQzb05aX2JVb1pZa0gtYnJuOFFSQ2t3SF9kbXZqU21jRVkyWl9VbVEtZU90SGdxOUJwZ0VGWmhLSGpmeGcxZG12WGNQV1U0dXF2cU1TMVhZRExQaHBPWmQwbUVPR3J6Ull4dEJEZExOLWNVc3dCS3Z5MXJhZHY5VTBkYlpZaGpmQzh5WEdUaXR1dEVXUVIzN3BEWExIYXZMWVJ1REFsZ1dNczZpQmNLMF9jOEduMGQyRXlDNGk5S29aSEtHOWlQY2pMT0ItajdhQ2dZS0FTOFNBUllTRlFIR1gyTWliTnBSTEJsYnBRcXZ3YlcwN2hYall3MDIwNyIsICJyZWZyZXNoX3Rva2VuIjogIjEvLzA5MEhSYzhXcEZXS3lDZ1lJQVJBQUdBa1NOd0YtTDlJclhJMEduZEJGVTRyaWNkbmJWbWpJRlNzNzI2MGZhTS1IaTF5TWNKcktQeEQ5TXFzb2NFUTlROXBWb3ZUREw0SFV4VlEiLCAidG9rZW5fdXJpIjogImh0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VuIiwgImNsaWVudF9pZCI6ICI3MjczOTExNDkxOTktZnZmYTJtdDl2cmtpdDBvYjIzNDJlNmtldGE5dDFkNWkuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCAiY2xpZW50X3NlY3JldCI6ICJHT0NTUFgteG0wdjBTU1NPOVA4V2VlWjFrVDdnbE9Wc2xxUiIsICJzY29wZXMiOiBbImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL2F1dGgvY2FsZW5kYXIiXSwgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIsICJhY2NvdW50IjogIiIsICJleHBpcnkiOiAiMjAyNi0wNi0yM1QwODo1Njo0NC41NDAyNDVaIn0=

# ── AIRTABLE ────────────────────────────────────────
AIRTABLE_API_KEY=pat****** (copier depuis .env)
AIRTABLE_BASE_ID=app9ARpnvh7J82J3O
AIRTABLE_TABLE_NAME=Rendez-vous

# ── WEBHOOK ─────────────────────────────────────────
WEBHOOK_URL=https://web-production-ca95d.up.railway.app/webhook

# ── DASHBOARD ───────────────────────────────────────
DASHBOARD_PASSWORD=Cpjnjzb3

# ── OPENAI ──────────────────────────────────────────
OPENAI_API_KEY=sk-****** (copier depuis .env)

# ── ELEVENLABS ──────────────────────────────────────
ELEVENLABS_API_KEY=sk_6270ff286354adc9d7e7fa742a22589a1fdd4248cb90318b
```

## Vérification

Une fois les variables ajoutées :

1. Railway va redéployer automatiquement
2. Vérifie les logs : https://railway.com/project/8787da03-ba86-4caf-bd77-78744368d937/service/0a161fd1-8391-4d93-8834-bdfc179c3fd0/deployments

Les logs devraient afficher :
```
INFO:     Uvicorn running on http://0.0.0.0:PORT
INFO:     Application startup complete.
```

3. Teste l'endpoint public :
```bash
curl https://web-production-ca95d.up.railway.app/
```

Devrait retourner :
```json
{"status": "Agent Vocal RDV actif"}
```

## Prochaines étapes

1. ✅ Variables Railway configurées
2. ⏳ Acheter un numéro VAPI sur https://app.vapi.ai
3. ⏳ Assigner le numéro à l'assistant ID : `b74867fb-8dd0-4ff5-9d3f-985e2873f8a5`
4. ⏳ Appeler le numéro pour tester

## Troubleshooting

Si le serveur ne démarre pas :
- Vérifie les logs Railway
- Assure-toi que `GOOGLE_TOKEN_JSON` est bien copié (c'est une longue chaîne)
- Vérifie que toutes les variables sont présentes
