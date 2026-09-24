import os
import re
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import cloudscraper
import numpy as np

COEFICIENTE_HOGAR_TIPO = 3.09

# ------------------------------------------------------------------------------
# CANASTA BÁSICA ALIMENTARIA COMPLETA (INDEC) CON PRECIOS OFICIALES DE REFERENCIA
# (Precios orientativos actualizados por unidad/kg/litro)
# ------------------------------------------------------------------------------
CBA_INDEC = [
    # --- PANADERÍA Y CEREALES ---
    {"rubro": "Panadería", "producto": "Pan francés", "keywords": ["pan frances", "pan kg"], "precio_indec": 2400.0, "cantidad_ae": 6.75, "kcal_100g": 265, "prot_100g": 9.0, "carb_100g": 55.0, "grasas_100g": 1.2},
    {"rubro": "Panadería", "producto": "Galletitas de agua", "keywords": ["galletitas agua", "galleta agua"], "precio_indec": 3800.0, "cantidad_ae": 0.42, "kcal_100g": 420, "prot_100g": 9.5, "carb_100g": 68.0, "grasas_100g": 12.0},
    {"rubro": "Panadería", "producto": "Galletitas dulces", "keywords": ["galletitas dulces", "galleta dulce"], "precio_indec": 4200.0, "cantidad_ae": 0.21, "kcal_100g": 450, "prot_100g": 6.5, "carb_100g": 72.0, "grasas_100g": 15.0},
    {"rubro": "Almacén", "producto": "Harina de trigo 000", "keywords": ["harina trigo 000", "harina 000"], "precio_indec": 1200.0, "cantidad_ae": 1.08, "kcal_100g": 340, "prot_100g": 10.0, "carb_100g": 72.0, "grasas_100g": 1.2},
    {"rubro": "Almacén", "producto": "Arroz blanco", "keywords": ["arroz blanco 1kg", "arroz 1kg"], "precio_indec": 2800.0, "cantidad_ae": 1.20, "kcal_100g": 354, "prot_100g": 7.0, "carb_100g": 78.0, "grasas_100g": 0.6},
    {"rubro": "Almacén", "producto": "Fideos secos", "keywords": ["fideos secos 500g", "fideos guiseros", "tallarines"], "precio_indec": 2200.0, "cantidad_ae": 1.74, "kcal_100g": 355, "prot_100g": 12.0, "carb_100g": 73.0, "grasas_100g": 1.5},
    {"rubro": "Almacén", "producto": "Harina de maíz (Polenta)", "keywords": ["polenta", "harina de maiz"], "precio_indec": 1800.0, "cantidad_ae": 0.21, "kcal_100g": 350, "prot_100g": 8.0, "carb_100g": 76.0, "grasas_100g": 1.0},

    # --- PAPA Y BATATA ---
    {"rubro": "Frutas y Verduras", "producto": "Papa blanca", "keywords": ["papa blanca", "papa x kg"], "precio_indec": 1200.0, "cantidad_ae": 6.51, "kcal_100g": 80, "prot_100g": 2.0, "carb_100g": 18.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Batata", "keywords": ["batata"], "precio_indec": 1600.0, "cantidad_ae": 0.51, "kcal_100g": 86, "prot_100g": 1.6, "carb_100g": 20.0, "grasas_100g": 0.1},

    # --- AZÚCAR Y DULCES ---
    {"rubro": "Almacén", "producto": "Azúcar", "keywords": ["azucar 1kg", "azucar blanca"], "precio_indec": 1400.0, "cantidad_ae": 1.23, "kcal_100g": 387, "prot_100g": 0.0, "carb_100g": 100.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Dulce de leche", "keywords": ["dulce de leche 400g", "dulce de leche"], "precio_indec": 3800.0, "cantidad_ae": 0.11, "kcal_100g": 315, "prot_100g": 6.0, "carb_100g": 55.0, "grasas_100g": 7.5},

    # --- CARNES Y DERIVADOS ---
    {"rubro": "Carnes", "producto": "Asado con hueso", "keywords": ["asado kg", "asado de tira"], "precio_indec": 9500.0, "cantidad_ae": 0.70, "kcal_100g": 250, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 20.0},
    {"rubro": "Carnes", "producto": "Carnaza común / Picada", "keywords": ["carne picada kg", "picada comun"], "precio_indec": 7200.0, "cantidad_ae": 1.20, "kcal_100g": 210, "prot_100g": 19.5, "carb_100g": 0.0, "grasas_100g": 14.0},
    {"rubro": "Carnes", "producto": "Pollo entero", "keywords": ["pollo entero kg", "pollo fresco"], "precio_indec": 3800.0, "cantidad_ae": 1.67, "kcal_100g": 170, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 11.0},

    # --- LÁCTEOS Y HUEVOS ---
    {"rubro": "Lácteos y Huevos", "producto": "Huevos (docena)", "keywords": ["huevos docena", "maple huevos", "huevos x 12"], "precio_indec": 3800.0, "cantidad_ae": 0.60, "kcal_100g": 150, "prot_100g": 12.5, "carb_100g": 0.7, "grasas_100g": 10.0},
    {"rubro": "Lácteos y Huevos", "producto": "Leche entera", "keywords": ["leche entera 1l", "leche sachet 1l"], "precio_indec": 1650.0, "cantidad_ae": 9.27, "kcal_100g": 60, "prot_100g": 3.1, "carb_100g": 4.7, "grasas_100g": 3.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso cuartirolo / cremoso", "keywords": ["queso cremoso kg", "queso cuartirolo"], "precio_indec": 9800.0, "cantidad_ae": 0.15, "kcal_100g": 310, "prot_100g": 18.0, "carb_100g": 1.5, "grasas_100g": 26.0},

    # --- ACEITES Y BEBIDAS ---
    {"rubro": "Almacén", "producto": "Aceite de girasol", "keywords": ["aceite girasol 900", "aceite girasol 1l"], "precio_indec": 3200.0, "cantidad_ae": 1.20, "kcal_100g": 884, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 100.0},
    {"rubro": "Almacén", "producto": "Yerba mate", "keywords": ["yerba mate 1kg", "yerba mate 500g"], "precio_indec": 4200.0, "cantidad_ae": 0.51, "kcal_100g": 30, "prot_100g": 1.0, "carb_100g": 6.0, "grasas_100g": 0.0}
]

def extraer_factor_unidad(texto):
    """
    Detecta la cantidad/unidad en el texto comercial y devuelve el factor 
    para escalar el precio a 1 Kilogramo o 1 Litro (ej: 500g -> factor 0.5 -> precio / 0.5).
    """
    texto = texto.lower()
    
    # 1. Búsqueda de Kilos o Litros directos: "1.5 kg", "1kg", "2 l", "1.5l"
    match_kgl = re.search(r'(\d+(?:[\.,]\d+)?)\s*(kg|kilo|kilos|l|lt|litro|litros)\b', texto)
    if match_kgl:
        val = float(match_kgl.group(1).replace(',', '.'))
        return val if val > 0 else 1.0

    # 2. Búsqueda de Gramos, Millilitros o CC: "500g", "900 ml", "750 cc", "400 gr"
    match_gml = re.search(r'(\d+(?:[\.,]\d+)?)\s*(g|gr|grs|gramos|ml|cc)\b', texto)
    if match_gml:
        val = float(match_gml.group(1).replace(',', '.'))
        return (val / 1000.0) if val > 0 else 1.0

    # 3. Unidades especiales (ej: maple de 30 huevos -> 2.5 docenas)
    if 'maple' in texto or '30' in texto:
        return 2.5

    return 1.0  # Asunción por defecto (1 kg / 1 L)

def extraer_observaciones_raw(scraper, item_config, fecha, timestamp, max_paginas=3):
    observaciones = []
    textos_vistos = set()

    rubro = item_config['rubro']
    producto = item_config['producto']
    keywords = item_config.get('keywords', [])

    for kw in keywords:
        if not kw:
            continue

        for pagina in range(1, max_paginas + 1):
            search_url = f"https://depotexpress.com.ar/?s={kw}&post_type=product&paged={pagina}"

            try:
                res = scraper.get(search_url, timeout=20)
                if res.status_code != 200:
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.select('.product, .type-product, div.item-producto, article')

                if not items:
                    break

                nuevas_obs_pagina = 0

                for item in items:
                    texto = item.get_text(separator=' ', strip=True)

                    if texto in textos_vistos:
                        continue

                    textos_vistos.add(texto)

                    coincidencia = re.search(r'\$\s*([\d\.\,]+)', texto)

                    if coincidencia:
                        precio_raw = coincidencia.group(1)
                        limpio = re.sub(r'[^\d,\.]', '', precio_raw)
                        if ',' in limpio and '.' in limpio:
                            limpio = limpio.replace('.', '').replace(',', '.')
                        elif ',' in limpio:
                            limpio = limpio.replace(',', '.')

                        try:
                            valor_publicado = float(limpio)
                            factor_unidad = extraer_factor_unidad(texto)
                            precio_normalizado_kgl = valor_publicado / factor_unidad

                            if 200 < precio_normalizado_kgl < 300000:
                                observaciones.append({
                                    'fecha': fecha,
                                    'timestamp': timestamp,
                                    'rubro': rubro,
                                    'producto': producto,
                                    'keyword_usada': kw,
                                    'descripcion_producto': texto[:80],
                                    'precio_publicado': valor_publicado,
                                    'factor_unidad': factor_unidad,
                                    'precio': precio_normalizado_kgl  # Guardamos el precio normalizado por KG/L
                                })
                                nuevas_obs_pagina += 1
                        except ValueError:
                            continue

                if nuevas_obs_pagina == 0:
                    break

                time.sleep(0.3)

            except Exception as e:
                print(f"Error scraping '{kw}' (Pág {pagina}): {e}")
                break

    return observaciones

def main():
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y-%m-%d %H:%M:%S")

    print(f"=== INICIANDO SCRAPING NORMALIZADO X KG/L ({timestamp}) ===")
    
    todas_observaciones_raw = []
    resumen_productos = []

    for item in CBA_INDEC:
        obs = extraer_observaciones_raw(scraper, item, fecha_hoy, timestamp)
        registro = item.copy()
        precio_indec = item.get("precio_indec", 0.0)

        # --------------------------------------------------------------------------
        # FILTRADO Y SELECCIÓN REPRESENTATIVA (BANDA DE TOLERANCIA + MEDIANA)
        # --------------------------------------------------------------------------
        obs_validas = []
        if precio_indec > 0 and obs:
            p_min = precio_indec * 0.50
            p_max = precio_indec * 2.20
            obs_validas = [o for o in obs if p_min <= o['precio'] <= p_max]
        elif obs:
            obs_validas = obs

        if obs_validas:
            # Seleccionar la Mediana para evitar sesgos de promociones puntuales o unidades pequeñas
            precios_normalizados = [o['precio'] for o in obs_validas]
            precio_final = float(np.median(precios_normalizados))
            metodo_calculo = "Mediana Normalizada (Scraping)"
            coincidencias = len(obs_validas)
            
            # Guardamos la observación representativa más cercana a la mediana
            obs_representativa = min(obs_validas, key=lambda x: abs(x['precio'] - precio_final))
            todas_observaciones_raw.append(obs_representativa)
        else:
            if precio_indec > 0:
                precio_final = precio_indec
                metodo_calculo = "Referencia Oficial INDEC"
            else:
                precio_final = 0.0
                metodo_calculo = "Sin datos"
            coincidencias = 0

        registro.update({
            'fecha': fecha_hoy,
            'timestamp': timestamp,
            'precio_unitario_estimado': precio_final,
            'coincidencias': coincidencias,
            'metodo_calculo': metodo_calculo
        })
        resumen_productos.append(registro)
        print(f"-> Rubro: '{item['rubro']}' | Producto: '{item['producto']}' | Precio/kg-L: ${precio_final:,.2f} ({metodo_calculo})")

    df_resumen = pd.DataFrame(resumen_productos)

    # Cálculo de Totales
    df_resumen['costo_mensual_ae'] = df_resumen['cantidad_ae'] * df_resumen['precio_unitario_estimado']
    df_resumen['costo_hogar_tipo'] = df_resumen['costo_mensual_ae'] * COEFICIENTE_HOGAR_TIPO

    costo_total_ae = df_resumen['costo_mensual_ae'].sum()
    costo_total_hogar = costo_total_ae * COEFICIENTE_HOGAR_TIPO

    # Resumen por consola
    print("\n" + "="*95)
    print("RESUMEN DE RESULTADOS RECALCULADOS (NORMALIZADOS X KG/L)")
    print("="*95)
    print(f"✅ Costo Total Adulto Equivalente (AE): ${costo_total_ae:,.2f}")
    print(f"✅ Costo Total Hogar Tipo (3.09 AE):     ${costo_total_hogar:,.2f}")
    print("="*95)

if __name__ == "__main__":
    main()
