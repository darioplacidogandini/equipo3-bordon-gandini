import os
import re
import time
import logging
from datetime import datetime
import pandas as pd
import cloudscraper
import numpy as np

# ------------------------------------------------------------------------------
# CONFIGURACIÓN DEL REGISTRO DE ERRORES Y EVENTOS
# ------------------------------------------------------------------------------
ARCHIVO_LOG_ERRORES = "cba_errores_log.txt"

logging.basicConfig(
    filename=ARCHIVO_LOG_ERRORES,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8"
)

# ------------------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN Y PONDERACIÓN (INDEC)
# ------------------------------------------------------------------------------
COEFICIENTE_HOGAR_TIPO = 3.09  
INVERSO_COEFICIENTE_ENGEL = 2.25  

# CANASTA BÁSICA ALIMENTARIA COMPLETA - PRODUCTOS DESAGREGADOS
CBA_INDEC = [
    # --- PANADERÍA Y CEREALES ---
    {"rubro": "Panadería", "producto": "Pan francés", "keywords": ["pan frances", "baguette", "flautita", "pan"], "cantidad_ae": 6.750, "kcal_100g": 265, "prot_100g": 9.0, "carb_100g": 55.0, "grasas_100g": 1.2},
    {"rubro": "Panadería", "producto": "Galletitas de agua", "keywords": ["galletitas de agua", "galletitas agua", "express", "galletas agua"], "cantidad_ae": 0.420, "kcal_100g": 420, "prot_100g": 9.5, "carb_100g": 68.0, "grasas_100g": 12.0},
    {"rubro": "Panadería", "producto": "Galletitas dulces", "keywords": ["galletitas dulces", "pepas", "surtidas", "galletas dulces"], "cantidad_ae": 0.210, "kcal_100g": 450, "prot_100g": 6.5, "carb_100g": 72.0, "grasas_100g": 15.0},
    {"rubro": "Almacén", "producto": "Arroz blanco", "keywords": ["arroz largo fino", "arroz blanco", "arroz"], "cantidad_ae": 1.200, "kcal_100g": 354, "prot_100g": 7.0, "carb_100g": 78.0, "grasas_100g": 0.6},
    {"rubro": "Almacén", "producto": "Harina de trigo 000", "keywords": ["harina 000", "harina trigo", "harina comun"], "cantidad_ae": 1.080, "kcal_100g": 340, "prot_100g": 10.0, "carb_100g": 72.0, "grasas_100g": 1.2},
    {"rubro": "Almacén", "producto": "Harina de maíz / Polenta", "keywords": ["polenta", "harina de maiz", "harina maiz"], "cantidad_ae": 0.210, "kcal_100g": 350, "prot_100g": 8.0, "carb_100g": 76.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Fideos secos", "keywords": ["fideos tallarines", "fideos tirabuzon", "fideos secos", "fideos"], "cantidad_ae": 1.740, "kcal_100g": 355, "prot_100g": 12.0, "carb_100g": 73.0, "grasas_100g": 1.5},

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
    {"rubro": "Almacén", "producto": "Dulce de leche", "keywords": ["dulce de leche", "dulce leche", "dulce de leche colonial", "dulce de leche clasico"], "cantidad_ae": 0.110, "kcal_100g": 315, "prot_100g": 7.0, "carb_100g": 55.0, "grasas_100g": 7.0},
    {"rubro": "Almacén", "producto": "Mermelada", "keywords": ["mermelada durazno", "mermelada frutilla", "mermelada"], "cantidad_ae": 0.110, "kcal_100g": 260, "prot_100g": 0.5, "carb_100g": 65.0, "grasas_100g": 0.1},
    {"rubro": "Almacén", "producto": "Dulce de batata", "keywords": ["dulce de batata", "dulce batata"], "cantidad_ae": 0.110, "kcal_100g": 255, "prot_100g": 0.5, "carb_100g": 63.0, "grasas_100g": 0.1},
    {"rubro": "Almacén", "producto": "Lentejas", "keywords": ["lentejas secas", "lentejas"], "cantidad_ae": 0.120, "kcal_100g": 340, "prot_100g": 24.0, "carb_100g": 60.0, "grasas_100g": 1.0},
    {"rubro": "Almacén", "producto": "Arvejas", "keywords": ["arvejas secas", "arvejas lata", "arvejas"], "cantidad_ae": 0.120, "kcal_100g": 340, "prot_100g": 22.0, "carb_100g": 60.0, "grasas_100g": 1.2},

    # --- CARNES, MENUDENCIAS Y FIAMBRES ---
    {"
