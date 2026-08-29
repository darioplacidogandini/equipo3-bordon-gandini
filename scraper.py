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
# ------------------------------------------------------------------------------
# CANASTA BÁSICA ALIMENTARIA CON VALORES NUTRICIONALES (por 100g / 100mL)
# ------------------------------------------------------------------------------

CBA_INDEC = [
    # --- PAN Y CEREALES ---
    {"rubro": "Pan francés", "cantidad_ae": 6.30, "keyword": "pan frances", "kcal_100g": 265, "prot_100g": 9.0, "carb_100g": 55.0, "grasas_100g": 1.2},
    {"rubro": "Galletitas de agua", "cantidad_ae": 1.29, "keyword": "galletitas agua", "kcal_100g": 420, "prot_100g": 9.5, "carb_100g": 68.0, "grasas_100g": 12.0},
    {"rubro": "Galletitas dulces", "cantidad_ae": 0.60, "keyword": "galletitas dulces", "kcal_100g": 450, "prot_100g": 6.5, "carb_100g": 72.0, "grasas_100g": 15.0},
    {"rubro": "Harina de trigo 000", "cantidad_ae": 1.02, "keyword": "harina trigo 000", "kcal_100g": 340, "prot_100g": 10.0, "carb_100g": 72.0, "grasas_100g": 1.2},
    {"rubro": "Arroz blanco", "cantidad_ae": 0.63, "keyword": "arroz blanco", "kcal_100g": 354, "prot_100g": 7.0, "carb_100g": 78.0, "grasas_100g": 0.6},
    {"rubro": "Fideos secos", "cantidad_ae": 1.29, "keyword": "fideos secos", "kcal_100g": 355, "prot_100g": 12.0, "carb_100g": 73.0, "grasas_100g": 1.5},
    {"rubro": "Harina de maíz (Polenta)", "cantidad_ae": 0.30, "keyword": "polenta", "kcal_100g": 350, "prot_100g": 8.0, "carb_100g": 76.0, "grasas_100g": 1.0},

    # --- CARNES Y DERIVADOS ---
    {"rubro": "Asado con hueso", "cantidad_ae": 0.70, "keyword": "asado", "kcal_100g": 250, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 20.0},
    {"rubro": "Carnaza común / Picada", "cantidad_ae": 1.50, "keyword": "carne picada", "kcal_100g": 210, "prot_100g": 19.5, "carb_100g": 0.0, "grasas_100g": 14.0},
    {"rubro": "Nalga", "cantidad_ae": 1.20, "keyword": "nalga", "kcal_100g": 135, "prot_100g": 21.0, "carb_100g": 0.0, "grasas_100g": 5.0},
    {"rubro": "Paleta", "cantidad_ae": 1.20, "keyword": "paleta", "kcal_100g": 145, "prot_100g": 20.0, "carb_100g": 0.0, "grasas_100g": 7.0},
    {"rubro": "Cuadril", "cantidad_ae": 0.80, "keyword": "cuadril", "kcal_100g": 140, "prot_100g": 21.5, "carb_100g": 0.0, "grasas_100g": 5.5},
    {"rubro": "Pollo entero", "cantidad_ae": 2.13, "keyword": "pollo entero", "kcal_100g": 170, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 11.0},
    {"rubro": "Pescado (Merluza)", "cantidad_ae": 0.40, "keyword": "merluza", "kcal_100g": 90, "prot_100g": 19.0, "carb_100g": 0.0, "grasas_100g": 1.2},
    {"rubro": "Paleta cocida / Jamón", "cantidad_ae": 0.20, "keyword": "paleta cocida", "kcal_100g": 130, "prot_100g": 16.0, "carb_100g": 2.0, "grasas_100g": 6.5},

    # --- LÁCTEOS Y HUEVOS ---
    {"rubro": "Leche entera fresca", "cantidad_ae": 7.95, "keyword": "leche entera sachet", "kcal_100g": 60, "prot_100g": 3.1, "carb_100g": 4.7, "grasas_100g": 3.0},
    {"rubro": "Queso cremoso", "cantidad_ae": 0.30, "keyword": "queso cremoso", "kcal_100g": 310, "prot_100g": 18.0, "carb_100g": 1.5, "grasas_100g": 26.0},
    {"rubro": "Queso sardo", "cantidad_ae": 0.10, "keyword": "queso sardo", "kcal_100g": 370, "prot_100g": 28.0, "carb_100g": 1.8, "grasas_100g": 28.0},
    {"rubro": "Yogur entero", "cantidad_ae": 0.60, "keyword": "yogur entero", "kcal_100g": 63, "prot_100g": 3.3, "carb_100g": 5.0, "grasas_100g": 3.2},
    {"rubro": "Manteca", "cantidad_ae": 0.15, "keyword": "manteca", "kcal_100g": 740, "prot_100g": 0.8, "carb_100g": 0.1, "grasas_100g": 82.0},
    {"rubro": "Huevos (unidades aprox)", "cantidad_ae": 0.60, "keyword": "huevos", "kcal_100g": 150, "prot_100g": 12.5, "carb_100g": 0.7, "grasas_100g": 10.0},

    # --- FRUTAS Y VERDURAS ---
    {"rubro": "Papa blanca", "cantidad_ae": 7.05, "keyword": "papa blanca", "kcal_100g": 80, "prot_100g": 2.0, "carb_100g": 18.0, "grasas_100g": 0.1},
    {"rubro": "Batata", "cantidad_ae": 0.50, "keyword": "batata", "kcal_100g": 86, "prot_100g": 1.6, "carb_100g": 20.0, "grasas_100g": 0.1},
    {"rubro": "Cebolla", "cantidad_ae": 1.20, "keyword": "cebolla", "kcal_100g": 40, "prot_100g": 1.1, "carb_100g": 9.0, "grasas_100g": 0.1},
    {"rubro": "Lechuga", "cantidad_ae": 0.60, "keyword": "lechuga", "kcal_100g": 15, "prot_100g": 1.3, "carb_100g": 2.8, "grasas_100g": 0.2},
    {"rubro": "Tomate redondo", "cantidad_ae": 1.20, "keyword": "tomate redondo", "kcal_100g": 18, "prot_100g": 0.9, "carb_100g": 3.9, "grasas_100g": 0.2},
    {"rubro": "Zanahoria", "cantidad_ae": 0.70, "keyword": "zanahoria", "kcal_100g": 41, "prot_100g": 0.9, "carb_100g": 9.5, "grasas_100g": 0.2},
    {"rubro": "Zapallo Anco", "cantidad_ae": 0.80, "keyword": "zapallo anco", "kcal_100g": 45, "prot_100g": 1.0, "carb_100g": 11.0, "grasas_100g": 0.1},
    {"rubro": "Manzana", "cantidad_ae": 1.20, "keyword": "manzana", "kcal_100g": 52, "prot_100g": 0.3, "carb_100g": 14.0, "grasas_100g": 0.2},
    {"rubro": "Banana", "cantidad_ae": 1.20, "keyword": "banana", "kcal_100g": 89, "prot_100g": 1.1, "carb_100g": 23.0, "grasas_100g": 0.3},
    {"rubro": "Naranja", "cantidad_ae": 1.20, "keyword": "naranja", "kcal_100g": 47, "prot_100g": 0.9, "carb_100g": 12.0, "grasas_100g": 0.1},

    # --- ACEITES, AZÚCAR Y ALMACÉN ---
    {"rubro": "Aceite de girasol", "cantidad_ae": 1.20, "keyword": "aceite girasol", "kcal_100g": 884, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 100.0},
    {"rubro": "Azúcar", "cantidad_ae": 1.20, "keyword": "azucar", "kcal_100g": 387, "prot_100g": 0.0, "carb_100g": 100.0, "grasas_100g": 0.0},
    {"rubro": "Dulce de leche", "cantidad_ae": 0.30, "keyword": "dulce de leche", "kcal_100g": 315, "prot_100g": 6.0, "carb_100g": 55.0, "grasas_100g": 7.5},
    {"rubro": "Mermelada", "cantidad_ae": 0.20, "keyword": "mermelada", "kcal_100g": 260, "prot_100g": 0.4, "carb_100g": 65.0, "grasas_100g": 0.1},
    {"rubro": "Lentejas secas", "cantidad_ae": 0.20, "keyword": "lentejas", "kcal_100g": 350, "prot_100g": 25.0, "carb_100g": 60.0, "grasas_100g": 1.0},
    {"rubro": "Yerba mate", "cantidad_ae": 0.60, "keyword": "yerba mate", "kcal_100g": 30, "prot_100g": 1.0, "carb_100g": 6.0, "grasas_100g": 0.0},
    {"rubro": "Té en saquitos", "cantidad_ae": 0.05, "keyword": "te saquitos", "kcal_100g": 1, "prot_100g": 0.0, "carb_100g": 0.2, "grasas_100g": 0.0},
    {"rubro": "Café molido", "cantidad_ae": 0.05, "keyword": "cafe molido", "kcal_100g": 2, "prot_100g": 0.1, "carb_100g": 0.3, "grasas_100g": 0.0},
    {"rubro": "Sal fina", "cantidad_ae": 0.15, "keyword": "sal fina", "kcal_100g": 0, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 0.0}
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
    # --------------------------------------------------------------------------
    # CÁLCULOS NUTRICIONALES Y CONSUMO INDIVIDUAL (DIARIO Y MENSUAL)
    # --------------------------------------------------------------------------
    # Consumo diario en gramos/mililitros por persona (1 Adulto Equivalente)
    df['consumo_mensual_kg_l'] = df['cantidad_ae']
    df['consumo_diario_g_ml'] = (df['cantidad_ae'] * 1000) / 30

    # Aporte nutricional diario por alimento
    df['kcal_diarias'] = (df['consumo_diario_g_ml'] * df['kcal_100g']) / 100
    df['proteinas_g_dia'] = (df['consumo_diario_g_ml'] * df['prot_100g']) / 100
    df['carbohidratos_g_dia'] = (df['consumo_diario_g_ml'] * df['carb_100g']) / 100
    df['grasas_g_dia'] = (df['consumo_diario_g_ml'] * df['grasas_100g']) / 100

    # Exportar archivo independiente de la Tabla Nutricional
    cols_nutricionales = [
        'rubro', 'consumo_mensual_kg_l', 'consumo_diario_g_ml',
        'kcal_diarias', 'proteinas_g_dia', 'carbohidratos_g_dia', 'grasas_g_dia'
    ]
    df_nutricion = df[cols_nutricionales].copy()

    # Fila resumen con el total de la dieta
    fila_total_nutr = pd.DataFrame([{
        'rubro': 'TOTAL DIARIO (1 ADULTO EQUIVALENTE)',
        'consumo_mensual_kg_l': df['consumo_mensual_kg_l'].sum(),
        'consumo_diario_g_ml': df['consumo_diario_g_ml'].sum(),
        'kcal_diarias': df['kcal_diarias'].sum(),
        'proteinas_g_dia': df['proteinas_g_dia'].sum(),
        'carbohidratos_g_dia': df['carbohidratos_g_dia'].sum(),
        'grasas_g_dia': df['grasas_g_dia'].sum()
    }])

    df_nutricion_final = pd.concat([df_nutricion, fila_total_nutr], ignore_index=True)
    df_nutricion_final.to_csv("cba_tabla_nutricional.csv", index=False, encoding='utf-8-sig')

    print(f"📊 Aporte energético total: {df['kcal_diarias'].sum():,.0f} kcal/día por persona.")
    
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
