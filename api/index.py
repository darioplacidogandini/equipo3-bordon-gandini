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
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 18px;">
              <h3 class="card-title" style="margin: 0;">🥗 Tabla de Información Nutricional</h3>
              <div style="display: flex; align-items: center; gap: 8px;">
                <label for="filtro-rubro-nutricional" style="font-weight: 600; font-size: 0.9rem; color: #475569;">Filtrar por Rubro:</label>
                <select id="filtro-rubro-nutricional" onchange="filtrarNutricional()" style="padding: 8px 12px; border-radius: 8px; border: 1px solid var(--border); font-size: 0.9rem; background: #ffffff; cursor: pointer; color: var(--text);">
                  <option value="todos">Todos los rubros
