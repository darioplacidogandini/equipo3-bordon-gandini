import os
import re
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import cloudscraper

COEFICIENTE_HOGAR_TIPO = 3.09

# ------------------------------------------------------------------------------
# CANASTA BÁSICA ALIMENTARIA COMPLETA (INDEC) CON PRECIOS OFICIALES DE REFERENCIA
# Ajustada según la composición oficial por Adulto Equivalente (AE)
# ------------------------------------------------------------------------------
CBA_INDEC = [
    # --- PANADERÍA Y CEREALES ---
    {"rubro": "Panadería", "producto": "Pan francés", "keywords": ["pani", "pan frances"], "precio_indec": 2400.0, "cantidad_ae": 6.75, "kcal_100g": 265, "prot_100g": 9.0, "carb_100g": 55.0, "grasas_100g": 1.2},
    {"rubro": "Panadería", "producto": "Galletitas de agua", "keywords": ["gals", "galleta agua"], "precio_indec": 1800.0, "cantidad_ae": 0.42, "kcal_100g": 420, "prot_100g": 9.5, "carb_100g": 68.0, "grasas_100g": 12.0},
    {"rubro": "Panadería", "producto": "Galletitas dulces", "keywords": ["gald", "galleta dulce"], "precio_indec": 2200.0, "cantidad_ae": 0.21, "kcal_100g": 450, "prot_100g": 6.5, "carb_100g": 72.0, "grasas_100g": 15.0},
    {"rubro": "Almacén", "producto": "Harina de trigo 000", "keywords": ["hart", "harina trigo"], "precio_indec": 950.0, "cantidad_ae": 1.08, "kcal_100g": 340, "prot_100g": 10.0, "carb_100g": 72.0, "grasas_100g": 1.2},
    {"rubro": "Almacén", "producto": "Arroz blanco", "keywords": ["arr", "arroz blanco"], "precio_indec": 1900.0, "cantidad_ae": 1.20, "kcal_100g": 354, "prot_100g": 7.0, "carb_100g": 78.0, "grasas_100g": 0.6},
    {"rubro": "Almacén", "producto": "Fideos secos", "keywords": ["fido", "fideos secos"], "precio_indec": 1600.0, "cantidad_ae": 1.74, "kcal_100g": 355, "prot_100g": 12.0, "carb_100g": 73.0, "grasas_100g": 1.5},
    {"rubro": "Almacén", "producto": "Harina de maíz (Polenta)", "keywords": ["harm", "polenta"], "precio_indec": 1200.0, "cantidad_ae": 0.21, "kcal_100g": 350, "prot_100g": 8.0, "carb_100g": 76.0, "grasas_100g": 1.0},

    # --- PAPA Y BATATA ---
    {"rubro": "Frutas y Verduras", "producto": "Papa blanca", "keywords": ["papa blanca", "papa "], "precio_indec": 1100.0, "cantidad_ae": 6.51, "kcal_100g": 80, "prot_100g": 2.0, "carb_100g": 18.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Batata", "keywords": ["batata"], "precio_indec": 1500.0, "cantidad_ae": 0.51, "kcal_100g": 86, "prot_100g": 1.6, "carb_100g": 20.0, "grasas_100g": 0.1},

    # --- AZÚCAR Y DULCES ---
    {"rubro": "Almacén", "producto": "Azúcar", "keywords": ["azuc", "azucar"], "precio_indec": 1200.0, "cantidad_ae": 1.23, "kcal_100g": 387, "prot_100g": 0.0, "carb_100g": 100.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Dulce de leche", "keywords": ["dulce leche"], "precio_indec": 2600.0, "cantidad_ae": 0.11, "kcal_100g": 315, "prot_100g": 6.0, "carb_100g": 55.0, "grasas_100g": 7.5},
    {"rubro": "Almacén", "producto": "Dulce de batata", "keywords": ["dulce batata"], "precio_indec": 2300.0, "cantidad_ae": 0.11, "kcal_100g": 255, "prot_100g": 0.5, "carb_100g": 63.0, "grasas_100g": 0.1},
    {"rubro": "Almacén", "producto": "Mermelada", "keywords": ["mer", "mermelada"], "precio_indec": 2400.0, "cantidad_ae": 0.11, "kcal_100g": 260, "prot_100g": 0.4, "carb_100g": 65.0, "grasas_100g": 0.1},

    # --- LEGUMBRES SECAS ---
    {"rubro": "Almacén", "producto": "Lentejas secas", "keywords": ["legu", "lentejas"], "precio_indec": 3200.0, "cantidad_ae": 0.12, "kcal_100g": 350, "prot_100g": 25.0, "carb_100g": 60.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Arvejas secas / en lata", "keywords": ["arvejas"], "precio_indec": 1800.0, "cantidad_ae": 0.12, "kcal_100g": 340, "prot_100g": 22.0, "carb_100g": 60.0, "grasas_100g": 1.4},

    # --- HORTALIZAS ---
    {"rubro": "Frutas y Verduras", "producto": "Acelga", "keywords": ["acelga"], "precio_indec": 1500.0, "cantidad_ae": 0.80, "kcal_100g": 19, "prot_100g": 1.8, "carb_100g": 3.7, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Cebolla", "keywords": ["cebolla"], "precio_indec": 1200.0, "cantidad_ae": 1.10, "kcal_100g": 40, "prot_100g": 1.1, "carb_100g": 9.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Lechuga", "keywords": ["lechuga"], "precio_indec": 2800.0, "cantidad_ae": 0.60, "kcal_100g": 15, "prot_100g": 1.3, "carb_100g": 2.8, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Tomate perita / redondo", "keywords": ["tomate perita", "tomate redondo"], "precio_indec": 2400.0, "cantidad_ae": 1.20, "kcal_100g": 18, "prot_100g": 0.9, "carb_100g": 3.9, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Tomate envasado (pure/pelado)", "keywords": ["pure tomate", "tomate lata", "tomate envasado"], "precio_indec": 1400.0, "cantidad_ae": 0.53, "kcal_100g": 24, "prot_100g": 1.2, "carb_100g": 4.5, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Zanahoria", "keywords": ["zanahoria"], "precio_indec": 1100.0, "cantidad_ae": 0.70, "kcal_100g": 41, "prot_100g": 0.9, "carb_100g": 9.5, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Zapallo Anco", "keywords": ["zapallo anco", "zapallo"], "precio_indec": 1300.0, "cantidad_ae": 0.80, "kcal_100g": 45, "prot_100g": 1.0, "carb_100g": 11.0, "grasas_100g": 0.1},

    # --- FRUTAS ---
    {"rubro": "Frutas y Verduras", "producto": "Manzana", "keywords": ["manzana"], "precio_indec": 2100.0, "cantidad_ae": 1.20, "kcal_100g": 52, "prot_100g": 0.3, "carb_100g": 14.0, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Mandarina", "keywords": ["mandarina"], "precio_indec": 1700.0, "cantidad_ae": 0.85, "kcal_100g": 53, "prot_100g": 0.8, "carb_100g": 13.3, "grasas_100g": 0.3},
    {"rubro": "Frutas y Verduras", "producto": "Naranja", "keywords": ["naranja"], "precio_indec": 1600.0, "cantidad_ae": 1.20, "kcal_100g": 47, "prot_100g": 0.9, "carb_100g": 12.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Banana", "keywords": ["banana"], "precio_indec": 1900.0, "cantidad_ae": 1.20, "kcal_100g": 89, "prot_100g": 1.1, "carb_100g": 23.0, "grasas_100g": 0.3},
    {"rubro": "Frutas y Verduras", "producto": "Pera", "keywords": ["pera"], "precio_indec": 2000.0, "cantidad_ae": 0.50, "kcal_100g": 57, "prot_100g": 0.4, "carb_100g": 15.0, "grasas_100g": 0.1},

    # --- CARNES Y DERIVADOS ---
    {"rubro": "Carnes", "producto": "Asado con hueso", "keywords": ["asado"], "precio_indec": 8500.0, "cantidad_ae": 0.70, "kcal_100g": 250, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 20.0},
    {"rubro": "Carnes", "producto": "Carnaza común / Picada", "keywords": ["carne picada", "picada"], "precio_indec": 6200.0, "cantidad_ae": 1.20, "kcal_100g": 210, "prot_100g": 19.5, "carb_100g": 0.0, "grasas_100g": 14.0},
    {"rubro": "Carnes", "producto": "Espinazo", "keywords": ["espinazo"], "precio_indec": 3500.0, "cantidad_ae": 0.50, "kcal_100g": 190, "prot_100g": 16.0, "carb_100g": 0.0, "grasas_100g": 14.0},
    {"rubro": "Carnes", "producto": "Paleta vacuno", "keywords": ["paleta vacuno", "paleta"], "precio_indec": 8200.0, "cantidad_ae": 0.90, "kcal_100g": 145, "prot_100g": 20.0, "carb_100g": 0.0, "grasas_100g": 7.0},
    {"rubro": "Carnes", "producto": "Nalga", "keywords": ["nalga"], "precio_indec": 9800.0, "cantidad_ae": 0.90, "kcal_100g": 135, "prot_100g": 21.0, "carb_100g": 0.0, "grasas_100g": 5.0},
    {"rubro": "Carnes", "producto": "Pollo entero", "keywords": ["pollo entero", "pollo fresco"], "precio_indec": 3100.0, "cantidad_ae": 1.67, "kcal_100g": 170, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 11.0},
    {"rubro": "Carnes", "producto": "Pescado (Merluza)", "keywords": ["merluza", "filet merluza"], "precio_indec": 7500.0, "cantidad_ae": 0.40, "kcal_100g": 90, "prot_100g": 19.0, "carb_100g": 0.0, "grasas_100g": 1.2},
    {"rubro": "Carnes", "producto": "Hígado (Menudencias)", "keywords": ["higado"], "precio_indec": 3200.0, "cantidad_ae": 0.27, "kcal_100g": 133, "prot_100g": 20.4, "carb_100g": 3.8, "grasas_100g": 3.6},
    {"rubro": "Fiambrería", "producto": "Paleta cocida", "keywords": ["paleta cocida", "paleta fiambre"], "precio_indec": 8900.0, "cantidad_ae": 0.03, "kcal_100g": 130, "prot_100g": 16.0, "carb_100g": 2.0, "grasas_100g": 6.5},
    {"rubro": "Fiambrería", "producto": "Salame", "keywords": ["salame", "salamin"], "precio_indec": 11500.0, "cantidad_ae": 0.03, "kcal_100g": 380, "prot_100g": 20.0, "carb_100g": 1.5, "grasas_100g": 33.0},

    # --- LÁCTEOS Y HUEVOS ---
    {"rubro": "Lácteos y Huevos", "producto": "Huevos (unidades/kg)", "keywords": ["huevos", "huevo"], "precio_indec": 3200.0, "cantidad_ae": 0.60, "kcal_100g": 150, "prot_100g": 12.5, "carb_100g": 0.7, "grasas_100g": 10.0},
    {"rubro": "Lácteos y Huevos", "producto": "Leche entera", "keywords": ["lech"], "precio_indec": 1250.0, "cantidad_ae": 9.27, "kcal_100g": 60, "prot_100g": 3.1, "carb_100g": 4.7, "grasas_100g": 3.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso crema", "keywords": ["queso crema"], "precio_indec": 6800.0, "cantidad_ae": 0.10, "kcal_100g": 240, "prot_100g": 6.0, "carb_100g": 4.0, "grasas_100g": 22.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso cuartirolo / cremoso", "keywords": ["queso cremoso", "queso cuartirolo"], "precio_indec": 8200.0, "cantidad_ae": 0.15, "kcal_100g": 310, "prot_100g": 18.0, "carb_100g": 1.5, "grasas_100g": 26.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso de rallar / Sardo", "keywords": ["queso sardo", "queso rallar"], "precio_indec": 12500.0, "cantidad_ae": 0.08, "kcal_100g": 370, "prot_100g": 28.0, "carb_100g": 1.8, "grasas_100g": 28.0},
    {"rubro": "Lácteos y Huevos", "producto": "Yogur entero", "keywords": ["yogur entero", "yogur firme"], "precio_indec": 1800.0, "cantidad_ae": 0.57, "kcal_100g": 63, "prot_100g": 3.3, "carb_100g": 5.0, "grasas_100g": 3.2},
    {"rubro": "Lácteos y Huevos", "producto": "Manteca", "keywords": ["manteca"], "precio_indec": 15500.0, "cantidad_ae": 0.06, "kcal_100g": 740, "prot_100g": 0.8, "carb_100g": 0.1, "grasas_100g": 82.0},

    # --- ACEITES, BEBIDAS, CONDIMENTOS Y VARIOS ---
    {"rubro": "Almacén", "producto": "Aceite de girasol", "keywords": ["acei"], "precio_indec": 2800.0, "cantidad_ae": 1.20, "kcal_100g": 884, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 100.0},
    {"rubro": "Bebidas", "producto": "Bebidas no alcohólicas (Gaseosas/Soda)", "keywords": ["gaseosa", "soda"], "precio_indec": 1500.0, "cantidad_ae": 3.45, "kcal_100g": 25, "prot_100g": 0.0, "carb_100g": 6.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Bebidas alcohólicas (Cerveza/Vino)", "keywords": ["cerveza", "vino"], "precio_indec": 2200.0, "cantidad_ae": 1.08, "kcal_100g": 55, "prot_100g": 0.3, "carb_100g": 3.5, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Sal fina", "keywords": ["sal fina"], "precio_indec": 900.0, "cantidad_ae": 0.12, "kcal_100g": 0, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Condimentos (Mayonesa/Caldos)", "keywords": ["mayonesa", "caldo"], "precio_indec": 3500.0, "cantidad_ae": 0.12, "kcal_100g": 450, "prot_100g": 1.0, "carb_100g": 8.0, "grasas_100g": 45.0},
    {"rubro": "Almacén", "producto": "Vinagre", "keywords": ["vinagre"], "precio_indec": 1100.0, "cantidad_ae": 0.06, "kcal_100g": 18, "prot_100g": 0.0, "carb_100g": 0.5, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Café molido", "keywords": ["cafm", "cafe molido"], "precio_indec": 8500.0, "cantidad_ae": 0.03, "kcal_100g": 2, "prot_100g": 0.1, "carb_100g": 0.3, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Yerba mate", "keywords": ["yerb"], "precio_indec": 3800.0, "cantidad_ae": 0.51, "kcal_100g": 30, "prot_100g": 1.0, "carb_100g": 6.0, "grasas_100g": 0.0}
]

def obtener_ultimo_precio_historico(nombre_producto):
    """Busca en cba_historico_detalle.csv el último precio válido para el producto."""
    file_detalle = "cba_historico_detalle.csv"
    if os.path.exists(file_detalle):
        try:
            df_hist = pd.read_csv(file_detalle)
            df_prod = df_hist[(df_hist['producto'] == nombre_producto) & (df_hist['precio_unitario_estimado'] > 0)]
            if not df_prod.empty:
                return float(df_prod.iloc[-1]['precio_unitario_estimado'])
        except Exception:
            pass
    return 0.0

def extraer_observaciones_raw(scraper, item_config, fecha, timestamp, max_paginas=5):
    observaciones = []
    textos_vistos = set()

    rubro = item_config['rubro']
    producto = item_config['producto']
    keywords = item_config.get('keywords', [item_config.get('keyword', '')])

    for kw in keywords:
        if not kw:
            continue

        for pagina in range(1, max_paginas + 1):
            search_url = f"https://depotexpress.com.ar/?s={kw}&post_type=product&paged={pagina}"

            try:
                res = scraper.get(search_url, timeout=25)
                if res.status_code != 200:
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.select('.product, .type-product, div.item-producto, article')
                
                if not items:
                    menciones = soup.find_all(string=lambda t: t and '$' in t)
                    for m in menciones:
                        padre = m.find_parent(['div', 'li', 'article'])
                        if padre and padre not in items:
                            items.append(padre)

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
                            valor = float(limpio)
                            if 100 < valor < 150000:
                                observaciones.append({
                                    'fecha': fecha,
                                    'timestamp': timestamp,
                                    'rubro': rubro,
                                    'producto': producto,
                                    'keyword_usada': kw,
                                    'descripcion_producto': texto[:80],
                                    'precio': valor
                                })
                                nuevas_obs_pagina += 1
                        except ValueError:
                            continue

                if nuevas_obs_pagina == 0:
                    break

                time.sleep(0.5)

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

    print(f"=== INICIANDO SCRAPING (MENOR PRECIO / FALLBACK INDEC) ({timestamp}) ===")
    
    todas_observaciones_raw = []
    resumen_productos = []

    for item in CBA_INDEC:
        obs = extraer_observaciones_raw(scraper, item, fecha_hoy, timestamp)
        registro = item.copy()

        if obs:
            # 1. Prioridad: Scraping Web exitoso
            obs_minima = min(obs, key=lambda x: x['precio'])
            precio_final = obs_minima['precio']
            metodo_calculo = "Precio Mínimo Encontrado"
            coincidencias = 1
            todas_observaciones_raw.append(obs_minima)
        else:
            # 2. Prioridad: Referencia Oficial INDEC
            precio_indec = item.get("precio_indec", 0.0)
            
            if precio_indec > 0:
                precio_final = precio_indec
                metodo_calculo = "Referencia Oficial INDEC"
                coincidencias = 0
            else:
                # 3. Prioridad: Último histórico guardado
                precio_hist = obtener_ultimo_precio_historico(item['producto'])
                if precio_hist > 0:
                    precio_final = precio_hist
                    metodo_calculo = "Histórico Guardado"
                else:
                    precio_final = 0.0
                    metodo_calculo = "Sin coincidencias (0)"
                coincidencias = 0

        registro.update({
            'fecha': fecha_hoy,
            'timestamp': timestamp,
            'precio_unitario_estimado': precio_final,
            'coincidencias': coincidencias,
            'metodo_calculo': metodo_calculo
        })
        resumen_productos.append(registro)
        print(f"-> Rubro: '{item['rubro']}' | Producto: '{item['producto']}' | Precio: ${precio_final:,.2f} ({metodo_calculo})")

    df_resumen = pd.DataFrame(resumen_productos)
    df_raw = pd.DataFrame(todas_observaciones_raw)

    # Persistir archivo histórico RAW
    file_raw = "cba_observaciones_raw.csv"
    if not df_raw.empty:
        if os.path.exists(file_raw):
            df_raw.to_csv(file_raw, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df_raw.to_csv(file_raw, index=False, encoding='utf-8-sig')

    # Cálculo de Totales y Exportación de Detalle
    df_resumen['costo_mensual_ae'] = df_resumen['cantidad_ae'] * df_resumen['precio_unitario_estimado']
    df_resumen['costo_hogar_tipo'] = df_resumen['costo_mensual_ae'] * COEFICIENTE_HOGAR_TIPO

    costo_total_ae = df_resumen['costo_mensual_ae'].sum()
    costo_total_hogar = costo_total_ae * COEFICIENTE_HOGAR_TIPO

    file_detalle = "cba_historico_detalle.csv"
    if os.path.exists(file_detalle):
        df_hist_det = pd.read_csv(file_detalle)
        df_det_final = pd.concat([df_hist_det, df_resumen], ignore_index=True)
    else:
        df_det_final = df_resumen

    df_det_final.to_csv(file_detalle, index=False, encoding='utf-8-sig')

    # Exportación de Totales Históricos
    file_totales = "cba_historico_totales.csv"
    df_totales = pd.DataFrame([{
        'fecha': fecha_hoy,
        'timestamp': timestamp,
        'costo_total_ae': costo_total_ae,
        'costo_total_hogar': costo_total_hogar
    }])

    if os.path.exists(file_totales):
        df_totales.to_csv(file_totales, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df_totales.to_csv(file_totales, index=False, encoding='utf-8-sig')

    # Exportación de Tabla Nutricional
    df_nutri = df_resumen[[
        'rubro', 'producto', 'cantidad_ae', 'kcal_100g', 'prot_100g', 'carb_100g', 'grasas_100g'
    ]].copy()

    df_nutri['kcal_diarias_ae'] = (df_nutri['cantidad_ae'] * 10 * df_nutri['kcal_100g']) / 30.0
    df_nutri['prot_diarias_g'] = (df_nutri['cantidad_ae'] * 10 * df_nutri['prot_100g']) / 30.0
    df_nutri['carb_diarios_g'] = (df_nutri['cantidad_ae'] * 10 * df_nutri['carb_100g']) / 30.0
    df_nutri['grasas_diarias_g'] = (df_nutri['cantidad_ae'] * 10 * df_nutri['grasas_100g']) / 30.0

    df_nutri['fecha'] = fecha_hoy
    df_nutri['timestamp'] = timestamp

    file_nutricional = "cba_tabla_nutricional.csv"
    if os.path.exists(file_nutricional):
        df_nutri.to_csv(file_nutricional, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df_nutri.to_csv(file_nutricional, index=False, encoding='utf-8-sig')

    # Resumen por consola
    cols_pantalla = ['rubro', 'producto', 'coincidencias', 'precio_unitario_estimado', 'costo_mensual_ae', 'metodo_calculo']
    
    print("\n" + "="*95)
    print("RESUMEN DE RESULTADOS (CBA - SCRAPING + REFERENCIA INDEC)")
    print("="*95)
    print(df_resumen[cols_pantalla].rename(columns={
        'rubro': 'Rubro',
        'producto': 'Producto',
        'coincidencias': 'Encontrado',
        'precio_unitario_estimado': 'Precio Final ($)',
        'costo_mensual_ae': 'Costo Mensual AE ($)',
        'metodo_calculo': 'Método Cálculo'
    }).to_string(index=False))
    print("="*95)
    print(f"✅ Costo Total Adulto Equivalente (AE): ${costo_total_ae:,.2f}")
    print(f"✅ Costo Total Hogar Tipo (3.09 AE):     ${costo_total_hogar:,.2f}")
    print("="*95)

if __name__ == "__main__":
    main()
