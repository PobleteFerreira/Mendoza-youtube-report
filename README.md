# 📊 Mendoza YouTube Streaming Report

Este repositorio contiene un sistema automatizado de recolección, análisis y visualización crítica de datos sobre canales de streaming mendocinos en YouTube. El proyecto combina métodos computacionales con una perspectiva de economía política de la comunicación, con el fin de mapear la evolución, sostenibilidad y diversidad de actores locales.

## 🎯 Objetivos

* Construir una línea de tiempo mensual de la actividad de los canales.
* Evaluar impacto, frecuencia, engagement y estrategias de monetización alternativa.
* Visualizar resultados para redes sociales y toma de decisiones.

## 🧪 Metodología

* Extracción automatizada de datos con la API de YouTube.
* Análisis longitudinal, multicanal y contextual.
* Generación de reportes en gráficos, tablas y textos para Instagram/LinkedIn.

## 🗂 Estructura del Repositorio

```
Mendoza-youtube-report/
├── .github/workflows/       # GitHub Actions: automatización semanal/mensual
├── data/
│   ├── raw/                 # Datos crudos descargados desde la API
│   ├── processed/           # Datos limpios y enriquecidos para análisis
├── output/                 # Gráficos y resúmenes generados
├── scripts/                # Scripts Python paso a paso
│   ├── 01_fetch_data.py
│   ├── 02_clean_transform.py
│   ├── 03_generate_metrics.py
│   ├── 04_visualizations.py
│   └── 05_generate_posts.py
├── notebooks/              # Análisis exploratorios o informes jupyter opcionales
├── prompts/                # Prompts para solicitar ampliaciones a modelos de IA
├── extractor/requirements.txt  # Librerías necesarias
├── .gitignore              # Archivos a excluir del repositorio
└── README.md               # Este archivo
```

## 🧠 ¿Por qué este proyecto es diferente?

* Se basa en datos directamente obtenidos desde la API, no estimaciones.
* Se contextualiza en la economía local y la diversidad de producciones.
* Se considera la estructura de cada canal: cantidad de programas, ritmos de producción, estrategias.

## ⚙️ Requisitos para correr localmente

* Python 3.10+
* API Key de YouTube habilitada
* `pip install -r extractor/requirements.txt`

## 🚀 Automatización con GitHub Actions

Este repositorio está preparado para ejecutarse automáticamente cada semana o mes, descargando nuevos datos y actualizando resultados.

## 📢 Contacto

Para dudas o colaboraciones: pobleteferreira@gmail.com
