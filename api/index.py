from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import io
import ssl
import csv
import urllib.request

app = FastAPI(title="CBA Scraper API")
handler = app

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
    
    try:
        req = urllib.request.Request(url_remota, headers={'User-Agent': 'Mozilla/5.0'})
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=8, context=ssl_context) as response:
            contenido = response.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(contenido))
            return list(reader)
    except Exception as e:
        print(f"Error descargando {url_remota}: {e}")

    rutas_locales = [
        nombre_archivo,
        os.path.join("..", nombre_archivo),
        os.path.join(os.path.dirname(__file__), "..", nombre_archivo)
    ]
    for ruta in rutas_locales:
        if os.path.exists(ruta):
            try:
                with open(ruta, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            except Exception as e:
                print(f"Error leyendo local {ruta}: {e}")

    return None

@app.get("/", response_class=HTMLResponse)
def render_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Dashboard - Canasta Básica Alimentaria</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
      <style>
        :root { 
          --bg: #f1f5f9; 
          --card: #ffffff; 
          --primary: #4f46e5; 
          --primary-gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
          --secondary: #10b981; 
          --text: #0f172a; 
          --sub: #64748b; 
          --border: #e2e8f0;
        }
        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; }
        .container { max-width: 1280px; margin: 0 auto; }
        
        /* Header vistoso con gradiente */
        header { 
          background: linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%); 
          color: white; 
          padding: 28px 32px; 
          border-radius: 16px; 
          margin-bottom: 28px;
          box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.3);
        }
        h1 { margin: 0 0 6px 0; font-size: 2rem; font-weight: 800; display: flex; align-items: center; gap: 12px; }
        p.subtitle { margin: 0; opacity: 0.9; font-size: 1rem; font-weight: 400; }
        
        /* Navegación por pestañas */
        .tabs {
          display: flex;
          gap: 10px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }
        .tab-btn {
          padding: 12px 24px;
          background: #ffffff;
          border: 1px solid #cbd5e1;
          border-radius: 12px;
          font-size: 0.95rem;
          font-weight: 600;
          color: #475569;
          cursor: pointer;
          transition: all 0.25s ease;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .tab-btn:hover {
          background: #f8fafc;
          color: var(--primary);
          border-color: #a5b4fc;
          transform: translateY(-1px);
        }
        .tab-btn.active {
          background: var(--primary-gradient);
          color: #ffffff;
          border-color: transparent;
          box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
        }
        .tab-content {
          display: none;
          animation: fadeIn 0.3s ease-in-out;
        }
        .tab-content.active {
          display: block;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* KPIs Estilizados y Coloridos */
        .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 24px; }
        .kpi-card { 
          background: var(--card); 
          padding: 22px; 
          border-radius: 16px; 
          border: 1px solid var(--border);
          box-shadow: 0 4px 15px rgba(0,0,0,0.03);
          position: relative;
          overflow: hidden;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .kpi-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 8px 25px rgba(0,0,0,0.06);
        }
        .kpi-card.cba {
          border-left: 6px solid #3b82f6;
          background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
        }
        .kpi-card.cbt {
          border-left: 6px solid #10b981;
          background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
        }
        .kpi-card.cobertura {
          border-left: 6px solid #f59e0b;
          background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
        }
        .kpi-card span { font-size: 0.85rem; color: var(--sub); font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
        .kpi-card .value { font-size: 1.8rem; font-weight: 800; margin-top: 10px; color: var(--text); }
        .kpi-card.cba .value { color: #1d4ed8; }
        .kpi-card.cbt .value { color: #047857; }
        .kpi-card.cobertura .value { color: #b45309; }

        /* Tarjetas e Histogramas/Tablas */
        .chart-card, .table-card { 
          background: var(--card); 
          padding: 26px; 
          border-radius: 16px; 
          border: 1px solid var(--border); 
          margin-bottom: 24px;
          box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        }
        .card-title {
          margin: 0 0 18px 0;
          font-size: 1.2rem;
          font-weight: 700;
          color: #1e293b;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .chart-container { position: relative; height: 380px; width: 100%; }
        .grid-charts {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
          gap: 24px;
        }
        @media (max-width: 640px) {
          .grid-charts { grid-template-columns: 1fr; }
        }

        /* Estilos de tablas */
        .table-container {
          overflow-x: auto;
          max-height: 520px;
          border: 1px solid var(--border);
          border-radius: 12px;
          margin-top: 12px;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }
        table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.875rem;
          text-align: left;
        }
        th {
          position: sticky;
          top: 0;
          background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%);
          color: #ffffff;
          font-weight: 700;
          padding: 14px 18px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-size: 0.78rem;
          white-space: nowrap;
          z-index: 10;
        }
        td {
          padding: 12px 18px;
          border-bottom: 1px solid var(--border);
          white-space: nowrap;
          color: #334155;
        }
        tr:nth-child(even) {
          background-color: #f8fafc;
        }
        tr:hover {
          background-color: #e0e7ff;
          transition: background-color 0.15s ease;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <header>
          <h1>📊 Canasta Básica Alimentaria (CBA & CBT)</h1>
          <p class="subtitle">Monitoreo y estimación de costos vía Web Scraping</p>
        </header>

        <!-- Navegación por Pestañas -->
        <nav class="tabs">
          <button class="tab-btn active" onclick="cambiarTab(event, 'tab-resumen')">📈 Resumen General</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-graficos')">📊 Gráficos Analíticos</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-totales')">📋 Tabla de Totales</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-nutricional')">🥗 Información Nutricional</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-historico')">🗂️ Histórico Detallado</button>
        </nav>

        <!-- Pestaña 1: Resumen General (KPIs y Gráfico Principal) -->
        <div id="tab-resumen" class="tab-content active">
          <div class="kpis">
            <div class="kpi-card cba">
              <span>CBA Hogar Tipo</span>
              <div class="value" id="kpi-cba">$ --</div>
            </div>
            <div class="kpi-card cbt">
              <span>CBT Hogar Tipo</span>
              <div class="value" id="kpi-cbt">$ --</div>
            </div>
            <div class="kpi-card cobertura">
              <span>Cobertura Scraper</span>
              <div class="value" id="kpi-cobertura">-- %</div>
            </div>
          </div>

          <div class="chart-card">
            <h3 class="card-title">📈 Evolución Histórica de Costos</h3>
            <div class="chart-container">
              <canvas id="cbaChartResumen"></canvas>
            </div>
          </div>
        </div>

        <!-- Pestaña 2: Gráficos Analíticos -->
        <div id="tab-graficos" class="tab-content">
          <div class="grid-charts">
            <div class="chart-card">
              <h3 class="card-title">🏷️ Contribución al Costo por Rubro (%)</h3>
              <div class="chart-container">
                <canvas id="rubroChart"></canvas>
              </div>
            </div>

            <div class="chart-card">
              <h3 class="card-title">🎯 Cobertura del Scraper (%)</h3>
              <div class="chart-container">
                <canvas id="coberturaChart"></canvas>
              </div>
            </div>

            <div class="chart-card">
              <h3 class="card-title">🥗 Composición Nutricional / Gramaje por Alimento</h3>
              <div class="chart-container">
                <canvas id="nutricionalChart"></canvas>
              </div>
            </div>
          </div>
        </div>

        <!-- Pestaña 3: Tabla de Totales -->
        <div id="tab-totales" class="tab-content">
          <div class="table-card">
            <h3 class="card-title">📋 Tabla de Totales (CBA / CBT)</h3>
            <div class="table-container" id="tabla-totales-container">
              <p style="padding: 16px; color: var(--sub);">Cargando tabla de totales...</p>
            </div>
          </div>
        </div>

        <!-- Pestaña 4: Información Nutricional -->
        <div id="tab-nutricional" class="tab-content">
          <div class="table-card">
            <h3 class="card-title">🥗 Tabla de Información Nutricional</h3>
            <div class="table-container" id="tabla-nutricional-container">
              <p style="padding: 16px; color: var(--sub);">Cargando información nutricional...</p>
            </div>
          </div>
        </div>

        <!-- Pestaña 5: Histórico Detallado -->
        <div id="tab-historico" class="tab-content">
          <div class="table-card">
            <h3 class="card-title">🗂️ Tabla de Datos Históricos</h3>
            <div class="table-container" id="tabla-historico-container">
              <p style="padding: 16px; color: var(--sub);">Cargando histórico...</p>
            </div>
          </div>
        </div>
      </div>

      <script>
        let chartResumenInstance = null;
        let chartCoberturaInstance = null;
        let chartNutricionalInstance = null;
        let chartRubroInstance = null;

        function cambiarTab(evt, tabId) {
          const contents = document.querySelectorAll('.tab-content');
          contents.forEach(c => c.classList.remove('active'));

          const btns = document.querySelectorAll('.tab-btn');
          btns.forEach(b => b.classList.remove('active'));

          document.getElementById(tabId).classList.add('active');
          evt.currentTarget.classList.add('active');
        }

        function crearTabla(data, containerId) {
          const container = document.getElementById(containerId);
          if (!data || !Array.isArray(data) || data.length === 0) {
            container.innerHTML = '<p style="padding: 16px; color: var(--sub);">No hay datos disponibles.</p>';
            return;
          }

          const cols = Object.keys(data[0]);
          let html = '<table><thead><tr>';
          cols.forEach(col => {
            const headerName = col.replace(/_/g, ' ').toUpperCase();
            html += `<th>${headerName}</th>`;
          });
          html += '</tr></thead><tbody>';

          data.forEach(row => {
            html += '<tr>';
            cols.forEach(col => {
              html += `<td>${row[col] !== null && row[col] !== undefined ? row[col] : ''}</td>`;
            });
            html += '</tr>';
          });
          html += '</tbody></table>';

          container.innerHTML = html;
        }

        function renderizarGraficosTotales(data) {
          if (!data || data.length === 0) return;

          const fechas = data.map(i => i.fecha);
          const cbaHogar = data.map(i => parseFloat(i.costo_total_cba_hogar));
          const cbtHogar = data.map(i => parseFloat(i.costo_total_cbt_hogar));
          const coberturas = data.map(i => parseFloat(i.cobertura_scraper_pct || 0));

          // Gráfico en la pestaña Resumen
          const ctxResumen = document.getElementById('cbaChartResumen').getContext('2d');
          const gradCBA = ctxResumen.createLinearGradient(0, 0, 0, 400);
          gradCBA.addColorStop(0, 'rgba(59, 130, 246, 0.35)');
          gradCBA.addColorStop(1, 'rgba(59, 130, 246, 0.01)');

          const gradCBT = ctxResumen.createLinearGradient(0, 0, 0, 400);
          gradCBT.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
          gradCBT.addColorStop(1, 'rgba(16, 185, 129, 0.01)');

          const chartConfigEvolucion = {
            type: 'line',
            data: {
              labels: fechas,
              datasets: [
                {
                  label: 'CBA Hogar Tipo',
                  data: cbaHogar,
                  borderColor: '#2563eb',
                  backgroundColor: gradCBA,
                  borderWidth: 3,
                  pointBackgroundColor: '#1d4ed8',
                  pointRadius: 4,
                  pointHoverRadius: 7,
                  fill: true,
                  tension: 0.3
                },
                {
                  label: 'CBT Hogar Tipo',
                  data: cbtHogar,
                  borderColor: '#10b981',
                  backgroundColor: gradCBT,
                  borderWidth: 3,
                  pointBackgroundColor: '#047857',
                  pointRadius: 4,
                  pointHoverRadius: 7,
                  fill: true,
                  tension: 0.3
                }
              ]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { 
                legend: { 
                  position: 'top',
                  labels: { font: { size: 13, weight: 'bold' }, usePointStyle: true, padding: 20 }
                } 
              },
              scales: {
                y: {
                  grid: { color: '#f1f5f9' },
                  ticks: { font: { size: 12 }, callback: (val) => '$' + val.toLocaleString('es-AR') }
                },
                x: { grid: { display: false }, ticks: { font: { size: 12 } } }
              }
            }
          };

          if (chartResumenInstance) chartResumenInstance.destroy();
          chartResumenInstance = new Chart(ctxResumen, chartConfigEvolucion);

          // Gráfico de Cobertura (%)
          const ctxCobertura = document.getElementById('coberturaChart').getContext('2d');
          if (chartCoberturaInstance) chartCoberturaInstance.destroy();
          chartCoberturaInstance = new Chart(ctxCobertura, {
            type: 'bar',
            data: {
              labels: fechas,
              datasets: [{
                label: 'Cobertura del Scraper (%)',
                data: coberturas,
                backgroundColor: 'rgba(245, 158, 11, 0.75)',
                borderColor: '#d97706',
                borderWidth: 1.5,
                borderRadius: 6
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false }
              },
              scales: {
                y: {
                  min: 0,
                  max: 100,
                  ticks: { callback: (val) => val + '%' }
                },
                x: { grid: { display: false } }
              }
            }
          });
        }

        function renderizarGraficoNutricional(data) {
          if (!data || data.length === 0) return;

          const keyProducto = Object.keys(data[0]).find(k => k.includes('producto') || k.includes('alimento') || k.includes('item')) || Object.keys(data[0])[0];
          const keyValor = Object.keys(data[0]).find(k => k.includes('gramo') || k.includes('cantidad') || k.includes('valor') || k.includes('kcal')) || Object.keys(data[0])[1];

          const productos = data.slice(0, 12).map(i => i[keyProducto] || 'N/D');
          const valores = data.slice(0, 12).map(i => parseFloat(i[keyValor] || 0));

          const ctxNut = document.getElementById('nutricionalChart').getContext('2d');
          if (chartNutricionalInstance) chartNutricionalInstance.destroy();
          chartNutricionalInstance = new Chart(ctxNut, {
            type: 'bar',
            data: {
              labels: productos,
              datasets: [{
                label: keyValor.replace(/_/g, ' ').toUpperCase(),
                data: valores,
                backgroundColor: 'rgba(99, 102, 241, 0.75)',
                borderColor: '#4f46e5',
                borderWidth: 1.5,
                borderRadius: 6
              }]
            },
            options: {
              indexAxis: 'y',
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false }
              },
              scales: {
                x: { grid: { color: '#f1f5f9' } },
                y: { grid: { display: false } }
              }
            }
          });
        }

        function renderizarGraficoRubros(data) {
          if (!data || data.length === 0) return;

          // Detectar columnas asociadas a rubro y costo
          const keyRubro = Object.keys(data[0]).find(k => k.includes('rubro') || k.includes('categoria') || k.includes('grupo')) || 'rubro';
          const keyCosto = Object.keys(data[0]).find(k => k.includes('costo') || k.includes('subtotal') || k.includes('precio') || k.includes('total')) || 'costo';

          // Filtrar por la última fecha cargada en los datos históricos si existe la columna fecha
          const fechas = [...new Set(data.map(i => i.fecha).filter(Boolean))];
          const ultimaFecha = fechas.length > 0 ? fechas[fechas.length - 1] : null;
          const datosFiltrados = ultimaFecha ? data.filter(i => i.fecha === ultimaFecha) : data;

          const acumRubro = {};
          let costoTotalGeneral = 0;

          datosFiltrados.forEach(row => {
            const rubro = row[keyRubro] || 'Otros';
            const costo = parseFloat(row[keyCosto] || 0);
            if (!isNaN(costo) && costo > 0) {
              acumRubro[rubro] = (acumRubro[rubro] || 0) + costo;
              costoTotalGeneral += costo;
            }
          });

          const rubros = Object.keys(acumRubro);
          if (rubros.length === 0 || costoTotalGeneral === 0) return;

          const porcentajes = rubros.map(r => ((acumRubro[r] / costoTotalGeneral) * 100).toFixed(1));

          // Paleta de colores variados para distinguir cada rubro
          const colores = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
            '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
            '#14b8a6', '#a855f7'
          ];

          const ctxRubro = document.getElementById('rubroChart').getContext('2d');
          if (chartRubroInstance) chartRubroInstance.destroy();

          chartRubroInstance = new Chart(ctxRubro, {
            type: 'bar',
            data: {
              labels: rubros,
              datasets: [{
                label: 'Contribución al Costo (%)',
                data: porcentajes,
                backgroundColor: colores.slice(0, rubros.length),
                borderColor: colores.slice(0, rubros.length),
                borderWidth: 1,
                borderRadius: 6
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      const rubro = context.label;
                      const pct = context.parsed.y;
                      const monto = acumRubro[rubro] ? `$${acumRubro[rubro].toLocaleString('es-AR', {maximumFractionDigits: 2})}` : '';
                      return ` ${pct}% (${monto})`;
                    }
                  }
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  grid: { color: '#f1f5f9' },
                  ticks: { callback: (val) => val + '%' }
                },
                x: { grid: { display: false } }
              }
            }
          });
        }

        async function cargarTotales() {
          try {
            const res = await fetch('/api/totales');
            const data = await res.json();
            if (!data || data.length === 0) return;

            const ultimo = data[data.length - 1];
            const fmt = (val) => new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(val);
            
            document.getElementById('kpi-cba').textContent = fmt(ultimo.costo_total_cba_hogar || 0);
            document.getElementById('kpi-cbt').textContent = fmt(ultimo.costo_total_cbt_hogar || 0);
            document.getElementById('kpi-cobertura').textContent = `${parseFloat(ultimo.cobertura_scraper_pct || 0).toFixed(1)}%`;

            renderizarGraficosTotales(data);
            crearTabla(data, 'tabla-totales-container');
          } catch (err) {
            console.error('Error cargando totales:', err);
            document.getElementById('tabla-totales-container').innerHTML = '<p style="padding: 16px; color: #ef4444;">Error al cargar la tabla de totales.</p>';
          }
        }

        async function cargarNutricional() {
          try {
            const res = await fetch('/api/nutricional');
            const data = await res.json();
            renderizarGraficoNutricional(data);
            crearTabla(data, 'tabla-nutricional-container');
          } catch (err) {
            console.error('Error cargando información nutricional:', err);
            document.getElementById('tabla-nutricional-container').innerHTML = '<p style="padding: 16px; color: var(--sub);">No se pudo cargar la información nutricional.</p>';
          }
        }

        async function cargarHistorico() {
          try {
            const res = await fetch('/api/historico');
            const data = await res.json();
            renderizarGraficoRubros(data);
            crearTabla(data, 'tabla-historico-container');
          } catch (err) {
            console.error('Error cargando histórico:', err);
            document.getElementById('tabla-historico-container').innerHTML = '<p style="padding: 16px; color: var(--sub);">No se pudo cargar el histórico.</p>';
          }
        }

        function cargarDashboard() {
          cargarTotales();
          cargarNutricional();
          cargarHistorico();
        }

        cargarDashboard();
      </script>
    </body>
    </html>
    """

@app.get("/api/totales")
def get_totales():
    data = leer_csv("cba_historico_totales.csv")
    if data is not None:
        return data
    return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})

@app.get("/api/nutricional")
def get_nutricional():
    data = (
        leer_csv("cba_tabla_nutricional.csv") or
        leer_csv("cba_nutricional.csv") or
        leer_csv("cba_informacion_nutricional.csv") or
        leer_csv("cba_nutricion.csv")
    )
    if data is not None:
        return data
    return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})

@app.get("/api/historico")
def get_historico():
    data = (
        leer_csv("cba_historico_detalle.csv") or
        leer_csv("cba_historico.csv") or
        leer_csv("cba_historico_precios.csv") or
        leer_csv("cba_precios.csv")
    )
    if data is not None:
        return data
    return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
