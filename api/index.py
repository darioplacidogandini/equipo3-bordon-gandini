from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="CBA Scraper API")

# Habilitar CORS para permitir llamadas desde cualquier frontend (React, Vue, HTML, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "API de Canasta Básica Alimentaria",
        "endpoints": [
            "/api/totales",
            "/api/detalle",
            "/api/nutricional"
        ]
    }

@app.get("/api/totales")
def get_totales():
    file_path = "cba_historico_totales.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    return {"error": "Archivo cba_historico_totales.csv no encontrado"}

@app.get("/api/detalle")
def get_detalle():
    file_path = "cba_historico_detalle.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    return {"error": "Archivo cba_historico_detalle.csv no encontrado"}

@app.get("/api/nutricional")
def get_nutricional():
    file_path = "cba_tabla_nutricional.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    return {"error": "Archivo cba_tabla_nutricional.csv no encontrado"}
