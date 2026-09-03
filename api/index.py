import io
import os
import ssl
import urllib.request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import pandas as pd

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
    # 1. Intento de descarga remota desde GitHub Raw
    repo = os.environ.get("VERCEL_GIT_REPO_SLUG", REPO_GITHUB)
    url_remota = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{repo}/main/{nombre_archivo}"

    try:
        req = urllib.request.Request(
            url_remota, headers={"User-Agent": "Mozilla/5.0"}
        )
        # Contexto SSL sin verificación estricta para evitar certificados fallidos en serverless
        ssl_context = ssl._create_unverified_context()

        with urllib.request.urlopen(
            req, timeout=10, context=ssl_context
        ) as response:
            df = pd.read_csv(response, encoding="utf-8-sig")
            if not df.empty:
                # Reemplazar NaN por None/string vacío para evitar error 500 en JSON
                return df.where(pd.notnull(df), None)
    except Exception as e:
        print(f"Error al obtener {url_remota} desde GitHub: {e}")

    # 2. Fallback a archivos locales
    rutas_locales = [
        nombre_archivo,
        os.path.join("..", nombre_archivo),
        os.path.join(os.path.dirname(__file__), "..", nombre_archivo),
    ]
    for ruta in rutas_locales:
        if os.path.exists(ruta):
            try:
                df = pd.read_csv(ruta, encoding="utf-8-sig")
                if not df.empty:
                    return df.where(pd.notnull(df), None)
            except Exception:
                pass

    return None


@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Canasta Básica Alimentaria</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 text-gray-800 p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <header class="flex justify-between items-center border-b pb-4">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">Canasta Básica Alimentaria</h1>
                    <p class="text-sm text-gray-500">Estimación vía Web Scraping</p>
                </div>
                <a href="/docs" target="_blank" class="text-sm bg-gray-200 hover:bg-gray-300 px-3 py-2 rounded font-medium text-gray-700">Documentación API</a>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Costo Adulto Equivalente (AE)</p>
                    <p class="text-3xl font-extrabold text-emerald-600 mt-2" id="costo-ae">Cargando...</p>
                </div>
                <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Costo Hogar Tipo (3.09 AE)</p>
                    <p class="text-3xl font-extrabold text-blue-600 mt-2" id="costo-hogar">Cargando...</p>
                </div>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div class="p-4 border-b bg-gray-50">
                    <h2 class="font-bold text-gray-700">Detalle por Rubro</h2>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-100 text-gray-600 border-b">
                            <tr>
                                <th class="p-3">Rubro</th>
                                <th class="p-3">Muestras</th>
                                <th class="p-3">Precio Estimado</th>
                                <th class="p-3">Costo Mensual AE</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-detalle" class="divide-y divide-gray-200">
                            <tr><td colspan="4" class="p-4 text-center text-gray-400">Cargando datos...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            async function fetchJSON(url) {
                try {
                    let res = await fetch(url);
                    if (!res.ok && url.startsWith('/api/')) {
                        res = await fetch(url.replace('/api/', '/'));
                    }
                    if (!res.ok) return [];
                    return await res.json();
                } catch (e) {
                    console.error("Error cargando JSON:", e);
                    return [];
                }
            }

            async function cargarDatos() {
                const totales = await fetchJSON('/api/totales');
                if (Array.isArray(totales) && totales.length > 0) {
                    const ultimo = totales[totales.length - 1];
                    document.getElementById('costo-ae').innerText = `$ ${Number(ultimo.costo_total_ae || 0).toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                    document.getElementById('costo-hogar').innerText = `$ ${Number(ultimo.costo_total_hogar || 0).toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                } else {
                    document.getElementById('costo-ae').innerText = 'Sin datos';
                    document.getElementById('costo-hogar').innerText = 'Sin datos';
                }

                const detalle = await fetchJSON('/api/detalle');
                const tbody = document.getElementById('tabla-detalle');
                tbody.innerHTML = '';
                
                if (Array.isArray(detalle) && detalle.length > 0) {
                    const fechaReciente = detalle[detalle.length - 1]?.fecha;
                    const filtrados = detalle.filter(d => d.fecha === fechaReciente);

                    filtrados.forEach(item => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td class="p-3 font-medium text-gray-900">${item.rubro}</td>
                            <td class="p-3 text-gray-500">${item.coincidencias || 0}</td>
                            <td class="p-3">$ ${Number(item.precio_unitario_estimado || 0).toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
                            <td class="p-3 font-semibold text-gray-800">$ ${Number(item.costo_mensual_ae || 0).toLocaleString('es-AR', {minimumFractionDigits: 2})}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-gray-500">No se pudieron cargar los datos desde GitHub.</td></tr>';
                }
            }
            cargarDatos();
        </script>
    </body>
    </html>
    """


@app.get("/totales")
@app.get("/api/totales")
def get_totales():
    df = leer_csv("cba_historico_totales.csv")
    return df.to_dict(orient="records") if df is not None else []


@app.get("/detalle")
@app.get("/api/detalle")
def get_detalle():
    df = leer_csv("cba_historico_detalle.csv")
    return df.to_dict(orient="records") if df is not None else []


@app.get("/nutricional")
@app.get("/api/nutricional")
def get_nutricional():
    df = leer_csv("cba_tabla_nutricional.csv")
    return df.to_dict(orient="records") if df is not None else []
