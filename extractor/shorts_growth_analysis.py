#!/usr/bin/env python3
"""
Genera un análisis longitudinal y gráficos de YouTube Shorts basados en los datos mensuales extraídos por `shorts_analysis.py`.

Requisitos:
- Archivos CSV mensuales en `data/shorts/shorts_YYYY-MM.csv`.
- Python 3.10+
- Paquetes: pandas, matplotlib

Salida:
- CSV resumen: `data/shorts/resumen_shorts.csv`
- Gráficos EN <periodo> en `data/shorts/graficos/`:
    - cantidad_shorts.png
    - vistas_totales.png
    - vistas_promedio.png
    - engagement_rate.png
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def main():
    # Definir rutas
    INPUT_DIR = Path("data/shorts")
    OUTPUT_CSV = INPUT_DIR / "resumen_shorts.csv"
    GRAFICOS_DIR = INPUT_DIR / "graficos"
    GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)

    # Buscar archivos mensuales
    archivos = sorted(INPUT_DIR.glob("shorts_*.csv"))
    if not archivos:
        print(f"⚠️ No se encontraron archivos shorts_*.csv en {INPUT_DIR}")
        return

    # Leer y concatenar todos los meses
    df_list = []
    for file in archivos:
        periodo = file.stem.split('_')[1]
        try:
            df = pd.read_csv(file)
            df["Periodo"] = pd.to_datetime(periodo, format="%Y-%m")
            df_list.append(df)
        except Exception as e:
            print(f"⚠️ Error al leer {file}: {e}")

    df_all = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
    if df_all.empty:
        print("⚠️ No hay datos para analizar después de concatenar.")
        return

    # Asegurar formatos de fecha
    df_all["Fecha"] = pd.to_datetime(df_all["Fecha"], errors='coerce')

    # Agrupar por canal y período
    resumen = df_all.groupby(["CanalID", "Nombre", "Periodo"]).agg({
        "VideoID": "count",
        "Vistas": "sum",
        "Likes": "sum",
        "Comentarios": "sum"
    }).reset_index()

    resumen = resumen.rename(columns={
        "VideoID": "CantidadShorts",
        "Vistas": "VistasTotales",
        "Likes": "LikesTotales",
        "Comentarios": "ComentariosTotales"
    })

    # Métricas derivadas
    resumen["VistasPromedio"] = resumen["VistasTotales"] / resumen["CantidadShorts"]
    resumen["EngagementRate"] = (
        resumen["LikesTotales"] + resumen["ComentariosTotales"]
    ) / resumen["VistasTotales"]

    # Guardar CSV de resumen
    resumen.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ CSV resumen guardado en {OUTPUT_CSV}")

    # Función genérica de gráfico de línea
    def plot_line(data, y_col, title, ylabel, out_filename):
        plt.figure(figsize=(10, 6))
        for canal, grupo in data.groupby("Nombre"):
            plt.plot(
                grupo["Periodo"],
                grupo[y_col],
                marker="o",
                label=canal
            )
        plt.title(title)
        plt.xlabel("Periodo")
        plt.ylabel(ylabel)
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.legend(title="Canal", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(GRAFICOS_DIR / out_filename)
        plt.close()

    # Generar gráficos
    plot_line(resumen, "CantidadShorts", "Shorts publicados por mes", "Cantidad de Shorts", "cantidad_shorts.png")
    plot_line(resumen, "VistasTotales", "Vistas totales por mes", "Vistas Totales", "vistas_totales.png")
    plot_line(resumen, "VistasPromedio", "Vistas promedio por Short", "Vistas Promedio", "vistas_promedio.png")
    plot_line(resumen, "EngagementRate", "Engagement rate por mes", "Engagement Rate (likes+comentarios / vistas)", "engagement_rate.png")

    print(f"✅ Gráficos guardados en {GRAFICOS_DIR}")


if __name__ == "__main__":
    main()


