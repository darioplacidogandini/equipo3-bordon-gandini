from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="CBA Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Página principal: Dashboard Visual HTML
@app.get("/", response_class=HTMLResponse)
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

            <!-- Tarjetas de Resumen -->
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

            <!-- Tabla de Detalle -->
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
            async function cargarDatos() {
                try {
                    // Cargar Totales
                    const resTotales = await fetch('/api/totales');
                    const totales = await resTotales.json();
                    if (totales.length > 0) {
                        const ultimo = totales[totales.length - 1];
                        document.getElementById('costo-ae').innerText = `$ ${Number(ultimo.costo_total_ae).toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
                        document.getElementById('costo-hogar').innerText = `$ ${Number(ultimo.costo_total_hogar).toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
                    }

                    // Cargar Detalle
                    const resDetalle = await fetch('/api/detalle');
                    const detalle = await resDetalle.json();
                    const tbody = document.getElementById('tabla-detalle');
                    tbody.innerHTML = '';
                    
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
                } catch (e) {
                    console.error('Error:', e);
                }
            }
            cargarDatos();
        </script>
    </body>
    </html>
    """

# 2. Endpoints de datos JSON en segundo plano
@app.get("/api/totales")
def get_totales():
    file_path = "cba_historico_totales.csv"
    if os.path.exists(file_path):
        return pd.read_csv(file_path).to_dict(orient="records")
    return []

@app.get("/api/detalle")
def get_detalle():
    file_path = "cba_historico_detalle.csv"
    if os.path.exists(file_path):
        return pd.read_csv(file_path).to_dict(orient="records")
    return []

@app.get("/api/nutricional")
def get_nutricional():
    file_path = "cba_tabla_nutricional.csv"
    if os.path.exists(file_path):
        return pd.read_csv(file_path).to_dict(orient="records")
    return []
