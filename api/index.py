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
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        :root { 
          --bg: #f8fafc; 
          --card: #ffffff; 
          --primary: #2563eb; 
          --secondary: #059669; 
          --text: #0f172a; 
          --sub: #64748b; 
          --border: #e2e8f0;
        }
        body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { margin-bottom: 24px; }
        h1 { margin: 0 0 8px 0; font-size: 1.75rem; }
        p.subtitle { margin: 0; color: var(--sub); font-size: 0.95rem; }
        
        /* Navegación por pestañas */
        .tabs {
          display: flex;
          gap: 12px;
          border-bottom: 2px solid var(--border);
          margin-bottom: 24px;
        }
        .tab-btn {
          padding: 12px 20px;
          background: none;
          border: none;
          border-bottom: 3px solid transparent;
          font-size: 0.95rem;
          font-weight: 600;
          color: var(--sub);
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .tab-btn:hover {
          color: var(--primary);
        }
        .tab-btn.active {
          color: var(--primary);
          border-bottom-color: var(--primary);
        }
        .tab-content {
          display: none;
        }
        .tab-content.active {
          display: block;
        }

        /* KPIs */
        .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .kpi-card { background: var(--card); padding: 20px; border-radius: 12px; border: 1px solid var(--border); }
        .kpi-card span { font-size: 0.85rem; color: var(--sub); font-weight: 600; text-transform: uppercase; }
        .kpi-card .value { font-size: 1.6rem; font-weight: 700; margin-top: 8px; color: var(--text); }
        
        /* Tarjetas e Historgramas/Tablas */
        .chart-card, .table-card { background: var(--card); padding: 24px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 24px; }
        .chart-container { position: relative; height: 380px; width: 100%; }

        /* Estilos de tablas */
        .table-container {
          overflow-x: auto;
          max-height: 500px;
          border: 1px solid var(--border);
          border-radius: 8px;
          margin-top: 16px;
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
          background: #f1f5f9;
          color: #334155;
          font-weight: 600;
          padding: 12px 16px;
          border-bottom: 2px solid var(--border);
          white-space: nowrap;
          z-index: 10;
        }
        td {
          padding: 10px 16px;
          border-bottom: 1px solid var(--border);
          white-space: nowrap;
        }
        tr:hover {
          background-color: #f8fafc;
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
          <button class="tab-btn active" onclick="cambiarTab(event, 'tab-totales')">Totales</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-nutricional')">Información Nutricional</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-historico')">Histórico</button>
        </nav>

        <!-- Pestaña 1: Totales -->
        <div id="tab-totales" class="tab-content active">
          <div class="kpis">
            <div class="kpi-card">
              <span>CBA Hogar Tipo</span>
              <div class="value" id="kpi-cba">$ --</div>
            </div>
            <div class="kpi-card">
              <span>CBT Hogar Tipo</span>
              <div class="value" id="kpi-cbt">$ --</div>
            </div>
            <div class="kpi-card">
              <span>Cobertura Scraper</span>
              <div class="value" id="kpi-cobertura">-- %</div>
            </div>
          </div>

          <div class="chart-card">
            <h3>Evolución Histórica de Costos</h3>
            <div class="chart-container">
              <canvas id="cbaChart"></canvas>
            </div>
          </div>

          <div class="table-card">
            <h3>Tabla de Totales</h3>
            <div class="table-container" id="tabla-totales-container">
              <p style="padding: 16px; color: var(--sub);">Cargando tabla de totales...</p>
            </div>
          </div>
        </div>

        <!-- Pestaña 2: Información Nutricional -->
        <div id="tab-nutricional" class="tab-content">
          <div class="table-card">
            <h3>Tabla de Información Nutricional</h3>
            <div class="table-container" id="tabla-nutricional-container">
              <p style="padding: 16px; color: var(--sub);">Cargando información nutricional...</p>
            </div>
          </div>
        </div>

        <!-- Pestaña 3: Histórico -->
        <div id="tab-historico" class="tab-content">
          <div class="table-card">
            <h3>Tabla de Datos Históricos</h3>
            <div class="table-container" id="tabla-historico-container">
              <p style="padding: 16px; color: var(--sub);">Cargando histórico...</p>
            </div>
          </div>
        </div>
      </div>

      <script>
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

            const fechas = data.map(i => i.fecha);
            const cbaHogar = data.map(i => parseFloat(i.costo_total_cba_hogar));
            const cbtHogar = data.map(i => parseFloat(i.costo_total_cbt_hogar));

            new Chart(document.getElementById('cbaChart'), {
              type: 'line',
              data: {
                labels: fechas,
                datasets: [
                  {
                    label: 'CBA Hogar Tipo',
                    data: cbaHogar,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.2
                  },
                  {
                    label: 'CBT Hogar Tipo',
                    data: cbtHogar,
                    borderColor: '#059669',
                    backgroundColor: 'rgba(5, 150, 105, 0.1)',
                    fill: true,
                    tension: 0.2
                  }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: {
                  y: {
                    ticks: { callback: (val) => '$' + val.toLocaleString('es-AR') }
                  }
                }
              }
            });

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
        leer_csv("cba_historico.csv") or
        leer_csv("cba_historico_precios.csv") or
        leer_csv("cba_precios.csv")
    )
    if data is not None:
        return data
    return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
