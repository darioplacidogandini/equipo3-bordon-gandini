import os
import re
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import cloudscraper

COEFICIENTE_HOGAR_TIPO = 3.09

# ------------------------------------------------------------------------------
# DEFINICIÓN DETALLADA DE LA CANASTA BÁSICA ALIMENTARIA (INDEC - 1 ADULTO EQUIV)
# Cantidades mensuales estimadas por rubro/corte específico
# ------------------------------------------------------------------------------
CBA_INDEC = [
    # --- PAN Y CEREALES ---
    {"rubro": "Pan francés", "cantidad_ae": 6.30, "keyword": "pan frances"},
    {"rubro": "Galletitas de agua", "cantidad_ae": 1.29, "keyword": "galletitas agua"},
    {"rubro": "Galletitas dulces", "cantidad_ae": 0.60, "keyword": "galletitas dulces"},
    {"rubro": "Harina de trigo 000", "cantidad_ae": 1.02, "keyword": "harina trigo 000"},
    {"rubro": "Arroz blanco", "cantidad_ae": 0.63, "keyword": "arroz blanco"},
    {"rubro": "Fideos secos / guiseros", "cantidad_ae": 1.29, "keyword": "fideos secos"},
    {"rubro": "Harina de maíz (Polenta)", "cantidad_ae": 0.30, "keyword": "polenta"},

    # --- CARNES Y DERIVADOS ---
    {"rubro": "Asado con hueso", "cantidad_ae": 0.70, "keyword": "asado"},
    {"rubro": "Carnaza común / Picada", "cantidad_ae": 1.50, "keyword": "carne picada"},
    {"rubro": "Nalga", "cantidad_ae": 1.20, "keyword": "nalga"},
    {"rubro": "Paleta", "cantidad_ae": 1.20, "keyword": "paleta"},
    {"rubro": "Cuadril", "cantidad_ae": 0.80, "keyword": "cuadril"},
    {"rubro": "Pollo entero", "cantidad_ae": 2.13, "keyword": "pollo entero"},
    {"rubro": "Pescado (Merluza)", "cantidad_ae": 0.40, "keyword": "merluza"},
    {"rubro": "Paleta cocida / Jamón", "cantidad_ae": 0.20, "keyword": "paleta cocida"},

    # --- LÁCTEOS Y HUEVOS ---
    {"rubro": "Leche entera fresca", "cantidad_ae": 7.95, "keyword": "leche entera sachet"},
    {"rubro": "Queso cremoso", "cantidad_ae": 0.30, "keyword": "queso cremoso"},
    {"rubro": "Queso rallar / Sardo", "cantidad_ae": 0.10, "keyword": "queso sardo"},
    {"rubro": "Yogur entero", "cantidad_ae": 0.60, "keyword": "yogur entero"},
    {"rubro": "Manteca", "cantidad_ae": 0.15, "keyword": "manteca"},
    {"rubro": "Huevos (docena)", "cantidad_ae": 0.60, "keyword": "huevos"},

    # --- FRUTAS Y VERDURAS ---
    {"rubro": "Papa blanca", "cantidad_ae": 7.05, "keyword": "papa blanca"},
    {"rubro": "Batata", "cantidad_ae": 0.50, "keyword": "batata"},
    {"rubro": "Cebolla", "cantidad_ae": 1.20, "keyword": "cebolla"},
    {"rubro": "Lechuga", "cantidad_ae": 0.60, "keyword": "lechuga"},
    {"rubro": "Tomate redondo", "cantidad_ae": 1.20, "keyword": "tomate redondo"},
    {"rubro": "Zanahoria", "cantidad_ae": 0.70, "keyword": "zanahoria"},
    {"rubro": "Zapallo Anco", "cantidad_ae": 0.80, "keyword": "zapallo anco"},
    {"rubro": "Manzana deliciosa", "cantidad_ae": 1.20, "keyword": "manzana"},
    {"rubro": "Banana", "cantidad_ae": 1.20, "keyword": "banana"},
    {"rubro": "Naranja", "cantidad_ae": 1.20, "keyword": "naranja"},

    # --- ACEITES, AZÚCAR Y ALMACÉN ---
    {"rubro": "Aceite de girasol", "cantidad_ae": 1.20, "keyword": "aceite girasol"},
    {"rubro": "Azúcar", "cantidad_ae": 1.20, "keyword": "azucar"},
    {"rubro": "Dulce de leche", "cantidad_ae": 0.30, "keyword": "dulce de leche"},
    {"rubro": "Mermelada", "cantidad_ae": 0.20, "keyword": "mermelada"},
    {"rubro": "Lentejas secas", "cantidad_ae": 0.20, "keyword": "lentejas"},
    {"rubro": "Yerba mate", "cantidad_ae": 0.60, "keyword": "yerba mate"},
    {"rubro": "Té en saquitos", "cantidad_ae": 0.05, "keyword": "te saquitos"},
    {"rubro": "Café", "cantidad_ae": 0.05, "keyword": "cafe molido"},
    {"rubro": "Sal fina", "cantidad_ae": 0.15, "keyword": "sal fina"}
]

