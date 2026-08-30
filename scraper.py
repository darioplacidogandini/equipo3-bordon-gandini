import os
import re
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import cloudscraper

COEFICIENTE_HOGAR_TIPO = 3.09

# ------------------------------------------------------------------------------
# CANASTA BÁSICA ALIMENTARIA COMPLETA (INDEC) CON PROXIES DE RESPALDO
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
    {"rubro": "Hígado", "cantidad_ae": 0.45, "keyword": "higado", "kcal_100g": 133, "prot_100g": 20.4, "carb_100g": 3.8, "grasas_100g": 3.6, "proxy_rubro": "Carnaza común / Picada", "proxy_factor": 0.65},
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

    # --- ALMACÉN Y VARIOS ---
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

def extraer_observaciones_raw(scraper, keyword, rubro, fecha, timestamp, max_paginas=10):
    observaciones = []
    textos_vistos = set()

    for pagina in range(1, max_paginas + 1):
        # Paginación estándar de WooCommerce/WordPress
        search_url = f"https://depotexpress.com.ar/?s={keyword}&post_type=product&paged={pagina}"

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
                
                # Evita duplicar exactamente el mismo elemento extraído
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
                                'keyword': keyword,
                                'descripcion_producto': texto[:80],
                                'precio': valor
                            })
                            nuevas_obs_pagina += 1
                    except ValueError:
                        continue

            # Si en esta página no se añadieron productos nuevos, se detiene la paginación
            if nuevas_obs_pagina == 0:
                break

            time.sleep(0.8)

        except Exception as e:
            print(f"Error scraping '{keyword}' (Pág {pagina}): {e}")
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

    print(f"=== INICIANDO SCRAPING AMPLIADO ({timestamp}) ===")
    
    todas_observaciones_raw = []
    resumen_rubros = []

    # 1. Scraping exhaustivo con paginación
    for item in CBA_INDEC:
        obs = extraer_observaciones_raw(scraper, item['keyword'], item['rubro'], fecha_hoy, timestamp)
        todas_observaciones_raw.extend(obs)
        
        precios = [o['precio'] for o in obs]
        cant_obs = len(precios)

        registro = item.copy()
        
        if cant_obs > 0:
            precio_final = float(pd.Series(precios).median())
            metodo_calculo = "Mediana directa"
        else:
            precio_final = None
            metodo_calculo = "Faltante (Pendiente Imputación)"

        registro.update({
            'fecha': fecha_hoy,
            'timestamp': timestamp,
            'precio_unitario_estimado': precio_final,
            'coincidencias': cant_obs,
            'metodo_calculo': metodo_calculo
        })
        resumen_rubros.append(registro)
        print(f"-> Rubro: '{item['rubro']}' | Observaciones encontradas: {cant_obs}")

    df_resumen = pd.DataFrame(resumen_rubros)
    df_raw = pd.DataFrame(todas_observaciones_raw)

    # 2. Persistir archivo histórico RAW
    file_raw = "cba_observaciones_raw.csv"
    if not df_raw.empty:
        if os.path.exists(file_raw):
            df_raw.to_csv(file_raw, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df_raw.to_csv(file_raw, index=False, encoding='utf-8-sig')
        print(f"\n📦 Se guardaron {len(df_raw)} observaciones de precios crudas.")

    # 3. Imputación de Proxies para Faltantes
    for idx, row in df_resumen.iterrows():
        if pd.isna(row['precio_unitario_estimado']) or row['coincidencias'] == 0:
            proxy = row.get('proxy_rubro')
            factor = row.get('proxy_factor', 1.0)
            
            if proxy and proxy in df_resumen['rubro'].values:
                precio_proxy = df_resumen.loc[df_resumen['rubro'] == proxy, 'precio_unitario_estimado'].values[0]
                if pd.notna(precio_proxy):
                    df_resumen.at[idx, 'precio_unitario_estimado'] = precio_proxy * factor
                    df_resumen.at[idx, 'metodo_calculo'] = f"Proxy ({proxy} x {factor})"
            else:
                mediana_dia = df_resumen['precio_unitario_estimado'].median()
                df_resumen.at[idx, 'precio_unitario_estimado'] = mediana_dia
                df_resumen.at[idx, 'metodo_calculo'] = "Mediana General"

    # 4. Cálculo de Totales y Exportación
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

    # 5. Mostrar la tabla resultante con el conteo de observaciones por consola
    cols_pantalla = ['rubro', 'coincidencias', 'precio_unitario_estimado', 'costo_mensual_ae', 'metodo_calculo']
    
    print("\n" + "="*85)
    print("RESUMEN DE RESULTADOS (CBA - INDEC)")
    print("="*85)
    print(df_resumen[cols_pantalla].rename(columns={
        'rubro': 'Rubro',
        'coincidencias': 'Obs. Encontradas',
        'precio_unitario_estimado': 'Precio Mediana ($)',
        'costo_mensual_ae': 'Costo Mensual AE ($)',
        'metodo_calculo': 'Método Calculo'
    }).to_string(index=False))
    print("="*85)
    print(f"✅ Costo Total Adulto Equivalente (AE): ${costo_total_ae:,.2f}")
    print(f"✅ Costo Total Hogar Tipo (3.09 AE):     ${costo_total_hogar:,.2f}")
    print("="*85)

if __name__ == "__main__":
    main()
