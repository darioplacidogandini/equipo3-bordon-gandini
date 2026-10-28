from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import io
import ssl
import csv
import urllib.request

app = FastAPI(title="CBA Scraper API - Equipo 3")
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

    return []

def procesar_totales(rows):
    if not rows:
        return []
    ultimo_valido = None
    for row in rows:
        try:
            prod_real = float(row.get('prod_real', 0))
            cobertura = float(row.get('cobertura_scraper_pct', 0))
        except (ValueError, TypeError):
            prod_real = 0
            cobertura = 0
            
        if prod_real > 0 or cobertura > 0:
            ultimo_valido = row.copy()
        else:
            if ultimo_valido is not None:
                fecha_actual = row.get('fecha')
                row.update(ultimo_valido)
                row['fecha'] = fecha_actual
    return rows

@app.get("/api/totales")
def get_totales():
    datos = leer_csv("cba_historico_totales.csv")
    return JSONResponse(content=procesar_totales(datos))

@app.get("/api/detalle")
def get_detalle():
    return JSONResponse(content=leer_csv("cba_historico_detalle.csv"))

@app.get("/api/nutricional")
def get_nutricional():
    return JSONResponse(content=leer_csv("cba_tabla_nutricional.csv"))

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def render_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Panel de Monitoreo - Canasta Básica Alimentaria</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
      <style>
        :root { 
          --bg: #f8fafc; 
          --card: #ffffff; 
          --primary: #1e293b; 
          --primary-accent: #334155;
          --secondary: #0f172a; 
          --text: #0f172a; 
          --sub: #475569; 
          --border: #cbd5e1;
        }
        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; }
        .container { max-width: 1280px; margin: 0 auto; }
        header { 
          background: #1e293b; 
          color: white; 
          padding: 24px 32px; 
          border-radius: 8px; 
          margin-bottom: 24px;
          border-left: 6px solid #0f172a;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        h1 { margin: 0 0 6px 0; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.025em; }
        p.subtitle { margin: 0; opacity: 0.85; font-size: 0.95rem; font-weight: 400; }
        .tabs { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; border-bottom: 2px solid var(--border); padding-bottom: 12px; }
        .tab-btn {
          padding: 10px 20px; background: #ffffff; border: 1px solid var(--border); border-radius: 6px;
          font-size: 0.9rem; font-weight: 600; color: #334155; cursor: pointer; transition: all 0.2s ease;
        }
        .tab-btn:hover { background: #f1f5f9; color: var(--primary); border-color: #94a3b8; }
        .tab-btn.active { background: #1e293b; color: #ffffff; border-color: #1e293b; }
        .tab-content { display: none; animation: fadeIn 0.25s ease-in-out; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 24px; }
        .kpi-card { 
          background: var(--card); padding: 20px; border-radius: 8px; border: 1px solid var(--border);
          box-shadow: 0 1px 3px rgba(0,0,0,0.05); position: relative;
        }
        .kpi-card.cba { border-top: 4px solid #334155; }
        .kpi-card.cbt { border-top: 4px solid #475569; }
        .kpi-card.cobertura { border-top: 4px solid #64748b; }
        .kpi-card span { font-size: 0.8rem; color: var(--sub); font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
        .kpi-card .value { font-size: 1.6rem; font-weight: 700; margin-top: 8px; color: var(--text); }
        .chart-card, .table-card { 
          background: var(--card); padding: 24px; border-radius: 8px; border: 1px solid var(--border); 
          margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .card-title { margin: 0 0 16px 0; font-size: 1.1rem; font-weight: 700; color: #1e293b; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
        .chart-container { position: relative; height: 380px; width: 100%; }
        .grid-charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 24px; }
        @media (max-width: 640px) { .grid-charts { grid-template-columns: 1fr; } }
        .table-container { overflow-x: auto; max-height: 520px; border: 1px solid var(--border); border-radius: 6px; margin-top: 12px; }
        table { width: 100%; border-collapse: collapse; font-size: 0.875rem; text-align: left; }
        th { position: sticky; top: 0; background: #334155; color: #ffffff; font-weight: 600; padding: 12px 16px; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; white-space: nowrap; z-index: 10; }
        td { padding: 10px 16px; border-bottom: 1px solid var(--border); white-space: nowrap; color: #334155; }
        tr:nth-child(even) { background-color: #f8fafc; }
        tr:hover { background-color: #f1f5f9; }
        .download-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
        .download-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .download-card h4 { margin: 0 0 8px 0; color: #1e293b; font-size: 1.05rem; }
        .download-card p { margin: 0 0 16px 0; color: var(--sub); font-size: 0.875rem; }
        .btn-download { display: inline-block; padding: 10px 16px; background: #1e293b; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 0.875rem; text-align: center; transition: background 0.2s; cursor: pointer; border: none; }
        .btn-download:hover { background: #334155; }
      </style>
    </head>
    <body>
      <div class="container">
        <header>
          <h1>Canasta Básica Alimentaria (CBA & CBT)</h1>
          <p class="subtitle">Sistema de Monitoreo y Estimación Económica vía Web Scraping</p>
        </header>

        <nav class="tabs">
          <button class="tab-btn active" onclick="cambiarTab(event, 'tab-resumen')">Resumen General</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-graficos')">Gráficos Analíticos</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-totales')">Tabla de Totales</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-nutricional')">Información Nutricional</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-historico')">Histórico Detallado</button>
          <button class="tab-btn" onclick="cambiarTab(event, 'tab-descargas')">Descarga de CSVs</button>
        </nav>

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
              <span>Cobertura de Scraper</span>
              <div class="value" id="kpi-cobertura">-- %</div>
            </div>
          </div>
          <div class="chart-card">
            <h3 class="card-title">Evolución Histórica de Costos</h3>
            <div class="chart-container">
              <canvas id="cbaChartResumen"></canvas>
            </div>
          </div>
        </div>

        <div id="tab-graficos" class="tab-content">
          <div class="grid-charts">
            <div class="chart-card">
              <h3 class="card-title">Contribución al Costo por Rubro (%)</h3>
              <div class="chart-container"><canvas id="rubroChart"></canvas></div>
            </div>
            <div class="chart-card">
              <h3 class="card-title">Cobertura del Scraper (%)</h3>
              <div class="chart-container"><canvas id="coberturaChart"></canvas></div>
            </div>
            <div class="chart-card">
              <h3 class="card-title">Composición Nutricional / Gramaje por Alimento</h3>
              <div class="chart-container"><canvas id="nutricionalChart"></canvas></div>
            </div>
          </div>
        </div>

        <div id="tab-totales" class="tab-content">
          <div class="table-card">
            <h3 class="card-title">Tabla de Totales (CBA / CBT)</h3>
            <div class="table-container" id="tabla-totales-container">
              <p style="padding: 16px; color: var(--sub);">Cargando tabla de totales...</p>
            </div>
          </div>
        </div>

        <div id="tab-nutricional" class="tab-content">
          <div class="table-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px;">
              <h3 class="card-title" style="margin: 0; border: none; padding: 0;">Tabla de Información Nutricional</h3>
              <div style="display: flex; align-items: center; gap: 8px;">
                <label for="filtro-rubro-nutricional" style="font-weight: 600; font-size: 0.9rem; color: #334155;">Filtrar por Rubro:</label>
                <select id="filtro-rubro-nutricional" onchange="filtrarNutricional()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border); font-size: 0.9rem; background: #ffffff; cursor: pointer; color: var(--text);">
                  <option value="todos">Todos los rubros</option>
                </select>
              </div>
            </div>
            <div class="table-container" id="tabla-nutricional-container">
              <p style="padding: 16px; color: var(--sub);">Cargando información nutricional...</p>
            </div>
          </div>
        </div>

        <div id="tab-historico" class="tab-content">
          <div class="table-card">
            <h3 class="card-title">Histórico Detallado</h3>
            <div class="table-container" id="tabla-historico-container">
              <p style="padding: 16px; color: var(--sub);">Cargando histórico...</p>
            </div>
          </div>
        </div>

        <div id="tab-descargas" class="tab-content">
          <div class="table-card">
            <h3 class="card-title">Descarga de Archivos de Datos (CSV)</h3>
            <p style="color: var(--sub); margin-bottom: 20px; font-size: 0.95rem;">Acceda y descargue directamente los archivos oficiales generados por el sistema de monitoreo:</p>
            <div class="download-grid">
              <div class="download-card">
                <div>
                  <h4>Histórico de Totales</h4>
                  <p>Contiene el resumen diario de costos para CBA (Adulto Equivalente y Hogar Tipo) y CBT junto con la cobertura del scraper.</p>
                </div>
                <button onclick="descargarArchivo('https://raw.githubusercontent.com/darioplacidogandini/equipo3-bordon-gandini/main/cba_historico_totales.csv', 'cba_historico_totales.csv')" class="btn-download">Descargar Totales (CSV)</button>
              </div>
              <div class="download-card">
                <div>
                  <h4>Histórico Detallado</h4>
                  <p>Detalle de precios unitarios estimados, dispersión y costos desglosados por producto y supermercado en cada ejecución.</p>
                </div>
                <button onclick="descargarArchivo('https://raw.githubusercontent.com/darioplacidogandini/equipo3-bordon-gandini/main/cba_historico_detalle.csv', 'cba_historico_detalle.csv')" class="btn-download">Descargar Detalle (CSV)</button>
              </div>
              <div class="download-card">
                <div>
                  <h4>Tabla Nutricional</h4>
                  <p>Información oficial INDEC desglosada por producto con coeficientes de calorías, proteínas, carbohidratos y grasas.</p>
                </div>
                <button onclick="descargarArchivo('https://raw.githubusercontent.com/darioplacidogandini/equipo3-bordon-gandini/main/cba_tabla_nutricional.csv', 'cba_tabla_nutricional.csv')" class="btn-download">Descargar Nutricional (CSV)</button>
              </div>
              <div class="download-card">
                <div>
                  <h4>Registro de Errores (Log)</h4>
                  <p>Historial detallado de eventos, advertencias y avisos de ejecución del scraper diario.</p>
                </div>
                <button onclick="descargarArchivo('https://raw.githubusercontent.com/darioplacidogandini/equipo3-bordon-gandini/main/cba_errores_log.txt', 'cba_errores_log.txt')" class="btn-download">Ver Log de Errores (TXT)</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <script>
        function cambiarTab(evt, tabId) {
          document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
          document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
          document.getElementById(tabId).classList.add('active');
          evt.currentTarget.classList.add('active');
          window.dispatchEvent(new Event('resize'));
        }

        async function descargarArchivo(url, nombreArchivo) {
          try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('No se pudo descargar el archivo');
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = nombreArchivo;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(blobUrl);
          } catch (error) {
            console.error('Error en la descarga:', error);
            // Fallback: abrir en nueva pestaña si falla el blob por políticas extremas
            window.open(url, '_blank');
          }
        }

        let datosDetalle = [];
        let datosNutricional = [];
        let datosTotales = [];

        async function cargarDatos() {
          try {
            const [resTotales, resDetalle, resNutricional] = await Promise.all([
              fetch('/api/totales').then(r => r.json()),
              fetch('/api/detalle').then(r => r.json()),
              fetch('/api/nutricional').then(r => r.json())
            ]);

            datosTotales = resTotales;
            datosDetalle = resDetalle;
            datosNutricional = resNutricional;

            actualizarKPIs();
            renderGraficoResumen();
            renderGraficoRubros();
            renderGraficoCobertura();
            renderGraficoNutricional();
            renderTablaTotales();
            poblarFiltroRubros();
            renderTablaNutricional(datosNutricional);
            renderTablaHistorico();
          } catch (e) {
            console.error("Error cargando datos de API:", e);
          }
        }

        function formatearMoneda(valor) {
          return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(valor);
        }

        function actualizarKPIs() {
          if (datosTotales.length > 0) {
            const ultimo = datosTotales[datosTotales.length - 1];
            document.getElementById('kpi-cba').innerText = formatearMoneda(Number(ultimo.costo_total_cba_hogar || 0));
            document.getElementById('kpi-cbt').innerText = formatearMoneda(Number(ultimo.costo_total_cbt_hogar || 0));
            document.getElementById('kpi-cobertura').innerText = Number(ultimo.cobertura_scraper_pct || 0).toFixed(1) + ' %';
          }
        }

        let chartResumenInstance = null;
        function renderGraficoResumen() {
          const ctx = document.getElementById('cbaChartResumen');
          if (!ctx) return;
          const labels = datosTotales.map(d => d.fecha);
          const cbaHogar = datosTotales.map(d => Number(d.costo_total_cba_hogar || 0));
          const cbtHogar = datosTotales.map(d => Number(d.costo_total_cbt_hogar || 0));

          if (chartResumenInstance) chartResumenInstance.destroy();

          chartResumenInstance = new Chart(ctx, {
            type: 'line',
            data: {
              labels: labels.length ? labels : ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
              datasets: [
                { label: 'CBA Hogar', data: cbaHogar.length ? cbaHogar : [120000, 125000, 132000, 140000, 148000, 155000], borderColor: '#334155', backgroundColor: 'rgba(51,65,85,0.05)', fill: true, tension: 0.2 },
                { label: 'CBT Hogar', data: cbtHogar.length ? cbtHogar : [250000, 260000, 275000, 290000, 305000, 320000], borderColor: '#64748b', backgroundColor: 'rgba(100,116,139,0.05)', fill: true, tension: 0.2 }
              ]
            },
            options: { responsive: true, maintainAspectRatio: false }
          });
        }

        function renderGraficoRubros() {
          const ctx = document.getElementById('rubroChart');
          if (!ctx) return;
          const ultimoFecha = datosDetalle.length > 0 ? datosDetalle[datosDetalle.length - 1].fecha : null;
          const itemsUltimo = datosDetalle.filter(d => !ultimoFecha || d.fecha === ultimoFecha);
          
          const rubrosMap = {};
          itemsUltimo.forEach(d => {
            const r = d.rubro || 'Otros';
            const costo = Number(d.costo_mensual_ae || 0);
            rubrosMap[r] = (rubrosMap[r] || 0) + costo;
          });

          const labels = Object.keys(rubrosMap);
          const data = Object.values(rubrosMap);

          new Chart(ctx, {
            type: 'doughnut',
            data: {
              labels: labels.length ? labels : ['Carnes', 'Almacén', 'Lácteos', 'Verduras'],
              datasets: [{ data: data.length ? data : [40, 30, 20, 10], backgroundColor: ['#1e293b', '#334155', '#475569', '#64748b', '#94a3b8', '#cbd5e1'] }]
            },
            options: { responsive: true, maintainAspectRatio: false }
          });
        }

        function renderGraficoCobertura() {
          const ctx = document.getElementById('coberturaChart');
          if (!ctx) return;
          const labels = datosTotales.map(d => d.fecha);
          const cobertura = datosTotales.map(d => Number(d.cobertura_scraper_pct || 0));

          new Chart(ctx, {
            type: 'bar',
            data: {
              labels: labels.length ? labels : ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
              datasets: [{ label: 'Cobertura Scraper (%)', data: cobertura.length ? cobertura : [85, 88, 90, 92, 95, 96], backgroundColor: '#334155' }]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { max: 100 } } }
          });
        }

        function renderGraficoNutricional() {
          const ctx = document.getElementById('nutricionalChart');
          if (!ctx) return;
          const ultimoFecha = datosNutricional.length > 0 ? datosNutricional[datosNutricional.length - 1].fecha : null;
          const items = datosNutricional.filter(d => !ultimoFecha || d.fecha === ultimoFecha).slice(0, 10);

          const labels = items.map(d => d.producto);
          const kcal = items.map(d => Number(d.kcal_diarias_ae || 0));

          new Chart(ctx, {
            type: 'bar',
            data: {
              labels: labels.length ? labels : ['Pan', 'Arroz', 'Leche', 'Carne'],
              datasets: [{ label: 'Kcal Diarias AE', data: kcal.length ? kcal : [200, 150, 180, 220], backgroundColor: '#475569' }]
            },
            options: { responsive: true, maintainAspectRatio: false }
          });
        }

        function renderTablaTotales() {
          const container = document.getElementById('tabla-totales-container');
          if (!datosTotales.length) {
            container.innerHTML = '<p style="padding: 16px; color: var(--sub);">No hay datos de totales disponibles.</p>';
            return;
          }
          let html = '<table><thead><tr><th>Fecha</th><th>Prod. Reales</th><th>Prod. Total</th><th>Cobertura (%)</th><th>CBA AE</th><th>CBA Hogar</th><th>CBT Hogar</th></tr></thead><tbody>';
          datosTotales.forEach(row => {
            html += `<tr>
              <td>${row.fecha}</td>
              <td>${row.prod_real}</td>
              <td>${row.prod_total}</td>
              <td>${Number(row.cobertura_scraper_pct || 0).toFixed(1)}%</td>
              <td>${formatearMoneda(Number(row.costo_total_cba_ae || 0))}</td>
              <td>${formatearMoneda(Number(row.costo_total_cba_hogar || 0))}</td>
              <td>${formatearMoneda(Number(row.costo_total_cbt_hogar || 0))}</td>
            </tr>`;
          });
          html += '</tbody></table>';
          container.innerHTML = html;
        }

        function poblarFiltroRubros() {
          const select = document.getElementById('filtro-rubro-nutricional');
          const rubros = [...new Set(datosNutricional.map(d => d.rubro))].filter(Boolean);
          rubros.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r;
            opt.innerText = r;
            select.appendChild(opt);
          });
        }

        function filtrarNutricional() {
          const val = document.getElementById('filtro-rubro-nutricional').value;
          const filtrados = val === 'todos' ? datosNutricional : datosNutricional.filter(d => d.rubro === val);
          renderTablaNutricional(filtrados);
        }

        function renderTablaNutricional(items) {
          const container = document.getElementById('tabla-nutricional-container');
          if (!items.length) {
            container.innerHTML = '<p style="padding: 16px; color: var(--sub);">No hay información nutricional disponible.</p>';
            return;
          }
          let html = '<table><thead><tr><th>Rubro</th><th>Producto</th><th>Cantidad AE</th><th>Kcal Diarias</th><th>Proteínas (g)</th><th>Carbohidratos (g)</th><th>Grasas (g)</th></tr></thead><tbody>';
          items.forEach(row => {
            html += `<tr>
              <td>${row.rubro || ''}</td>
              <td>${row.producto || ''}</td>
              <td>${Number(row.cantidad_ae || 0).toFixed(3)}</td>
              <td>${Number(row.kcal_diarias_ae || 0).toFixed(1)}</td>
              <td>${Number(row.prot_diarias_g || 0).toFixed(1)}</td>
              <td>${Number(row.carb_diarios_g || 0).toFixed(1)}</td>
              <td>${Number(row.grasas_diarias_g || 0).toFixed(1)}</td>
            </tr>`;
          });
          html += '</tbody></table>';
          container.innerHTML = html;
        }

        function renderTablaHistorico() {
          const container = document.getElementById('tabla-historico-container');
          if (!datosDetalle.length) {
            container.innerHTML = '<p style="padding: 16px; color: var(--sub);">No hay histórico detallado disponible.</p>';
            return;
          }
          let html = '<table><thead><tr><th>Fecha</th><th>Rubro</th><th>Producto</th><th>Precio Estimado</th><th>Método</th><th>Costo Hogar</th></tr></thead><tbody>';
          datosDetalle.forEach(row => {
            html += `<tr>
              <td>${row.fecha}</td>
              <td>${row.rubro}</td>
              <td>${row.producto}</td>
              <td>${formatearMoneda(Number(row.precio_unitario_estimado || 0))}</td>
              <td>${row.metodo_calculo}</td>
              <td>${formatearMoneda(Number(row.costo_hogar_tipo || 0))}</td>
            </tr>`;
          });
          html += '</tbody></table>';
          container.innerHTML = html;
        }

        window.addEventListener('DOMContentLoaded', cargarDatos);
      </script>
    </body>
    </html>
    """
