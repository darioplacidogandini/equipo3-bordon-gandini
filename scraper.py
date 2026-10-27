import requests
import cloudscraper
import pandas as pd
import re
import os
import time
import logging
from datetime import datetime

# Configuración del registro de errores y eventos
LOG_FILE = "cba_errores_log.txt"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Diccionario de productos de la Canasta Básica Alimentaria con sus respectivas palabras clave para búsqueda
PRODUCTOS_CBA = {
    "Pan francés": ["pan frances", "pan flauta", "pan baguette"],
    "Galletitas de agua": ["galletitas de agua", "galletitas agua"],
    "Galletitas dulces": ["galletitas dulces", "pepas", "surtidas"],
    "Arroz blanco": ["arroz largo fino", "arroz", "gallo"],
    "Harina de trigo 000": ["harina 000", "harina trigo", "harina comun"],
    "Harina de maíz / Polenta": ["polenta", "harina de maiz"],
    "Fideos secos": ["fideos tallarines", "fideos tirabuzon", "fideos"],
    "Papa": ["papa negra", "papa blanca", "papa"],
    "Batata": ["batata"],
    "Cebolla": ["cebolla"],
    "Zanahoria": ["zanahoria"],
    "Acelga": ["acelga"],
    "Zapallo": ["zapallo anco", "calabaza"],
    "Tomate redondo": ["tomate redondo", "tomate"],
    "Manzana": ["manzana red deliciosa", "manzana"],
    "Naranja": ["naranja"],
    "Banana": ["banana", "bananas"],
    "Pera": ["pera"],
    "Dulce de leche": ["dulce de leche", "dulce de leche colonial", "dulce de leche clasico"],
    "Mermelada": ["mermelada durazno", "mermelada frutilla", "mermelada"],
    "Dulce de batata": ["dulce de batata", "batata"],
    "Lentejas": ["lentejas secas", "lentejas"],
    "Arvejas": ["arvejas secas", "arvejas"],
    "Asado": ["asado"],
    "Paleta": ["paleta vacuno", "paleta"],
    "Nalga": ["nalga"],
    "Carne picada": ["carne picada especial", "carne picada"],
    "Hígado": ["higado vacuno", "higado"],
    "Pollo": ["pollo entero", "pollo"],
    "Paleta cocida": ["paleta cocida", "jamon cocido"],
    "Salame": ["salame picado fino", "salamin", "salame"],
    "Huevos (docena)": ["huevos colorados", "huevos blancos", "docena huevos"],
    "Leche entera": ["leche entera sachet", "leche sachet", "leche"],
    "Queso cremoso": ["queso cremoso", "cremoso"],
    "Queso rallado": ["queso rallado"],
    "Yogur": ["yogur firme", "yogur bebibil", "yogur"],
    "Mantequilla / Manteca": ["manteca"],
    "Aceite de girasol": ["aceite de girasol", "aceite girasol"],
    "Gaseosa": ["gaseosa cola", "coca cola"],
    "Jugo": ["jugo en polvo", "tang", "clight"],
    "Cerveza": ["cerveza rubia", "cerveza lata"],
    "Vino": ["vino tinto", "vino carton"],
    "Sal fina": ["sal fina", "sal"],
    "Mayonesa": ["mayonesa clasica", "mayonesa"],
    "Caldo en cubo / Polvo": ["caldo en cubo", "caldo"],
    "Café": ["cafe instantaneo", "cafe molido"],
    "Yerba mate": ["yerba mate", "yerba con palo", "yerba"]
}

SUPERMERCADOS = [
    "carrefour.com.ar",
    "diaonline.supermercadosdia.com.ar"
]

def extraer_factor_unidad(nombre_producto):
    """
    Extrae la cantidad o peso en unidad estandarizada (kg/litro) desde el nombre del producto.
    """
    nombre = nombre_producto.lower()
    
    # Búsqueda de gramos (g o gr)
    match_g = re.search(r'(\d+)\s*(g|gr|gramos)', nombre)
    if match_g:
        gramos = float(match_g.group(1))
        return gramos / 1000.0 if gramos > 0 else 1.0

    # Búsqueda de kilogramos (kg)
    match_kg = re.search(r'(\d+(?:[\.,]\d+)?)\s*(kg|kilo|kilos)', nombre)
    if match_kg:
        kg = float(match_kg.group(1).replace(',', '.'))
        return kg if kg > 0 else 1.0

    # Búsqueda de mililitros (ml o cc)
    match_ml = re.search(r'(\d+)\s*(ml|cc)', nombre)
    if match_ml:
        ml = float(match_ml.group(1))
        return ml / 1000.0 if ml > 0 else 1.0

    # Búsqueda de litros (l o lt)
    match_l = re.search(r'(\d+(?:[\.,]\d+)?)\s*(l|lt|litro|litros)', nombre)
    if match_l:
        litros = float(match_l.group(1).replace(',', '.'))
        return litros if litros > 0 else 1.0

    return 1.0

