# -*- coding: utf-8 -*-
"""
Serveur local pour le developpement.
En production, Railway utilise le Procfile : uvicorn main:app --host 0.0.0.0 --port $PORT

Usage local :
    python launch.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
