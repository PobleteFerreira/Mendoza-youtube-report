#!/usr/bin/env python3
"""
Analiza la evolución mensual de los Shorts de canales de YouTube.
Lee todos los archivos mensuales generados por shorts_analysis.py y genera:
- CSV resumen por canal y mes
- Gráficos de evolución en tonos pasteles

Requiere: archivos en data/shorts/shorts_YYYY-MM.csv
Salida: data/shorts/resumen_shorts.csv + gráficas en /data/shorts/graficos/
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuración
INPUT_DIR = Path("data/shorts/")
GRAFICOS_DIR = INPUT_DIR / "graficos"
GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)

# Leer todos los archivos shorts_YYYY-MM.csv
archivos = list(INPUT_DIR.glob("shorts_*.csv"))
df_list = []

for file in archivos:
    mes = file.stem.split("_")[1]
    df = pd.read_csv(file)
    df["Periodo"] = mes
    df_list.append(df)

# Combinar todos los meses
df_all = pd.concat(df_list, ignore_index=True)

# Asegurar formatos
df_all["Fecha"] = pd.to_datetime(df_all["Fecha"], errors='coerce')
df_all["Periodo"] = pd.to_datetime(df_all["Periodo"], format="%Y-%m")

# Agrupar por canal y mes
resumen = df_all.groupby(["CanalID", "Nombre", "Periodo"]).agg({
    "VideoID": "count",
    "Vistas": "sum",
    "Likes": "sum",
    "Comentarios": "sum"
}).reset_index()

# Renombrar columnas
resumen = resumen.rename(columns={
    "VideoID": "CantidadShorts",
    "Vistas": "VistasTotales",
    "Likes": "LikesTotales",
    "Comentarios": "ComentariosTotales"
})

# Métricas derivadas
resumen["VistasPromedio"] = resumen["VistasTotales"] / resumen["CantidadShorts"]
resumen["EngagementRate"] = (resumen["LikesTotales"] + resumen["ComentariosTotales"]) / resumen["VistasTotales"]

# Ordenar para calcular crecimiento
resumen = resumen.sort_values(["CanalID", "Periodo"])

# Guardar resumen como CSV
resumen.to_csv(INPUT_DIR / "resumen_shorts.csv", index=False)

# Función de gráfico pastel
def graficar_variable(df, variable, titulo, ylabel, filename):
    plt.figure(figsize=(10, 6))
    pastel_colors = sns.color_palette("pastel")

    sns.lineplot(
        data=df,
        x="Periodo",
        y=variable,
        hue="Nombre",
        palette=pastel_colors,
        marker="o"
    )

    plt.title(titulo, fontsize=14)
    plt.ylabel(ylabel)
    plt.xlabel("Periodo")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend(title="Canal", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.savefig(GRAFICOS_DIR / f"{filename}.png")
    plt.close()

# Crear gráficos
graficar_variable(resumen, "CantidadShorts", "Shorts publicados por mes", "Cantidad de Shorts", "cantidad_shorts")
graficar_variable(resumen, "VistasTotales", "Vistas totales por mes", "Vistas", "vistas_totales")
graficar_variable(resumen, "VistasPromedio", "Vistas promedio por Short", "Promedio de vistas", "vistas_promedio")
graficar_variable(resumen, "EngagementRate", "Engagement rate por mes", "Engagement (likes+comentarios / vistas)", "engagement_rate")

print("✅ Análisis longitudinal completado. Gráficos guardados en /data/shorts/graficos/")