def consultar_api_vtex(scraper, keyword, dominio):
    """
    Realiza la consulta a la API pública de VTEX para un supermercado y keyword determinada.
    """
    observaciones = []
    
    # Manejo dinámico del dominio: evitar anteponer 'www.' para diaonline
    if "diaonline" in dominio or dominio.startswith("www."):
        base_url = f"https://{dominio}"
    else:
        base_url = f"https://www.{dominio}"
        
    url_api = f"{base_url}/api/catalog_system/pub/products/search?ft={keyword}&_from=0&_to=24"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": f"{base_url}/"
    }

    try:
        # Petición con precalentamiento simple
        scraper.get(base_url, headers=headers, timeout=10)
        time.sleep(0.3)

        response = scraper.get(url_api, headers=headers, timeout=10)
        
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
                                if 10 < precio_norm < 10000000:
                                    observaciones.append({
                                        'descripcion': nombre,
                                        'precio_publicado': precio,
                                        'factor_unidad': factor,
                                        'precio': precio_norm,
                                        'sitio': dominio
                                    })
        else:
            logging.warning(f"{dominio} devolvió status code {response.status_code} buscando '{keyword}'")
            
        time.sleep(0.2)
    except Exception as e:
        logging.error(f"Error conectando con {dominio} buscando '{keyword}': {str(e)}")
        
    return observaciones

def main():
    logging.info("--- Inicio de ejecución del scraper ---")
    scraper = cloudscraper.create_scraper()
    
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    registros_detalle = []
    registros_totales = []
    
    productos_encontrados = 0
    total_productos_cba = len(PRODUCTOS_CBA)

    for producto_cba, keywords in PRODUCTOS_CBA.items():
        hallazgos_producto = []
        
        for kw in keywords:
            for dominio in SUPERMERCADOS:
                resultados = consultar_api_vtex(scraper, kw, dominio)
                hallazgos_producto.extend(resultados)
            
            # Si se encontraron resultados con una palabra clave, pasamos al siguiente producto CBA
            if hallazgos_producto:
                break

        if hallazgos_producto:
            productos_encontrados += 1
            # Seleccionar el precio mínimo para la mediana/promedio representativo
            precios = [h['precio'] for h in hallazgos_producto]
            precio_promedio = sum(precios) / len(precios)
            
            for item in hallazgos_producto:
                registros_detalle.append({
                    'fecha': fecha_hoy,
                    'producto_cba': producto_cba,
                    'descripcion': item['descripcion'],
                    'precio_publicado': item['precio_publicado'],
                    'factor_unidad': item['factor_unidad'],
                    'precio_normalizado': item['precio'],
                    'sitio': item['sitio']
                })
                
            registros_totales.append({
                'fecha': fecha_hoy,
                'producto_cba': producto_cba,
                'precio_promedio': round(precio_promedio, 2),
                'total_ofertas': len(hallazgos_producto)
            })
        else:
            logging.info(f"Producto NO encontrado: {producto_cba}")

    # Guardar o actualizar archivos CSV históricos
    if registros_detalle:
        df_det_nuevo = pd.DataFrame(registros_detalle)
        if os.path.exists('cba_historico_detalle.csv'):
            df_det_nuevo.to_csv('cba_historico_detalle.csv', mode='a', header=False, index=False)
        else:
            df_det_nuevo.to_csv('cba_historico_detalle.csv', index=False)

    if registros_totales:
        df_tot_nuevo = pd.DataFrame(registros_totales)
        if os.path.exists('cba_historico_totales.csv'):
            df_tot_nuevo.to_csv('cba_historico_totales.csv', mode='a', header=False, index=False)
        else:
            df_tot_nuevo.to_csv('cba_historico_totales.csv', index=False)

    cobertura = (productos_encontrados / total_productos_cba) * 100
    logging.info(f"--- Fin de ejecución: Cobertura {cobertura:.2f}% ({productos_encontrados}/{total_productos_cba}) ---")

if __name__ == '__main__':
    main()
