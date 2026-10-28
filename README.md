# 🛒 Estimación de la Canasta Básica Alimentaria (CBA) vía Web Scraping

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![CI/CD](https://img.shields.io/badge/GitHub%20Actions-Automated-black.svg)](https://github.com/features/actions)

Sistema automatizado de captura, procesamiento y seguimiento continuo de precios minoristas para la estimación en tiempo real del costo de la **Canasta Básica Alimentaria (CBA)** y la **Canasta Básica Total (CBT)** en Argentina, mapeado según los estándares nutricionales del **INDEC** por Adulto Equivalente (AE).

---

## 📌 Tabla de Contenidos

- [Visión General](#-visión-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Metodología de Cálculo y Nutrición](#-metodología-de-cálculo-y-nutrición)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Configuración Local](#-instalación-y-configuración-local)
- [Uso y API REST](#-uso-y-api-rest)
- [Automatización CI/CD](#-automatización-cicd)
- [Equipo de Desarrollo](#-equipo-de-desarrollo)

---

## 👁️ Visión General

El cálculo oficial de la Canasta Básica Alimentaria suele presentar desfases temporales respecto a la dinámica inflacionaria. Este proyecto resuelve dicha brecha recolectando automáticamente precios desde las APIs de e-commerce de cadenas de supermercados en Argentina.

### Características Clave

- **Monitoreo Automatizado:** Recolección diaria de precios sobre 52 productos esenciales.
- **Normalización de Unidades:** Conversión automática de presentaciones (g, kg, ml, L, docenas) a precios unitarios estandarizados.
- **Homologación Nutricional:** Cálculo diario de calorías ($2.750\text{ kcal/día}$ por AE) y macronutrientes (proteínas, carbohidratos, grasas).
- **Dashboard e Interfaz Web:** Panel interactivo desplegado dinámicamente con FastAPI y Chart.js.
- **Exportación Abierta:** Disponibilidad de datos en formato CSV y endpoints REST en JSON.

---

## 🏗️ Arquitectura del Sistema

```
+------------------+      +-------------------+      +----------------------+
|   Fuentes Web    | ---> |   Scraper Core    | ---> | Matriz Nutricional   |
| (VTEX / E-comm)  |      |   (scraper.py)    |      | (cba_tabla_nutri.csv)|
+------------------+      +-------------------+      +----------------------+
                                    |                           |
                                    v                           v
                          +-------------------+      +----------------------+
                          |    Persistencia   | ---> | Servicio API / Dash  |
                          | (CSV Historicos)  |      |   (api/index.py)     |
                          +-------------------+      +----------------------+
```

1. **Scraper Core (`scraper.py`):** Consulta endpoints de búsqueda y extrae precios mediante la librería `cloudscraper` para evadir bloqueos de infraestructura.
2. **Normalización y Filtrado:** Procesa variaciones del catálogo, calcula la mediana de precios y filtra anomalías/outliers.
3. **Persistencia de Datos:** Almacena registros diarios en archivos CSV versionados en el repositorio.
4. **API y Dashboard (`api/index.py`):** Microservicio basado en FastAPI que sirve los endpoints REST y la interfaz web para monitoreo y descarga directa de datasets.

---

## 📊 Metodología de Cálculo y Nutrición

El cálculo del costo mensual de la CBA se alinea con la metodología oficial del **INDEC**:

$$\text{Precio Estándar (\$/Unidad)} = \frac{\text{Precio Relevado}}{\text{Factor de Unidad (kg/L)}}$$

$$\text{CBA Total Adulto Eq. (\$/Mes)} = \sum_{i=1}^{n} \left( \text{Precio Estándar}_i \times \text{Cantidad Mensual AE}_i \right)$$

$$\text{CBA Hogar Tipo (\$/Mes)} = \text{CBA Adulto Eq.} \times 3.09$$

$$\text{CBT Hogar Tipo (\$/Mes)} = \text{CBA Hogar Tipo} \times 2.25$$

*Donde:*
- **Coeficiente Hogar Tipo:** Coeficiente $3.09$ (Hogar 2 según INDEC: varón de 35 años, mujer de 31 años, hijo de 6 años e hija de 8 años).
- **Inverso del Coeficiente de Engel:** Factor $2.25$ para la estimación de la Canasta Básica Total (incluye bienes y servicios no alimentarios).

---

## 📁 Estructura del Proyecto

```bash
equipo3-bordon-gandini/
├── .github/
│   └── workflows/
│       └── scraper.yml              # Pipeline de integración continua (GitHub Actions)
├── api/
│   └── index.py                     # API REST y Dashboard en FastAPI
├── Documentación Técnica.pdf        # Especificaciones metodológicas completas
├── cba_historico_totales.csv        # Registro diario de CBA, CBT y cobertura
├── cba_historico_detalle.csv        # Desglose diario por producto, rubro y precio
├── cba_tabla_nutricional.csv        # Matriz nutricional de la CBA (INDEC)
├── cba_errores_log.txt              # Registro de eventos y errores del scraper
├── scraper.py                       # Módulo principal de extracción de datos
├── requirements.txt                 # Dependencias del proyecto
└── README.md                        # Documentación principal
```

---

## ⚙️ Instalación y Configuración Local

### Prerrequisitos

- Python 3.10 o superior
- `git`

### Pasos

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/darioplacidogandini/equipo3-bordon-gandini.git
   cd equipo3-bordon-gandini
   ```

2. **Crear y activar un entorno virtual:**
   ```bash
   # En Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # En Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el Scraper manualmente:**
   ```bash
   python scraper.py
   ```

5. **Iniciar el servidor web local:**
   ```bash
   uvicorn api.index:app --reload
   ```
   Accede a `http://127.0.0.1:8000` en tu navegador para ver el dashboard interactivo.

---

## 🚀 Uso y API REST

El microservicio expone los siguientes endpoints HTTP:

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/` | Dashboard interactivo con gráficos, tablas y KPIs. |
| `GET` | `/api/totales` | Histórico consolidado de costos (CBA / CBT) y cobertura del scraper. |
| `GET` | `/api/detalle` | Desglose histórico de precios por producto, rubro y método de cálculo. |
| `GET` | `/api/nutricional` | Matriz de composición nutricional (Kcal, Proteínas, Carbohidratos, Grasas). |
| `GET` | `/api/health` | Estado del servicio API. |

---

## 🤖 Automatización CI/CD

El proyecto cuenta con una rutina de ejecución automatizada configurada mediante **GitHub Actions** (`.github/workflows/scraper.yml`):

- **Frecuencia:** Ejecución automática diaria programada por *cron*.
- **Acciones:** Corre `scraper.py`, actualiza los archivos CSV históricos, valida la cobertura e integra los cambios automáticamente en el repositorio mediante `git commit`.

---

## 👥 Equipo de Desarrollo

- **Equipo 3:** Bordón - Gandini
- **Repositorio Oficial:** [equipo3-bordon-gandini](https://github.com/darioplacidogandini/equipo3-bordon-gandini)