def buscar_precio_promedio(scraper, keyword):
    search_url = f"https://depotexpress.com.ar/?s={keyword}&post_type=product"
    try:
        res = scraper.get(search_url, timeout=25)
        if res.status_code != 200:
            return None, 0

        soup = BeautifulSoup(res.text, 'html.parser')
        precios = []

        items = soup.select('.product, .type-product, div.item-producto, article')
        if not items:
            menciones = soup.find_all(string=lambda t: t and '$' in t)
            for m in menciones:
                padre = m.find_parent(['div', 'li', 'article'])
                if padre and padre not in items:
                    items.append(padre)

        for item in items:
            texto = item.get_text(separator=' ', strip=True)
            coincidencia = re.search(r'\$\s*([\d\.\,]+)', texto)

            if coincidencia:
                precio_raw = coincidencia.group(1)
                limpio = re.sub(r'[^\d,\.]', '', precio_raw)
                if ',' in limpio and '.' in limpio:
                    limpio = limpio.replace('.', '').replace(',', '.')
                elif ',' in limpio:
                    limpio = limpio.replace(',', '.')

                try:
                    valor = float(limpio)
                    if 100 < valor < 150000:
                        precios.append(valor)
                except ValueError:
                    continue

        if precios:
            return sum(precios) / len(precios), len(precios)
        return None, 0
    except Exception as e:
        print(f"Error scraping '{keyword}': {e}")
        return None, 0

def main():
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y-%m-%d %H:%M:%S")

    print(f"=== INICIANDO SCRAPING ({timestamp}) ===")
    resultados = []
    for item in CBA_INDEC:
        print(f"-> Buscando rubro: '{item['rubro']}'...")
        precio_prom, cant = buscar_precio_promedio(scraper, item['keyword'])
        resultados.append({
            'fecha': fecha_hoy,
            'timestamp': timestamp,
            'rubro': item['rubro'],
            'keyword': item['keyword'],
            'cantidad_ae': item['cantidad_ae'],
            'precio_unitario_estimado': precio_prom,
            'coincidencias': cant
        })
        time.sleep(1.2)

    df = pd.DataFrame(resultados)
    mediana = df['precio_unitario_estimado'].median()
    df['precio_unitario_estimado'] = df['precio_unitario_estimado'].fillna(mediana)

    # Cálculos
    df['costo_mensual_ae'] = df['cantidad_ae'] * df['precio_unitario_estimado']
    df['costo_hogar_tipo'] = df['costo_mensual_ae'] * COEFICIENTE_HOGAR_TIPO

    costo_total_ae = df['costo_mensual_ae'].sum()
    costo_total_hogar = costo_total_ae * COEFICIENTE_HOGAR_TIPO
    df['participacion_pct'] = (df['costo_mensual_ae'] / costo_total_ae) * 100

    # 1. Actualizar histórico detallado por rubro
    file_detalle = "cba_historico_detalle.csv"
    if os.path.exists(file_detalle):
        df_hist_det = pd.read_csv(file_detalle)
        df_det_final = pd.concat([df_hist_det, df], ignore_index=True)
    else:
        df_det_final = df

    df_det_final.to_csv(file_detalle, index=False, encoding='utf-8-sig')

    # 2. Actualizar histórico global diario
    file_totales = "cba_historico_totales.csv"
    df_totales_hoy = pd.DataFrame([{
        'fecha': fecha_hoy,
        'timestamp': timestamp,
        'costo_total_ae': costo_total_ae,
        'costo_total_hogar_tipo': costo_total_hogar
    }])

    if os.path.exists(file_totales):
        df_hist_tot = pd.read_csv(file_totales)
        df_tot_final = pd.concat([df_hist_tot, df_totales_hoy], ignore_index=True)
    else:
        df_tot_final = df_totales_hoy

    df_tot_final.to_csv(file_totales, index=False, encoding='utf-8-sig')

    print(f"✅ Scraping completado. Costo Total Hogar Tipo: ${costo_total_hogar:,.2f}")

if __name__ == "__main__":
    main()
