import os
import re
import time
from datetime import datetime
import pandas as pd
import cloudscraper
import numpy as np

# ------------------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN Y PONDERACIÓN
# ------------------------------------------------------------------------------
COEFICIENTE_HOGAR_TIPO = 3.09  
INVERSO_COEFICIENTE_ENGEL = 2.25  

# CANASTA BÁSICA ALIMENTARIA COMPLETA - PRODUCTOS DESAGREGADOS (Keywords mejoradas)
CBA_INDEC = [
    # --- PANADERÍA Y CEREALES ---
    {"rubro": "Panadería", "producto": "Pan francés", "keywords": ["pan frances", "baguette", "flautita", "pan flauta", "pan"], "cantidad_ae": 6.750, "kcal_100g": 265, "prot_100g": 9.0, "carb_100g": 55.0, "grasas_100g": 1.2},
    {"rubro": "Panadería", "producto": "Galletitas de agua", "keywords": ["galletitas de agua", "galletitas agua", "bagley", "express"], "cantidad_ae": 0.420, "kcal_100g": 420, "prot_100g": 9.5, "carb_100g": 68.0, "grasas_100g": 12.0},
    {"rubro": "Panadería", "producto": "Galletitas dulces", "keywords": ["galletitas dulces", "pepas", "surtidas"], "cantidad_ae": 0.210, "kcal_100g": 450, "prot_100g": 6.5, "carb_100g": 72.0, "grasas_100g": 15.0},
    {"rubro": "Almacén", "producto": "Arroz blanco", "keywords": ["arroz largo fino", "arroz", "gallo", "dos hermanos"], "cantidad_ae": 1.200, "kcal_100g": 354, "prot_100g": 7.0, "carb_100g": 78.0, "grasas_100g": 0.6},
    {"rubro": "Almacén", "producto": "Harina de trigo 000", "keywords": ["harina 000", "harina trigo", "harina comun"], "cantidad_ae": 1.080, "kcal_100g": 340, "prot_100g": 10.0, "carb_100g": 72.0, "grasas_100g": 1.2},
    {"rubro": "Almacén", "producto": "Harina de maíz / Polenta", "keywords": ["polenta", "harina de maiz", "manticora"], "cantidad_ae": 0.210, "kcal_100g": 350, "prot_100g": 8.0, "carb_100g": 76.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Fideos secos", "keywords": ["fideos tallarines", "fideos tirabuzon", "fideos guiseros", "fideos"], "cantidad_ae": 1.740, "kcal_100g": 355, "prot_100g": 12.0, "carb_100g": 73.0, "grasas_100g": 1.5},

    # --- VERDURAS, TUBÉRCULOS Y FRUTAS ---
    {"rubro": "Frutas y Verduras", "producto": "Papa blanca", "keywords": ["papa blanca", "papas", "papa"], "cantidad_ae": 6.510, "kcal_100g": 80, "prot_100g": 2.0, "carb_100g": 18.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Batata", "keywords": ["batata", "batatas"], "cantidad_ae": 0.510, "kcal_100g": 86, "prot_100g": 1.6, "carb_100g": 20.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Cebolla", "keywords": ["cebolla", "cebollas"], "cantidad_ae": 1.146, "kcal_100g": 40, "prot_100g": 1.1, "carb_100g": 9.0, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Tomate", "keywords": ["tomate redondo", "tomate perita", "tomate"], "cantidad_ae": 1.146, "kcal_100g": 18, "prot_100g": 0.9, "carb_100g": 3.9, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Zanahoria", "keywords": ["zanahoria", "zanahorias"], "cantidad_ae": 1.146, "kcal_100g": 41, "prot_100g": 0.9, "carb_100g": 9.6, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Zapallo", "keywords": ["zapallo anco", "zapallo cabutia", "zapallo"], "cantidad_ae": 1.146, "kcal_100g": 26, "prot_100g": 1.0, "carb_100g": 6.5, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Acelga", "keywords": ["acelga", "atado acelga"], "cantidad_ae": 1.146, "kcal_100g": 19, "prot_100g": 1.8, "carb_100g": 3.7, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Manzana", "keywords": ["manzana roja", "manzana verde", "manzana"], "cantidad_ae": 1.2375, "kcal_100g": 52, "prot_100g": 0.3, "carb_100g": 13.8, "grasas_100g": 0.2},
    {"rubro": "Frutas y Verduras", "producto": "Naranja", "keywords": ["naranja", "naranjas"], "cantidad_ae": 1.2375, "kcal_100g": 47, "prot_100g": 0.9, "carb_100g": 11.8, "grasas_100g": 0.1},
    {"rubro": "Frutas y Verduras", "producto": "Banana", "keywords": ["banana", "bananas"], "cantidad_ae": 1.2375, "kcal_100g": 89, "prot_100g": 1.1, "carb_100g": 22.8, "grasas_100g": 0.3},
    {"rubro": "Frutas y Verduras", "producto": "Pera", "keywords": ["pera", "peras"], "cantidad_ae": 1.2375, "kcal_100g": 57, "prot_100g": 0.4, "carb_100g": 15.0, "grasas_100g": 0.1},

    # --- AZÚCAR, DULCES Y LEGUMBRES ---
    {"rubro": "Almacén", "producto": "Azúcar", "keywords": ["azucar comun", "azucar blanca", "azucar"], "cantidad_ae": 1.230, "kcal_100g": 387, "prot_100g": 0.0, "carb_100g": 100.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Dulce de leche", "keywords": ["dulce de leche", "dulce de leche familiar"], "cantidad_ae": 0.110, "kcal_100g": 315, "prot_100g": 7.0, "carb_100g": 55.0, "grasas_100g": 7.0},
    {"rubro": "Almacén", "producto": "Mermelada", "keywords": ["mermelada durazno", "mermelada frutilla", "mermelada"], "cantidad_ae": 0.110, "kcal_100g": 260, "prot_100g": 0.5, "carb_100g": 65.0, "grasas_100g": 0.1},
    {"rubro": "Almacén", "producto": "Dulce de batata", "keywords": ["dulce de batata", "membrillo y batata"], "cantidad_ae": 0.110, "kcal_100g": 255, "prot_100g": 0.5, "carb_100g": 63.0, "grasas_100g": 0.1},
    {"rubro": "Almacén", "producto": "Lentejas", "keywords": ["lentejas secas", "lentejas", "lentejas en lata"], "cantidad_ae": 0.120, "kcal_100g": 340, "prot_100g": 24.0, "carb_100g": 60.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Arvejas", "keywords": ["arvejas secas", "arvejas lata", "arvejas"], "cantidad_ae": 0.120, "kcal_100g": 340, "prot_100g": 22.0, "carb_100g": 60.0, "grasas_100g": 1.2},

    # --- CARNES, MENUDENCIAS Y FIAMBRES ---
    {"rubro": "Carnes", "producto": "Asado", "keywords": ["asado", "tira de asado"], "cantidad_ae": 1.045, "kcal_100g": 250, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 20.0},
    {"rubro": "Carnes", "producto": "Carne picada", "keywords": ["carne picada", "picada comun", "picada especial"], "cantidad_ae": 1.045, "kcal_100g": 210, "prot_100g": 19.0, "carb_100g": 0.0, "grasas_100g": 15.0},
    {"rubro": "Carnes", "producto": "Paleta", "keywords": ["paleta vacuno", "corte paleta"], "cantidad_ae": 1.045, "kcal_100g": 170, "prot_100g": 20.0, "carb_100g": 0.0, "grasas_100g": 10.0},
    {"rubro": "Carnes", "producto": "Nalga", "keywords": ["nalga", "milanesa de nalga"], "cantidad_ae": 1.045, "kcal_100g": 140, "prot_100g": 21.0, "carb_100g": 0.0, "grasas_100g": 5.0},
    {"rubro": "Carnes", "producto": "Pollo entero", "keywords": ["pollo entero", "pollo fresco", "pollo"], "cantidad_ae": 1.045, "kcal_100g": 215, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 15.0},
    {"rubro": "Carnes", "producto": "Pescado", "keywords": ["filet de merluza", "merluza congelada", "pescado"], "cantidad_ae": 1.045, "kcal_100g": 90, "prot_100g": 18.0, "carb_100g": 0.0, "grasas_100g": 1.5},
    {"rubro": "Carnes", "producto": "Hígado", "keywords": ["higado vacuno", "higado"], "cantidad_ae": 0.270, "kcal_100g": 135, "prot_100g": 20.0, "carb_100g": 3.8, "grasas_100g": 4.0},
    {"rubro": "Carnes", "producto": "Paleta cocida", "keywords": ["paleta cocida", "jamon cocido", "fiambre"], "cantidad_ae": 0.030, "kcal_100g": 130, "prot_100g": 18.0, "carb_100g": 2.0, "grasas_100g": 6.0},
    {"rubro": "Carnes", "producto": "Salame", "keywords": ["salame picado fino", "salamin", "salame"], "cantidad_ae": 0.030, "kcal_100g": 400, "prot_100g": 20.0, "carb_100g": 1.0, "grasas_100g": 35.0},

    # --- LÁCTEOS Y HUEVOS ---
    {"rubro": "Lácteos y Huevos", "producto": "Huevos (docena)", "keywords": ["huevos colorados", "huevos blancos", "docena huevos", "huevos"], "cantidad_ae": 0.600, "kcal_100g": 150, "prot_100g": 12.5, "carb_100g": 0.7, "grasas_100g": 10.0},
    {"rubro": "Lácteos y Huevos", "producto": "Leche entera", "keywords": ["leche entera sachet", "leche sachet", "leche entera"], "cantidad_ae": 9.270, "kcal_100g": 60, "prot_100g": 3.1, "carb_100g": 4.7, "grasas_100g": 3.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso cremoso", "keywords": ["queso cremoso", "cremoso"], "cantidad_ae": 0.110, "kcal_100g": 300, "prot_100g": 18.0, "carb_100g": 1.5, "grasas_100g": 25.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso cuartirolo", "keywords": ["queso cuartirolo", "cuartirolo"], "cantidad_ae": 0.110, "kcal_100g": 280, "prot_100g": 19.0, "carb_100g": 1.5, "grasas_100g": 22.0},
    {"rubro": "Lácteos y Huevos", "producto": "Queso de rallar", "keywords": ["queso rallado", "sardo rallado", "queso sardo"], "cantidad_ae": 0.110, "kcal_100g": 380, "prot_100g": 33.0, "carb_100g": 1.5, "grasas_100g": 27.0},
    {"rubro": "Lácteos y Huevos", "producto": "Yogur", "keywords": ["yogur firme", "yogur bebibil", "yogur"], "cantidad_ae": 0.570, "kcal_100g": 65, "prot_100g": 3.2, "carb_100g": 9.0, "grasas_100g": 2.5},
    {"rubro": "Lácteos y Huevos", "producto": "Manteca", "keywords": ["manteca clasica", "manteca"], "cantidad_ae": 0.060, "kcal_100g": 717, "prot_100g": 0.9, "carb_100g": 0.1, "grasas_100g": 81.0},

    # --- ACEITES, CONDIMENTOS Y BEBIDAS ---
    {"rubro": "Almacén", "producto": "Aceite de girasol", "keywords": ["aceite de girasol", "aceite girasol", "aceite mezcla"], "cantidad_ae": 1.200, "kcal_100g": 884, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 100.0},
    {"rubro": "Bebidas", "producto": "Gaseosa", "keywords": ["gaseosa cola", "coca cola", "pepsi", "gaseosa"], "cantidad_ae": 1.150, "kcal_100g": 40, "prot_100g": 0.0, "carb_100g": 10.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Jugo", "keywords": ["jugo en polvo", "tang", "clight"], "cantidad_ae": 1.150, "kcal_100g": 35, "prot_100g": 0.0, "carb_100g": 9.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Soda", "keywords": ["soda sifon", "soda descartable", "soda"], "cantidad_ae": 1.150, "kcal_100g": 0, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Cerveza", "keywords": ["cerveza rubia", "cerveza lata", "cerveza"], "cantidad_ae": 0.540, "kcal_100g": 43, "prot_100g": 0.5, "carb_100g": 3.5, "grasas_100g": 0.0},
    {"rubro": "Bebidas", "producto": "Vino", "keywords": ["vino tinto", "vino carton", "vino"], "cantidad_ae": 0.540, "kcal_100g": 85, "prot_100g": 0.1, "carb_100g": 2.5, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Sal fina", "keywords": ["sal fina", "sal entrefina", "sal"], "cantidad_ae": 0.120, "kcal_100g": 0, "prot_100g": 0.0, "carb_100g": 0.0, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Mayonesa", "keywords": ["mayonesa clasica", "mayonesa"], "cantidad_ae": 0.060, "kcal_100g": 680, "prot_100g": 1.0, "carb_100g": 3.0, "grasas_100g": 75.0},
    {"rubro": "Almacén", "producto": "Caldo en cubo / Polvo", "keywords": ["caldo en cubo", "caldo gallina", "caldo verdura"], "cantidad_ae": 0.060, "kcal_100g": 250, "prot_100g": 10.0, "carb_100g": 25.0, "grasas_100g": 10.0},
    {"rubro": "Almacén", "producto": "Vinagre", "keywords": ["vinagre de alcohol", "vinagre manzana", "vinagre"], "cantidad_ae": 0.060, "kcal_100g": 18, "prot_100g": 0.0, "carb_100g": 0.1, "grasas_100g": 0.0},
    {"rubro": "Almacén", "producto": "Café", "keywords": ["cafe instantaneo", "cafe molido", "cafe"], "cantidad_ae": 0.030, "kcal_100g": 200, "prot_100g": 14.0, "carb_100g": 40.0, "grasas_100g": 0.2},
    {"rubro": "Almacén", "producto": "Yerba mate", "keywords": ["yerba mate", "yerba con palo", "yerba"], "cantidad_ae": 0.510, "kcal_100g": 30, "prot_100g": 1.0, "carb_100g": 6.0, "grasas_100g": 0.0}
]

def extraer_factor_unidad(nombre_producto):
    texto = nombre_producto.lower()
    match_kgl = re.search(r'(\d+(?:[\.,]\d+)?)\s*(kg|kilo|kilos|l|lt|litro|litros)\b', texto)
    if match_kgl:
        val = float(match_kgl.group(1).replace(',', '.'))
        return val if val > 0 else 1.0

    match_gml = re.search(r'(\d+(?:[\.,]\d+)?)\s*(g|gr|grs|gramos|ml|cc)\b', texto)
    if match_gml:
        val = float(match_gml.group(1).replace(',', '.'))
        return (val / 1000.0) if val > 0 else 1.0

    if 'x12' in texto or 'docena' in texto:
        return 0.6

    return 1.0

def consultar_api_vtex(scraper, keyword, dominio):
    observaciones = []
    url = f"https://www.{dominio}/api/catalog_system/pub/products/search?ft={keyword}&_from=0&_to=20"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "es-ES,es;q=0.9"
    }

    try:
        response = scraper.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            productos = response.json()
            if isinstance(productos, list):
                for prod in productos:
                    nombre = prod.get('productName', '')
                    items = prod.get('items', [])
                    for item in items:
                        sellers = item.get('sellers', [])
                        for seller in sellers:
                            offer = seller.get('commertialOffer', {})
                            precio = offer.get('Price', 0.0)
                            
                            if precio > 0:
                                factor = extraer_factor_unidad(nombre)
                                precio_norm = precio / factor
                                # Filtro de precios más amplio y flexible
                                if 10 < precio_norm < 5000000:
                                    observaciones.append({
                                        'descripcion': nombre,
                                        'precio_publicado': precio,
                                        'factor_unidad': factor,
                                        'precio': precio_norm,
                                        'sitio': dominio
                                    })
        time.sleep(0.1)
    except Exception:
        pass
    return observaciones

def main():
    scraper = cloudscraper.create_scraper()
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    timestamp = ahora.strftime("%Y-%m-%d %H:%M:%S")

    resumen_productos = []

    for item in CBA_INDEC:
        obs = []
        sitio_usado = "ninguno"
        
        for kw in item['keywords']:
            obs = consultar_api_vtex(scraper, kw, "carrefour.com.ar")
            if obs:
                sitio_usado = "carrefour"
                break
            
            obs = consultar_api_vtex(scraper, kw, "diaonline.supermercadosdia.com.ar")
            if obs:
                sitio_usado = "dia"
                break

        registro = item.copy()

        if obs:
            precios_norm = [o['precio'] for o in obs]
            precio_final = float(np.median(precios_norm))
            metodo_calculo = f"API JSON ({sitio_usado})"
            coincidencias = len(obs)
            dispersion_std = float(np.std(precios_norm)) if len(precios_norm) > 1 else 0.0
        else:
            precio_final = 0.0
            metodo_calculo = "No encontrado"
            dispersion_std = 0.0
            coincidencias = 0

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
    costo_cbt_hogar = costo_total_hogar * COEFICIENTE_HOGAR_TIPO * INVERSO_COEFICIENTE_ENGEL

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
