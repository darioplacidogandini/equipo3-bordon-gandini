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
# CANASTA BÁSICA ALIMENTARIA COMPLETA (INDEC) - PRECIOS BASE ACTUALIZADOS
# Cantidades expresadas en kg / litros por Adulto Equivalente (AE)
# ------------------------------------------------------------------------------
CBA_INDEC = [
    # --- PANADERÍA Y CEREALES ---
    {"rubro": "Panadería", "producto": "Pan francés", "keywords": ["pan frances", "pan kg", "pani"], "precio_indec": 4500.0, "cantidad_ae": 6.750, "kcal_100g": 265, "prot_100g": 9.0, "carb_100g": 55.0, "grasas_100g": 1.2},
    {"rubro": "Panadería", "producto": "Galletitas de agua", "keywords": ["galletitas agua", "galleta agua", "gals"], "precio_indec": 6800.0, "cantidad_ae": 0.420, "kcal_100g": 420, "prot_100g": 9.5, "carb_100g": 68.0, "grasas_100g": 12.0},
    {"rubro": "Panadería", "producto": "Galletitas dulces", "keywords": ["galletitas dulces", "galleta dulce", "gald"], "precio_indec": 7500.0, "cantidad_ae": 0.210, "kcal_100g": 450, "prot_100g": 6.5, "carb_100g": 72.0, "grasas_100g": 15.0},
    {"rubro": "Almacén", "producto": "Arroz blanco", "keywords": ["arroz blanco 1kg", "arroz 1kg", "arr"], "precio_indec": 3800.0, "cantidad_ae": 1.200, "kcal_100g": 354, "prot_100g": 7.0, "carb_100g": 78.0, "grasas_100g": 0.6},
    {"rubro": "Almacén", "producto": "Harina de trigo 000", "keywords": ["harina trigo 000", "harina 000"], "precio_indec": 2200.0, "cantidad_ae": 1.080, "kcal_100g": 340, "prot_100g": 10.0, "carb_100g": 72.0, "grasas_100g": 1.2},
    {"rubro": "Almacén", "producto": "Otras harinas (maíz / Polenta)", "keywords": ["polenta", "harina de maiz", "harm"], "precio_indec": 2800.0, "cantidad_ae": 0.210, "kcal_100g": 350, "prot_100g": 8.0, "carb_100g": 76.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Fideos secos", "keywords": ["fideos secos 500g", "fideos guiseros", "tallarines", "fido"], "precio_indec": 3800.0, "cantidad_ae": 1.740, "kcal_100g": 355, "prot_100g": 12.0, "carb_100g": 73.0, "grasas_100g": 1.5},

    # --- VERDURAS, TUBÉRCULOS Y FRUTAS ---
    {"rubro": "Frutas y Verduras", "producto": "Papa blanca", "keywords": ["papa blanca", "papa x kg"], "precio_indec": 1800.0, "cantidad_ae": 6.510, "kcal_100g": 80, "prot_100g": 2.0, "carb_100g": 18.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Batata", "keywords": ["batata"], "precio_indec": 2500.0, "cantidad_ae": 0.510, "kcal_100g": 86, "prot_100g": 1.6, "carb_100g": 20.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Hortalizas (cebolla, tomate, zanahoria, zapallo, etc.)", "keywords": ["cebolla kg", "tomate kg", "zanahoria kg", "zapallo kg", "acelga"], "precio_indec": 2200.0, "cantidad_ae": 5.730, "kcal_100g": 30, "prot_100g": 1.2, "carb_100g": 6.0, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Frutas (manzana, naranja, banana, pera)", "keywords": ["manzana kg", "naranja kg", "banana kg", "pera kg"], "precio_indec": 2800.0, "cantidad_ae": 4.950, "kcal_100g": 52, "prot_100g": 0.5, "carb_100g": 13.5, "grasas_100g": 0.2},

    # --- AZÚCAR, DULCES Y LEGUMBRES ---
    {"rubro": "Almacén", "producto": "Azúcar", "keywords": ["azucar 1kg", "azucar blanca", "azuc"], "precio_indec": 2000.0, "cantidad_ae": 1.230, "kcal_100g": 387, "prot_100g": 0.0, "carb_100g": 100.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Dulces (dulce de leche, mermelada, batata)", "keywords": ["dulce de leche", "mermelada", "dulce de batata", "dulce leche"], "precio_indec": 6500.0, "cantidad_ae": 0.330, "kcal_100g": 315, "prot_100g": 4.0, "carb_100g": 60.0, "grasas_100g": 5.0},
    {"rubro": "Almacén", "producto": "Legumbres secas (lentejas, arvejas)", "keywords": ["lentejas 500g", "arvejas 500g", "lentejas", "legu"], "precio_indec": 4200.0, "cantidad_ae": 0.240, "kcal_100g": 340, "prot_100g": 24.0, "carb_100g": 60.0, "grasas_100g": 1.0},

    # --- CARNES, MENUDENCIAS Y FIAMBRES ---
    {"rubro": "Carnes", "producto": "Carnes (asado, picada, paleta, nalga, pollo, pescado)", "keywords": ["carne picada", "asado kg", "nalga kg", "paleta kg", "pollo entero kg"], "precio_indec": 13500.0, "cantidad_ae": 6.270, "kcal_100g": 210, "prot_100g": 19.0, "carb_100g": 0.0, "grasas_100g": 14.0},
    {"rubro": "Carnes", "producto": "Menudencias (hígado)", "keywords": ["higado kg", "higado de vacuno"], "precio_indec": 5500.0, "cantidad_ae": 0.270, "kcal_100g": 135, "prot_100g": 20.0, "carb_100g": 3.8, "grasas_100g": 4.0},
    {"rubro": "Carnes", "producto": "Fiambres (paleta cocida, salame)", "keywords": ["paleta cocida", "salame"], "precio_indec": 15000.0, "cantidad_ae": 0.060, "kcal_100g": 300, "prot_100g": 16.0, "carb_100g": 2.0, "grasas_100g": 25.0},

    # --- LÁCTEOS Y HUEVOS ---
    {"rubro": "Lácteos y Huevos", "producto": "Huevos (docena)", "keywords": ["huevos docena", "maple huevos", "huevos x 12"], "precio_indec": 6000.0, "cantidad_ae": 0.600, "kcal_100g": 150, "prot_100g": 12.5, "carb_100g": 0.7, "grasas_100g": 10.0},
    {"rubro": "Lácteos y Huevos", "producto": "Leche entera", "keywords": ["leche entera 1l", "leche sachet 1l"], "precio_indec": 2400.0, "cantidad_ae": 9.270, "kcal_100g": 60, "prot_100g": 3.1, "carb_100g": 4.7, "grasas_100g": 3.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso (cremoso, cuartirolo, de rallar)", "keywords": ["queso cremoso kg", "queso cuartirolo", "queso rallar"], "precio_indec": 16000.0, "cantidad_ae": 0.330, "kcal_100g": 320, "prot_100g": 20.0, "carb_100g": 1.5, "grasas_100g": 26.0},
    {"rubro": "Lácteos y Huevos", "producto": "Yogur", "keywords": ["yogur entero", "yogur sachet", "yogur firm"], "precio_indec": 3800.0, "cantidad_ae": 0.570, "kcal_100g": 65, "prot_100g": 3.2, "carb_100g": 9.0, "grasas_100g": 2.5},
    {"rubro": "Lácteos y Huevos", "producto": "Manteca", "keywords": ["manteca 200g", "manteca 100g"], "precio_indec": 16000.0, "cantidad_ae": 0.060, "kcal_100g": 717, "prot_100g": 0.9, "carb_100g": 0.1, "grasas_100g": 81.0},

    # --- ACEITES, CONDIMENTOS Y BEBIDAS ---
    {"rubro": "Almacén", "producto": "Aceite de girasol", "keywords": ["aceite girasol 900", "aceite girasol 1l"], "precio_indec": 4800.0, "cantidad_ae": 1.200, "kcal_100g": 884, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 100.0},
    {"rubro": "Bebidas", "producto": "Bebidas no alcohólicas (gaseosas, jugos, soda)", "keywords": ["gaseosa 1.5l", "gaseosa 2l", "jugo concentrado", "soda 1.5l"], "precio_indec": 3200.0, "cantidad_ae": 3.450, "kcal_100g": 35, "prot_100g": 0.0, "carb_100g": 9.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Bebidas alcohólicas (cerveza, vino)", "keywords": ["cerveza 1l", "vino tinto 1l"], "precio_indec": 4500.0, "cantidad_ae": 1.080, "kcal_100g": 60, "prot_100g": 0.3, "carb_100g": 3.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Sal fina", "keywords": ["sal fina 500g", "sal fina 1kg"], "precio_indec": 1500.0, "cantidad_ae": 0.120, "kcal_100g": 0, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Condimentos (mayonesa, caldos)", "keywords": ["mayonesa", "caldo de verdura", "caldo de gallina"], "precio_indec": 7500.0, "cantidad_ae": 0.120, "kcal_100g": 350, "prot_100g": 1.0, "carb_100g": 10.0, "grasas_100g": 35.0},
    {"rubro": "Almacén", "producto": "Vinagre", "keywords": ["vinagre de alcohol", "vinagre de manzana"], "precio_indec": 2200.0, "cantidad_ae": 0.060, "kcal_100g": 18, "prot_100g": 0.0, "carb_100g": 0.1, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Café", "keywords": ["cafe molido", "cafe instantaneo"], "precio_indec": 32000.0, "cantidad_ae": 0.030, "kcal_100g": 200, "prot_100g": 14.0, "carb_100g": 40.0, "grasas_100g": 0.2},
    {"rubro": "Almacén", "producto": "Yerba mate", "keywords": ["yerba mate 1kg", "yerba mate 500g"], "precio_indec": 6500.0, "cantidad_ae": 0.510, "kcal_100g": 30, "prot_100g": 1.0, "carb_100g": 6.0, "grasas_100g": 0.0}
]

def extraer_factor_unidad(texto):
    texto = texto.lower()
    
    match_kgl = re.search(r'(\d+(?:[\.,]\d+)?)\s*(kg|kilo|kilos|l|lt|litro|litros)\b', texto)
    if match_kgl:
        val = float(match_kgl.group(1).replace(',', '.'))
        return val if val > 0 else 1.0

    match_gml = re.search(r'(\d+(?:[\.,]\d+)?)\s*(g|gr|grs|gramos|ml|cc)\b', texto)
    if match_gml:
        val = float(match_gml.group(1).replace(',', '.'))
        return (val / 1000.0) if val > 0 else 1.0

    if 'maple' in texto or '30' in texto:
        return 2.5

    return 1.0

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

                            if 200 < precio_normalizado_kgl < 500000:
                                observaciones.append({
                                    'fecha': fecha,
                                    'timestamp': timestamp,
                                    'rubro': rubro,
                                    'producto': producto,
                                    'keyword_usada': kw,
                                    'descripcion_producto': texto[:80],
                                    'precio_publicado': valor_publicado,
                                    'factor_unidad': factor_unidad,
                                    'precio': precio_normalizado_kgl
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

        obs_validas = []
        # FILTRO FLEXIBILIZADO: Acepta variaciones entre 30% y 350% respecto al valor base
        if precio_indec > 0 and obs:
            p_min = precio_indec * 0.30
            p_max = precio_indec * 3.50
            obs_validas = [o for o in obs if p_min <= o['precio'] <= p_max]
        elif obs:
            obs_validas = obs

        if obs_validas:
            precios_normalizados = [o['precio'] for o in obs_validas]
            precio_final = float(np.median(precios_normalizados))
            metodo_calculo = "Mediana Normalizada (Scraping)"
            coincidencias = len(obs_validas)
            
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

    # 1. Guardar detalle de productos por fecha
    archivo_detalle = "cba_historico_detalle.csv"
    if 'keywords' in df_resumen.columns:
        df_resumen_csv = df_resumen.drop(columns=['keywords'])
    else:
        df_resumen_csv = df_resumen.copy()

    if os.path.exists(archivo_detalle):
        df_resumen_csv.to_csv(archivo_detalle, mode='a', header=False, index=False, encoding="utf-8-sig")
        print(f"📁 Registros añadidos a '{archivo_detalle}'.")
    else:
        df_resumen_csv.to_csv(archivo_detalle, index=False, encoding="utf-8-sig")
        print(f"📁 Archivo '{archivo_detalle}' creado exitosamente.")

    # 2. Guardar resumen de totales acumulados
    archivo_totales = "cba_historico_totales.csv"
    df_totales = pd.DataFrame([{
        'fecha': fecha_hoy,
        'timestamp': timestamp,
        'costo_total_ae': costo_total_ae,
        'costo_total_hogar': costo_total_hogar
    }])

    if os.path.exists(archivo_totales):
        df_totales.to_csv(archivo_totales, mode='a', header=False, index=False, encoding="utf-8-sig")
        print(f"📁 Registros añadidos a '{archivo_totales}'.")
    else:
        df_totales.to_csv(archivo_totales, index=False, encoding="utf-8-sig")
        print(f"📁 Archivo '{archivo_totales}' creado exitosamente.")

    # 3. Guardar desglose nutricional
    archivo_nutricional = "cba_tabla_nutricional.csv"
    cols_nutricion = ['fecha', 'timestamp', 'rubro', 'producto', 'cantidad_ae', 'kcal_100g', 'prot_100g', 'carb_100g', 'grasas_100g', 'costo_mensual_ae']
    df_nutricional = df_resumen[cols_nutricion]

    if os.path.exists(archivo_nutricional):
        df_nutricional.to_csv(archivo_nutricional, mode='a', header=False, index=False, encoding="utf-8-sig")
        print(f"📁 Registros añadidos a '{archivo_nutricional}'.")
    else:
        df_nutricional.to_csv(archivo_nutricional, index=False, encoding="utf-8-sig")
        print(f"📁 Archivo '{archivo_nutricional}' creado exitosamente.")

if __name__ == "__main__":
    main()
