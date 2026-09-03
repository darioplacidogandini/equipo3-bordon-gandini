from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="CBA Scraper API")

# 🔴 REEMPLAZA ESTO CON EL NOMBRE EXACTO DE TU REPOSITTORIO EN GITHUB
USUARIO_GITHUB = "darioplacidogandini"
REPO_GITHUB = "equipo3-bordon-gandini"  # Ejemplo: "cba-scraper"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def leer_csv(nombre_archivo):
    # 1. Intentar en el entorno local
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

    # 2. Leer directamente desde GitHub Raw
    repo = os.environ.get("VERCEL_GIT_REPO_SLUG", REPO_GITHUB)
    url_remota = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{repo}/main/{nombre_archivo}"

    try:
        return pd.read_csv(url_remota)
    except Exception as e:
        print(f"Error cargando {url_remota}: {e}")
        return None
