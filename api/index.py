from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import io
import urllib.request

app = FastAPI(title="CBA Scraper API")

USUARIO_GITHUB = "darioplacidogandini"
REPO_GITHUB = "equipo3-bordon-gandini"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def leer_csv(nombre_archivo):
    # 1. Intentar lectura local
    rutas_locales = [
        nombre_archivo,
        os.path.join("..", nombre_archivo),
        os.path.join(os.path.dirname(__file__), "..", nombre_archivo)
    ]
    for ruta in rutas_locales:
        if os.path.exists(ruta):
            try:
                return pd.read_csv(ruta)
            except Exception:
                pass

    # 2. Descargar desde GitHub Raw con User-Agent para evitar el bloqueo 403
    repo = os.environ.get("VERCEL_GIT_REPO_SLUG", REPO_GITHUB)
    url_remota = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{repo}/main/{nombre_archivo}"

    try:
        req = urllib.request.Request(
            url_remota, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            contenido = response.read().decode('utf-8')
            return pd.read_csv(io.StringIO(contenido))
    except Exception as e:
        print(f"Error cargando {url_remota}: {e}")
        return None
