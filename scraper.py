import os
import re
import time
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup
import cloudscraper
import numpy as np

# ------------------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN Y PONDERACIÓN
# ------------------------------------------------------------------------------
COEFICIENTE_HOGAR_TIPO = 3.09  # Equivalencia de integrantes en un hogar tipo según INDEC
INVERSO_COEFICIENTE_ENGEL = 2.25  # Coeficiente para estimar la CBT a partir de la CBA

# CANASTA BÁSICA ALIMENTARIA COMPLETA - PRODUCTOS DESAGREGADOS
CBA_INDEC = [
    # --- PANADERÍA Y CEREALES ---
    {"rubro": "Panadería", "producto": "Pan francés", "keywords": ["pan frances", "pan kg", "pani"], "cantidad_ae": 6.750, "kcal_100g": 265, "prot_100g": 9.0, "carb_100g": 55.0, "grasas_100g": 1.2},
    {"rubro": "Panadería", "producto": "Galletitas de agua", "keywords": ["galletitas agua", "galleta agua", "gals"], "cantidad_ae": 0.420, "kcal_100g": 420, "prot_100g": 9.5, "carb_100g": 68.0, "grasas_100g": 12.0},
    {"rubro": "Panadería", "producto": "Galletitas dulces", "keywords": ["galletitas dulces", "galleta dulce", "gald"], "cantidad_ae": 0.210, "kcal_100g": 450, "prot_100g": 6.5, "carb_100g": 72.0, "grasas_100g": 15.0},
    {"rubro": "Almacén", "producto": "Arroz blanco", "keywords": ["arroz blanco 1kg", "arroz 1kg", "arr", "arroz"], "cantidad_ae": 1.200, "kcal_100g": 354, "prot_100g": 7.0, "carb_100g": 78.0, "grasas_100g": 0.6},
    {"rubro": "Almacén", "producto": "Harina de trigo 000", "keywords": ["harina trigo 000", "harina 000", "harina", "hart"], "cantidad_ae": 1.080, "kcal_100g": 340, "prot_100g": 10.0, "carb_100g": 72.0, "grasas_100g": 1.2},
    {"rubro": "Almacén", "producto": "Harina de maíz / Polenta", "keywords": ["polenta", "harina de maiz", "harm"], "cantidad_ae": 0.210, "kcal_100g": 350, "prot_100g": 8.0, "carb_100g": 76.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Fideos secos", "keywords": ["fideos secos 500g", "fideos guiseros", "tallarines", "fido"], "cantidad_ae": 1.740, "kcal_100g": 355, "prot_100g": 12.0, "carb_100g": 73.0, "grasas_100g": 1.5},

    # --- VERDURAS, TUBÉRCULOS Y FRUTAS ---
    {"rubro": "Frutas y Verduras", "producto": "Papa blanca", "keywords": ["papa blanca", "papa x kg"], "cantidad_ae": 6.510, "kcal_100g": 80, "prot_100g": 2.0, "carb_100g": 18.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Batata", "keywords": ["batata"], "cantidad_ae": 0.510, "kcal_100g": 86, "prot_100g": 1.6, "carb_100g": 20.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Cebolla", "keywords": ["cebolla kg"], "cantidad_ae": 1.146, "kcal_100g": 40, "prot_100g": 1.1, "carb_100g": 9.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Tomate", "keywords": ["tomate kg"], "cantidad_ae": 1.146, "kcal_100g": 18, "prot_100g": 0.9, "carb_100g": 3.9, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Zanahoria", "keywords": ["zanahoria kg"], "cantidad_ae": 1.146, "kcal_100g": 41, "prot_100g": 0.9, "carb_100g": 9.6, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Zapallo", "keywords": ["zapallo kg"], "cantidad_ae": 1.146, "kcal_100g": 26, "prot_100g": 1.0, "carb_100g": 6.5, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Acelga", "keywords": ["acelga"], "cantidad_ae": 1.146, "kcal_100g": 19, "prot_100g": 1.8, "carb_100g": 3.7, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Manzana", "keywords": ["manzana kg"], "cantidad_ae": 1.2375, "kcal_100g": 52, "prot_100g": 0.3, "carb_100g": 13.8, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Naranja", "keywords": ["naranja kg"], "cantidad_ae": 1.2375, "kcal_100g": 47, "prot_100g": 0.9, "carb_100g": 11.8, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Banana", "keywords": ["banana kg"], "cantidad_ae": 1.2375, "kcal_100g": 89, "prot_100g": 1.1, "carb_100g": 22.8, "grasas_100g": 0.3},
    {"rubro": "Frutas y Verduras", "producto": "Pera", "keywords": ["pera kg"], "cantidad_ae": 1.2375, "kcal_100g": 57, "prot_100g": 0.4, "carb_100g": 15.0, "grasas_100g": 0.1},

    # --- AZÚCAR, DULCES Y LEGUMBRES ---
    {"rubro": "Almacén", "producto": "Azúcar", "keywords": ["azucar 1kg", "azucar blanca", "azuc"], "cantidad_ae": 1.230, "kcal_100g": 387, "prot_100g": 0.0, "carb_100g": 100.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Dulce de leche", "keywords": ["dulce de leche", "dulce leche", "dulb"], "cantidad_ae": 0.110, "kcal_100g": 315, "prot_100g": 7.0, "carb_100g": 55.0, "grasas_100g": 7.0},
    {"rubro": "Almacén", "producto": "Mermelada", "keywords": ["mermelada"], "cantidad_ae": 0.110, "kcal_100g": 260, "prot_100g": 0.5, "carb_100g": 65.0, "grasas_100g": 0.1},
    {"rubro": "Almacén", "producto": "Dulce de batata", "keywords": ["dulce de batata"], "cantidad_ae": 0.110, "kcal_100g": 255, "prot_100g": 0.5, "carb_100g": 63.0, "grasas_100g": 0.1},
    {"rubro": "Almacén", "producto": "Lentejas", "keywords": ["lentejas 500g", "lentejas", "legu"], "cantidad_ae": 0.120, "kcal_100g": 340, "prot_100g": 24.0, "carb_100g": 60.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Arvejas", "keywords": ["arvejas 500g", "arvejas", "arv"], "cantidad_ae": 0.120, "kcal_100g": 340, "prot_100g": 22.0, "carb_100g": 60.0, "grasas_100g": 1.2},

    # --- CARNES, MENUDENCIAS Y FIAMBRES ---
    {"rubro": "Carnes", "producto": "Asado", "keywords": ["asado kg"], "cantidad_ae": 1.045, "kcal_100g": 250, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 20.0},
    {"rubro": "Carnes", "producto": "Carne picada", "keywords": ["carne picada"], "cantidad_ae": 1.045, "kcal_100g": 210, "prot_100g": 19.0, "carb_100g": 0.0, "grasas_100g": 15.0},
    {"rubro": "Carnes", "producto": "Paleta", "keywords": ["paleta kg"], "cantidad_ae": 1.045, "kcal_100g": 170, "prot_100g": 20.0, "carb_100g": 0.0, "grasas_100g": 10.0},
    {"rubro": "Carnes", "producto": "Nalga", "keywords": ["nalga kg"], "cantidad_ae": 1.045, "kcal_100g": 140, "prot_100g": 21.0, "carb_100g": 0.0, "grasas_100g": 5.0},
    {"rubro": "Carnes", "producto": "Pollo entero", "keywords": ["pollo entero kg"], "cantidad_ae": 1.045, "kcal_100g": 215, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 15.0},
    {"rubro": "Carnes", "producto": "Pescado", "keywords": ["pescado kg", "filet de merluza"], "cantidad_ae": 1.045, "kcal_100g": 90, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 1.5},
    {"rubro": "Carnes", "producto": "Hígado", "keywords": ["higado kg", "higado de vacuno"], "cantidad_ae": 0.270, "kcal_100g": 135, "prot_100g": 20.0, "carb_100g": 3.8, "grasas_100g": 4.0},
    {"rubro": "Carnes", "producto": "Paleta cocida", "keywords": ["paleta cocida"], "cantidad_ae": 0.030, "kcal_100g": 130, "prot_100g": 18.0, "carb_100g": 2.0, "grasas_100g": 6.0},
    {"rubro": "Carnes", "producto": "Salame", "keywords": ["salame"], "cantidad_ae": 0.030, "kcal_100g": 400, "prot_100g": 20.0, "carb_100g": 1.0, "grasas_100g": 35.0},

    # --- LÁCTEOS Y HUEVOS ---
    {"rubro": "Lácteos y Huevos", "producto": "Huevos (docena)", "keywords": ["huevos docena", "maple huevos", "huevos x 12"], "cantidad_ae": 0.600, "kcal_100g": 150, "prot_100g": 12.5, "carb_100g": 0.7, "grasas_100g": 10.0},
    {"rubro": "Lácteos y Huevos", "producto": "Leche entera", "keywords": ["leche entera 1l", "leche sachet 1l"], "cantidad_ae": 9.270, "kcal_100g": 60, "prot_100g": 3.1, "carb_100g": 4.7, "grasas_100g": 3.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso cremoso", "keywords": ["queso cremoso kg"], "cantidad_ae": 0.110, "kcal_100g": 300, "prot_100g": 18.0, "carb_100g": 1.5, "grasas_100g": 25.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso cuartirolo", "keywords": ["queso cuartirolo"], "cantidad_ae": 0.110, "kcal_100g": 280, "prot_100g": 19.0, "carb_100g": 1.5, "grasas_100g": 22.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso de rallar", "keywords": ["queso rallar"], "cantidad_ae": 0.110, "kcal_100g": 380, "prot_100g": 33.0, "carb_100g": 1.5, "grasas_100g": 27.0},
    {"rubro": "Lácteos y Huevos", "producto": "Yogur", "keywords": ["yogur entero", "yogur sachet", "yogur firm"], "cantidad_ae": 0.570, "kcal_100g": 65, "prot_100g": 3.2, "carb_100g": 9.0, "grasas_100g": 2.5},
    {"rubro": "Lácteos y Huevos", "producto": "Manteca", "keywords": ["manteca 200g", "manteca 100g"], "cantidad_ae": 0.060, "kcal_100g": 717, "prot_100g": 0.9, "carb_100g": 0.1, "grasas_100g": 81.0},

    # --- ACEITES, CONDIMENTOS Y BEBIDAS ---
    {"rubro": "Almacén", "producto": "Aceite de girasol", "keywords": ["aceite girasol 900", "aceite girasol 1l", "acgi"], "cantidad_ae": 1.200, "kcal_100g": 884, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 100.0},
    {"rubro": "Bebidas", "producto": "Gaseosa", "keywords": ["gaseosa 1.5l", "gaseosa 2l", "gas"], "cantidad_ae": 1.150, "kcal_100g": 40, "prot_100g": 0.0, "carb_100g": 10.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Jugo", "keywords": ["jugo concentrado"], "cantidad_ae": 1.150, "kcal_100g": 35, "prot_100g": 0.0, "carb_100g": 9.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Soda", "keywords": ["soda 1.5l", "agus"], "cantidad_ae": 1.150, "kcal_100g": 0, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Cerveza", "keywords": ["cerveza 1l", "cerv"], "cantidad_ae": 0.540, "kcal_100g": 43, "prot_100g": 0.5, "carb_100g": 3.5, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Vino", "keywords": ["vino tinto 1l", "vinf"], "cantidad_ae": 0.540, "kcal_100g": 85, "prot_100g": 0.1, "carb_100g": 2.5, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Sal fina", "keywords": ["sal fina 500g", "sal fina 1kg", "salf"], "cantidad_ae": 0.120, "kcal_100g": 0, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Mayonesa", "keywords": ["mayonesa", "mayo"], "cantidad_ae": 0.060, "kcal_100g": 680, "prot_100g": 1.0, "carb_100g": 3.0, "grasas_100g": 75.0},
    {"rubro": "Almacén", "producto": "Caldo en cubo / Polvo", "keywords": ["caldo de verdura", "caldo de gallina", "cald", "esp"], "cantidad_ae": 0.060, "kcal_100g": 250, "prot_100g": 10.0, "carb_100g": 25.0, "grasas_100g": 10.0},
    {"rubro": "Almacén", "producto": "Vinagre", "keywords": ["vinagre de alcohol", "vinagre de manzana", "vina"], "cantidad_ae": 0.060, "kcal_100g": 18, "prot_100g": 0.0, "carb_100g": 0.1, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Café", "keywords": ["cafe molido", "cafe instantaneo", "cafem"], "cantidad_ae": 0.030, "kcal_100g": 200, "prot_100g": 14.0, "carb_100g": 40.0, "grasas_100g": 0.2},
    {"rubro": "Almacén", "producto": "Yerba mate", "keywords": ["yerba mate 1kg", "yerba mate 500g", "yerb"], "cantidad_ae": 0.510, "kcal_100g": 30, "prot_100g": 1.0, "carb_100g": 6.0, "grasas_100g": 0.0}
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

def extraer_observaciones_sitio(scraper, item_config, fecha, timestamp, sitio, max_paginas=2):
    observaciones = []
    textos_vistos = set()
    rubro = item_config['rubro']
    producto = item_config['producto']
    keywords = item_config.get('keywords', [])

    for kw in keywords:
        if not kw:
            continue
        for pagina in range(1, max_paginas + 1):
            if sitio == 'depotexpress':
                search_url = f"https://depotexpress.com.ar/?s={kw}&post_type=product&paged={pagina}"
                selectors = ['.product', '.type-product', 'div.item-producto', 'article']
            elif sitio == 'diaonline':
                search_url = f"https://diaonline.supermercadosdia.com.ar/{kw}?_q={kw}&map=ft" if pagina == 1 else f"https://diaonline.supermercadosdia.com.ar/{kw}?_q={kw}&map=ft&page={pagina}"
                selectors = ['article', 'div[class*="product"]', 'div[class*="summary"]', 'li[class*="product"]']
            else:
                break

            try:
                res = scraper.get(search_url, timeout=15)
                if res.status_code != 200:
                    break
                soup = BeautifulSoup(res.text, 'html.parser')
                
                items = []
                for sel in selectors:
                    items = soup.select(sel)
                    if items:
                        break
                if not items:
                    items = soup.select('div, article')

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
                                    'sitio_origen': sitio,
                                    'descripcion_producto': texto[:80],
                                    'precio_publicado': valor_publicado,
                                    'factor_unidad': factor_unidad,
                                    'precio': precio_normalizado_kgl
                                })
                                nuevas_obs_pagina += 1
                        except ValueError:
                            continue
                if nuevas_obs_pagina == 0 and sitio == 'diaonline':
                    break
                time.sleep(0.2)
            except Exception:
                break
        if observaciones:
            break
    return observaciones

def main():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y-%m-%d %H:%M:%S")

    resumen_productos = []

    for item in CBA_INDEC:
        obs = extraer_observaciones_sitio(scraper, item, fecha_hoy, timestamp, 'depotexpress')
        sitio_usado = 'depotexpress'

        if not obs:
            obs = extraer_observaciones_sitio(scraper, item, fecha_hoy, timestamp, 'diaonline')
            sitio_usado = 'diaonline' if obs else 'ninguno'

        registro = item.copy()

        if obs:
            precios_normalizados = [o['precio'] for o in obs]
            precio_final = float(np.median(precios_normalizados))
            metodo_calculo = f"Mediana directa ({sitio_usado})"
            coincidencias = len(obs)
            dispersion_std = float(np.std(precios_normalizados)) if len(precios_normalizados) > 1 else 0.0
        else:
            precio_final = 0.0
            metodo_calculo = "No encontrado"
            dispersion_std = 0.0
            coincidencias = 0

        # Cálculos de nutrientes diarios por Adulto Equivalente (AE)
        cantidad_ae = item.get('cantidad_ae', 0.0)
        kcal_diarias = (cantidad_ae * 1000.0 / 30.0) * (item.get('kcal_100g', 0) / 100.0)
        prot_diarias = (cantidad_ae * 1000.0 / 30.0) * (item.get('prot_100g', 0.0) / 100.0)
        carb_diarios = (cantidad_ae * 1000.0 / 30.0) * (item.get('carb_100g', 0.0) / 100.0)
        grasas_diarias = (cantidad_ae * 1000.0 / 30.0) * (item.get('grasas_100g', 0.0) / 100.0)

        registro.update({
            'fecha': fecha_hoy,
            'timestamp': timestamp,
            'precio_unitario_estimado': precio_final,
            'coincidencias': coincidencias,
            'dispersion_std': dispersion_std,
            'metodo_calculo': metodo_calculo,
            'kcal_diarias_ae': kcal_diarias,
            'prot_diarias_g': prot_diarias,
            'carb_diarios_g': carb_diarios,
            'grasas_diarias_g': grasas_diarias
        })
        resumen_productos.append(registro)

    df_resumen = pd.DataFrame(resumen_productos)
    df_resumen['costo_mensual_ae'] = df_resumen['cantidad_ae'] * df_resumen['precio_unitario_estimado']
    df_resumen['costo_hogar_tipo'] = df_resumen['costo_mensual_ae'] * COEFICIENTE_HOGAR_TIPO

    costo_total_ae = df_resumen['costo_mensual_ae'].sum()
    costo_total_hogar = costo_total_ae * COEFICIENTE_HOGAR_TIPO

    total_productos = len(df_resumen)
    prod_con_coincidencias = (df_resumen['coincidencias'] > 0).sum()
    cobertura_scraper_pct = (prod_con_coincidencias / total_productos * 100.0) if total_productos > 0 else 0.0

    costo_cbt_ae = costo_total_ae * INVERSO_COEFICIENTE_ENGEL
    costo_cbt_hogar = costo_total_hogar * INVERSO_COEFICIENTE_ENGEL

    archivo_detalle = "cba_historico_detalle.csv"
    archivo_totales = "cba_historico_totales.csv"
    archivo_nutricional = "cba_tabla_nutricional.csv"

    df_resumen.drop(columns=['keywords'], errors='ignore').to_csv(archivo_detalle, mode='a', header=not os.path.exists(archivo_detalle), index=False, encoding="utf-8-sig")

    df_totales = pd.DataFrame([{
        'fecha': fecha_hoy,
        'timestamp': timestamp,
        'prod_real': prod_con_coincidencias,
        'prod_total': total_productos,
        'cobertura_scraper_pct': cobertura_scraper_pct,
        'costo_total_cba_ae': costo_total_ae,
        'costo_total_cba_hogar': costo_total_hogar,
        'costo_total_cbt_ae': costo_cbt_ae,
        'costo_total_cbt_hogar': costo_cbt_hogar
    }])
    df_totales.to_csv(archivo_totales, mode='a', header=not os.path.exists(archivo_totales), index=False, encoding="utf-8-sig")

    df_nutricional = df_resumen[['fecha', 'timestamp', 'rubro', 'producto', 'cantidad_ae', 'kcal_diarias_ae', 'prot_diarias_g', 'carb_diarios_g', 'grasas_diarias_g']]
    df_nutricional.to_csv(archivo_nutricional, mode='a', header=not os.path.exists(archivo_nutricional), index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
