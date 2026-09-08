from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import io
import ssl
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
    repo_env = os.environ.get("VERCEL_GIT_REPO_SLUG")
    repo = repo_env if repo_env else REPO_GITHUB
    url_remota = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{repo}/main/{nombre_archivo}"
    
    # 1. Intentar descargar desde GitHub Raw con SSL no verificado
    try:
        req = urllib.request.Request(
            url_remota, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            contenido = response.read().decode('utf-8-sig')
            df = pd.read_csv(io.StringIO(contenido))
            if not df.empty:
                return df.fillna("")
    except Exception as e:
        print(f"Error descargando {url_remota}: {e}")

    # 2. Fallback local
    rutas_locales = [
        nombre_archivo,
        os.path.join("..", nombre_archivo),
        os.path.join(os.path.dirname(__file__), "..", nombre_archivo)
    ]
    for ruta in rutas_locales:
        if os.path.exists(ruta):
            try:
                df = pd.read_csv(ruta, encoding='utf-8-sig')
                if not df.empty:
                    return df.fillna("")
            except Exception as e:
                print(f"Error leyendo archivo local {ruta}: {e}")

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
        <!-- Tailwind CSS -->
        <script src="https://cdn.tailwindcss.com"></script>
        <!-- Chart.js -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-100 text-gray-800 p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <header class="flex justify-between items-center border-b pb-4">
                <div>
                    <h1 class="text-2xl font-bold text-gray-900">Canasta Básica Alimentaria</h1>
                    <p class="text-sm text-gray-500">Estimación vía Web Scraping</p>
                </div>
                <a href="/docs" target="_blank" class="text-sm bg-gray-200 hover:bg-gray-300 px-3 py-2 rounded font-medium text-gray-700">Documentación API</a>
            </header>

            <!-- Cards KPI de Totales Actuales -->
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

            <!-- Navegación por Pestañas (Tabs) -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div class="border-b bg-gray-50 flex space-x-2 px-4 pt-2 overflow-x-auto">
                    <button id="btn-tab-grafico" onclick="seleccionarTab('grafico')" class="py-3 px-4 text-sm font-semibold border-b-2 border-blue-600 text-blue-600 focus:outline-none whitespace-nowrap">
                        Gráfico por Categoría
                    </button>
                    <button id="btn-tab-detalle" onclick="seleccionarTab('detalle')" class="py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-gray-500 hover:text-gray-700 focus:outline-none whitespace-nowrap">
                        Detalle por Producto
                    </button>
                    <button id="btn-tab-nutricional" onclick="seleccionarTab('nutricional')" class="py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-gray-500 hover:text-gray-700 focus:outline-none whitespace-nowrap">
                        Tabla Nutricional
                    </button>
                    <button id="btn-tab-totales" onclick="seleccionarTab('totales')" class="py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-gray-500 hover:text-gray-700 focus:outline-none whitespace-nowrap">
                        Histórico de Totales
                    </button>
                </div>

                <!-- Tab 1: Pestaña dedicada al Gráfico Interactivo -->
                <div id="tab-grafico" class="tab-contenido p-6 space-y-6">
                    <div class="bg-gray-50 p-6 rounded-xl border border-gray-200 flex flex-col md:flex-row items-center justify-around gap-6">
                        <div class="w-full md:w-1/2 max-w-md">
                            <h3 class="text-center font-bold text-gray-700 mb-4 text-sm uppercase tracking-wider">Distribución de Costo por Categoría</h3>
                            <canvas id="chart-categorias" class="max-h-72"></canvas>
                        </div>
                        <div class="w-full md:w-1/2 text-sm text-gray-600 space-y-4">
                            <div class="bg-white p-4 rounded-lg border border-gray-200 space-y-2">
                                <p class="font-bold text-gray-800 flex items-center gap-2">
                                    <span>💡</span> Gráfico Interactivo
                                </p>
                                <p class="text-xs text-gray-500 leading-relaxed">
                                    Haz clic en cualquier porción de la torta para filtrar la tabla inferior y ver únicamente los productos asociados a esa categoría.
                                </p>
                            </div>

                            <!-- Indicator de Filtro Activo -->
                            <div id="badge-filtro" class="hidden items-center justify-between bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg font-medium">
                                <span class="text-xs">Mostrando categoría: <strong id="cat-filtrada-nombre" class="text-sm font-bold text-blue-900"></strong></span>
                                <button onclick="limpiarFiltroCategoriaGrafico()" class="text-xs bg-blue-600 hover:bg-blue-700 text-white font-semibold px-2.5 py-1 rounded transition-colors">
                                    Ver Todas ✖
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Tabla filtrada asociada al gráfico -->
                    <div class="overflow-x-auto">
                        <h4 class="font-bold text-gray-700 mb-3 text-sm">Productos de la Selección</h4>
                        <table class="w-full text-left text-sm border-collapse">
                            <thead class="bg-gray-100 text-gray-600 border-b">
                                <tr>
                                    <th class="p-3">Categoría / Rubro</th>
                                    <th class="p-3">Producto</th>
                                    <th class="p-3">Muestras</th>
                                    <th class="p-3">Precio Estimado</th>
                                    <th class="p-3">Costo Mensual AE</th>
                                </tr>
                            </thead>
                            <tbody id="tabla-grafico-detalle" class="divide-y divide-gray-200">
                                <tr><td colspan="5" class="p-4 text-center text-gray-400">Cargando datos...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Tab 2: Detalle por Producto (Tabla Completa) -->
                <div id="tab-detalle" class="tab-contenido hidden overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-100 text-gray-600 border-b">
                            <tr>
                                <th class="p-3">Categoría / Rubro</th>
                                <th class="p-3">Producto</th>
                                <th class="p-3">Muestras</th>
                                <th class="p-3">Precio Estimado</th>
                                <th class="p-3">Costo Mensual AE</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-detalle" class="divide-y divide-gray-200">
                            <tr><td colspan="5" class="p-4 text-center text-gray-400">Cargando datos...</td></tr>
                        </tbody>
                    </table>
                </div>

                <!-- Tab 3: Tabla Nutricional -->
                <div id="tab-nutricional" class="tab-contenido hidden overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-100 text-gray-600 border-b">
                            <tr>
                                <th class="p-3">Categoría / Rubro</th>
                                <th class="p-3">Producto</th>
                                <th class="p-3">Cant. AE (Mensual)</th>
                                <th class="p-3">Kcal / Día</th>
                                <th class="p-3">Proteínas / Día</th>
                                <th class="p-3">Carbohidratos / Día</th>
                                <th class="p-3">Grasas / Día</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-nutricional" class="divide-y divide-gray-200">
                            <tr><td colspan="7" class="p-4 text-center text-gray-400">Cargando datos nutricionales...</td></tr>
                        </tbody>
                    </table>
                </div>

                <!-- Tab 4: Totales Históricos -->
                <div id="tab-totales" class="tab-contenido hidden overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-100 text-gray-600 border-b">
                            <tr>
                                <th class="p-3">Fecha / Registro</th>
                                <th class="p-3">Costo Total AE</th>
                                <th class="p-3">Costo Total Hogar Tipo (3.09 AE)</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-totales" class="divide-y divide-gray-200">
                            <tr><td colspan="3" class="p-4 text-center text-gray-400">Cargando histórico de totales...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            let globalDetalle = [];
            let miChartCategorias = null;
            let categoriaFiltroGrafico = null;

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

            function seleccionarTab(nombreTab) {
                const tabs = ['grafico', 'detalle', 'nutricional', 'totales'];
                tabs.forEach(t => {
                    const btn = document.getElementById(`btn-tab-${t}`);
                    const content = document.getElementById(`tab-${t}`);
                    if (t === nombreTab) {
                        btn.className = "py-3 px-4 text-sm font-semibold border-b-2 border-blue-600 text-blue-600 focus:outline-none whitespace-nowrap";
                        content.classList.remove('hidden');
                    } else {
                        btn.className = "py-3 px-4 text-sm font-semibold border-b-2 border-transparent text-gray-500 hover:text-gray-700 focus:outline-none whitespace-nowrap";
                        content.classList.add('hidden');
                    }
                });
            }

            function renderizarGraficoCategorias(datos) {
                const acumulado = {};
                datos.forEach(item => {
                    const cat = item.categoria || item.rubro || item.Rubro || 'Sin Categoría';
                    const costo = Number(item.costo_mensual_ae) || 0;
                    acumulado[cat] = (acumulado[cat] || 0) + costo;
                });

                const labels = Object.keys(acumulado);
                const values = Object.values(acumulado);

                const colores = [
                    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', 
                    '#EC4899', '#14B8A6', '#6366F1', '#84CC16', '#F97316'
                ];

                const ctx = document.getElementById('chart-categorias').getContext('2d');
                
                if (miChartCategorias) {
                    miChartCategorias.destroy();
                }

                miChartCategorias = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: values,
                            backgroundColor: colores.slice(0, labels.length)
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { boxWidth: 12, font: { size: 11 } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const val = context.raw || 0;
                                        return ` ${context.label}: $ ${val.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                                    }
                                }
                            }
                        },
                        onClick: (e, elements) => {
                            if (elements.length > 0) {
                                const index = elements[0].index;
                                const catSeleccionada = labels[index];
                                filtrarPorCategoriaGrafico(catSeleccionada);
                            }
                        }
                    }
                });
            }

            function filtrarPorCategoriaGrafico(cat) {
                if (categoriaFiltroGrafico === cat) {
                    limpiarFiltroCategoriaGrafico();
                    return;
                }
                categoriaFiltroGrafico = cat;
                
                const badge = document.getElementById('badge-filtro');
                badge.classList.remove('hidden');
                badge.classList.add('flex');
                document.getElementById('cat-filtrada-nombre').innerText = cat;
                
                poblarTablaGraficoDetalle();
            }

            function limpiarFiltroCategoriaGrafico() {
                categoriaFiltroGrafico = null;
                
                const badge = document.getElementById('badge-filtro');
                badge.classList.add('hidden');
                badge.classList.remove('flex');
                
                poblarTablaGraficoDetalle();
            }

            function poblarTablaGraficoDetalle() {
                const tbody = document.getElementById('tabla-grafico-detalle');
                tbody.innerHTML = '';

                if (!globalDetalle || globalDetalle.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">Sin datos de detalle.</td></tr>';
                    return;
                }

                const fechaReciente = globalDetalle[globalDetalle.length - 1]?.fecha;
                let filtrados = fechaReciente ? globalDetalle.filter(d => d.fecha === fechaReciente) : globalDetalle;
                if (filtrados.length === 0) filtrados = globalDetalle;

                if (categoriaFiltroGrafico) {
                    filtrados = filtrados.filter(item => {
                        const cat = item.categoria || item.rubro || item.Rubro || '-';
                        return cat === categoriaFiltroGrafico;
                    });
                }

                if (filtrados.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">No hay productos disponibles para esta categoría.</td></tr>';
                    return;
                }

                filtrados.forEach(item => {
                    const tr = document.createElement('tr');
                    const categoria = item.categoria || item.rubro || item.Rubro || '-';
                    const producto = item.producto || item.Producto || '-';
                    const muestras = item.coincidencias || item.muestras || 0;
                    const precio = Number(item.precio_unitario_estimado) || 0;
                    const costoAE = Number(item.costo_mensual_ae) || 0;

                    tr.innerHTML = `
                        <td class="p-3 text-gray-600 font-medium">${categoria}</td>
                        <td class="p-3 font-semibold text-gray-900">${producto}</td>
                        <td class="p-3 text-gray-500">${muestras}</td>
                        <td class="p-3">$ ${precio.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td class="p-3 font-semibold text-gray-800">$ ${costoAE.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            function poblarTablaDetalleGeneral() {
                const tbody = document.getElementById('tabla-detalle');
                tbody.innerHTML = '';

                if (!globalDetalle || globalDetalle.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">No se pudieron cargar los datos de detalle.</td></tr>';
                    return;
                }

                const fechaReciente = globalDetalle[globalDetalle.length - 1]?.fecha;
                let filtrados = fechaReciente ? globalDetalle.filter(d => d.fecha === fechaReciente) : globalDetalle;
                if (filtrados.length === 0) filtrados = globalDetalle;

                filtrados.forEach(item => {
                    const tr = document.createElement('tr');
                    const categoria = item.categoria || item.rubro || item.Rubro || '-';
                    const producto = item.producto || item.Producto || '-';
                    const muestras = item.coincidencias || item.muestras || 0;
                    const precio = Number(item.precio_unitario_estimado) || 0;
                    const costoAE = Number(item.costo_mensual_ae) || 0;

                    tr.innerHTML = `
                        <td class="p-3 text-gray-600 font-medium">${categoria}</td>
                        <td class="p-3 font-semibold text-gray-900">${producto}</td>
                        <td class="p-3 text-gray-500">${muestras}</td>
                        <td class="p-3">$ ${precio.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td class="p-3 font-semibold text-gray-800">$ ${costoAE.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            async function cargarDatos() {
                // 1. Cargar Totales (KPIs y Tabla Histórica)
                const totales = await fetchJSON('/api/totales');
                if (Array.isArray(totales) && totales.length > 0) {
                    const ultimo = totales[totales.length - 1];
                    const costoAE = Number(ultimo.costo_total_ae) || 0;
                    const costoHogar = Number(ultimo.costo_total_hogar) || 0;
                    
                    document.getElementById('costo-ae').innerText = `$ ${costoAE.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                    document.getElementById('costo-hogar').innerText = `$ ${costoHogar.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

                    // Poblar Tabla Histórica
                    const tbodyTotales = document.getElementById('tabla-totales');
                    tbodyTotales.innerHTML = '';
                    totales.slice().reverse().forEach(item => {
                        const tr = document.createElement('tr');
                        const fecha = item.timestamp || item.fecha || '-';
                        const cAE = Number(item.costo_total_ae) || 0;
                        const cHogar = Number(item.costo_total_hogar) || 0;

                        tr.innerHTML = `
                            <td class="p-3 text-gray-700 font-medium">${fecha}</td>
                            <td class="p-3 font-semibold text-emerald-600">$ ${cAE.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                            <td class="p-3 font-semibold text-blue-600">$ ${cHogar.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        `;
                        tbodyTotales.appendChild(tr);
                    });
                } else {
                    document.getElementById('costo-ae').innerText = 'Sin datos';
                    document.getElementById('costo-hogar').innerText = 'Sin datos';
                    document.getElementById('tabla-totales').innerHTML = '<tr><td colspan="3" class="p-4 text-center text-gray-500">Sin datos registrados.</td></tr>';
                }

                // 2. Cargar Detalle
                globalDetalle = await fetchJSON('/api/detalle');
                if (Array.isArray(globalDetalle) && globalDetalle.length > 0) {
                    const fechaReciente = globalDetalle[globalDetalle.length - 1]?.fecha;
                    let ultimosDatos = fechaReciente ? globalDetalle.filter(d => d.fecha === fechaReciente) : globalDetalle;
                    if (ultimosDatos.length === 0) ultimosDatos = globalDetalle;

                    renderizarGraficoCategorias(ultimosDatos);
                    poblarTablaGraficoDetalle();
                    poblarTablaDetalleGeneral();
                } else {
                    document.getElementById('tabla-grafico-detalle').innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">Sin datos de detalle.</td></tr>';
                    document.getElementById('tabla-detalle').innerHTML = '<tr><td colspan="5" class="p-4 text-center text-gray-500">Sin datos de detalle.</td></tr>';
                }

                // 3. Cargar Tabla Nutricional
                const nutricional = await fetchJSON('/api/nutricional');
                const tbodyNutri = document.getElementById('tabla-nutricional');
                tbodyNutri.innerHTML = '';

                if (Array.isArray(nutricional) && nutricional.length > 0) {
                    const fechaReciente = nutricional[nutricional.length - 1]?.fecha;
                    let filtradosNutri = fechaReciente ? nutricional.filter(n => n.fecha === fechaReciente) : nutricional;
                    if (filtradosNutri.length === 0) filtradosNutri = nutricional;

                    filtradosNutri.forEach(item => {
                        const tr = document.createElement('tr');
                        const categoria = item.categoria || item.rubro || item.Rubro || '-';
                        const producto = item.producto || item.Producto || '-';
                        const cantAE = Number(item.cantidad_ae) || 0;
                        const kcal = Number(item.kcal_diarias_ae) || 0;
                        const prot = Number(item.prot_diarias_g) || 0;
                        const carb = Number(item.carb_diarios_g) || 0;
                        const grasas = Number(item.grasas_diarias_g) || 0;

                        tr.innerHTML = `
                            <td class="p-3 text-gray-600 font-medium">${categoria}</td>
                            <td class="p-3 font-semibold text-gray-900">${producto}</td>
                            <td class="p-3 text-gray-500">${cantAE.toFixed(2)}</td>
                            <td class="p-3 text-emerald-700 font-medium">${kcal.toFixed(1)} kcal</td>
                            <td class="p-3">${prot.toFixed(1)} g</td>
                            <td class="p-3">${carb.toFixed(1)} g</td>
                            <td class="p-3">${grasas.toFixed(1)} g</td>
                        `;
                        tbodyNutri.appendChild(tr);
                    });
                } else {
                    tbodyNutri.innerHTML = '<tr><td colspan="7" class="p-4 text-center text-gray-500">No se pudieron cargar los datos nutricionales.</td></tr>';
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
