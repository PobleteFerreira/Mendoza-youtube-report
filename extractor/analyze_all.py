import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import glob

# Ajuste de estilos pastel y tamaño
sns.set_palette('pastel')
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "axes.facecolor": "#f8f9fa",
    "axes.edgecolor": "#cfcfcf",
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "figure.dpi": 150
})

FIRMA = "Análisis realizado por Andrés Poblete"
OUTDIR = Path("data/informes")
OUTDIR.mkdir(parents=True, exist_ok=True)
# Encuentra todos los archivos mensuales
canales_files = sorted(glob.glob("data/canales/report_*.csv"))
if not canales_files:
    raise FileNotFoundError("No hay archivos de canales para analizar. Corré primero la extracción mensual.")

# Lee y concatena todos los meses en un solo DataFrame
df_list = []
for archivo in canales_files:
    df_mes = pd.read_csv(archivo)
    # Extrae mes y año del archivo para columna auxiliar
    mes_anio = os.path.splitext(os.path.basename(archivo))[0].replace('report_', '')
    df_mes['Periodo'] = mes_anio
    df_list.append(df_mes)
df = pd.concat(df_list, ignore_index=True)

# Convierte columnas numéricas si fuera necesario
for col in ['Suscriptores', 'VistasTotales', 'CantidadVideos', 'CantidadVivosMes']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
# Ordena por canal y período para análisis longitudinal
df = df.sort_values(["CanalID", "Periodo"])

# Cálculo de crecimiento mensual (por canal)
df["Suscriptores_prev"] = df.groupby("CanalID")["Suscriptores"].shift(1)
df["CrecimientoSubs"] = df["Suscriptores"] - df["Suscriptores_prev"]
df["CrecimientoSubs_%"] = 100 * df["CrecimientoSubs"] / df["Suscriptores_prev"]

df["VistasTotales_prev"] = df.groupby("CanalID")["VistasTotales"].shift(1)
df["CrecimientoViews"] = df["VistasTotales"] - df["VistasTotales_prev"]
df["CrecimientoViews_%"] = 100 * df["CrecimientoViews"] / df["VistasTotales_prev"]

# Rellena NaN en las columnas de crecimiento con 0
df["CrecimientoSubs"] = df["CrecimientoSubs"].fillna(0)
df["CrecimientoSubs_%"] = df["CrecimientoSubs_%"].fillna(0)
df["CrecimientoViews"] = df["CrecimientoViews"].fillna(0)
df["CrecimientoViews_%"] = df["CrecimientoViews_%"].fillna(0)


# Ratio vistas/suscriptores (de cada mes)
df["RatioViews_Subs"] = df["VistasTotales"] / df["Suscriptores"]

# Engagement promedio (usando videos, si querés sumar)
# Si necesitás leer los archivos de videos, podés hacerlo también con glob.glob y pd.read_csv
# Ranking mensual por suscriptores
df["RankingSubs"] = df.groupby("Periodo")["Suscriptores"].rank(ascending=False, method='min')
df["RankingViews"] = df.groupby("Periodo")["VistasTotales"].rank(ascending=False, method='min')
df["RankingRatio"] = df.groupby("Periodo")["RatioViews_Subs"].rank(ascending=False, method='min')

# Ejemplo de gráfico: evolución de suscriptores (los 5 más grandes)
top5 = df[df["Periodo"] == df["Periodo"].max()].sort_values("Suscriptores", ascending=False).head(5)["CanalID"]
plt.figure()
for canal in top5:
    canal_data = df[df["CanalID"] == canal]
    plt.plot(canal_data["Periodo"], canal_data["Suscriptores"], marker='o', label=canal_data["Nombre"].iloc[0])
plt.xlabel("Mes")
plt.ylabel("Suscriptores")
plt.title("Evolución de suscriptores - Top 5 canales")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.3)
plt.text(0.99, 0.01, FIRMA, fontsize=10, color="#888", ha='right', va='bottom', transform=plt.gca().transAxes)
plt.tight_layout()
plt.savefig(OUTDIR / "evolucion_suscriptores_top5.png")
plt.close()
# Tabla resumen por canal (último mes)
df_ultimo = df[df["Periodo"] == df["Periodo"].max()]
tabla_ranking = df_ultimo[["Nombre", "Suscriptores", "VistasTotales", "CantidadVivosMes", "RankingSubs", "RankingViews", "RatioViews_Subs"]]
tabla_ranking = tabla_ranking.sort_values("RankingSubs")

tabla_ranking.to_excel(OUTDIR / "ranking_general.xlsx", index=False)
tabla_ranking.to_csv(OUTDIR / "ranking_general.csv", index=False)
# Top canal crecimiento
top_canal = df_ultimo.sort_values("CrecimientoSubs", ascending=False).iloc[0]
crecimiento = int(top_canal['CrecimientoSubs']) if pd.notna(top_canal['CrecimientoSubs']) else 0
linkedin_txt = f"""
Informe Mensual Streaming Mendocino ({df_ultimo['Periodo'].iloc[0]})
El canal que más creció en suscriptores fue {top_canal['Nombre']} (+{crecimiento}).
...
"""
Informe Mensual Streaming Mendocino ({df_ultimo['Periodo'].iloc[0]})
El canal que más creció en suscriptores fue {top_canal['Nombre']} (+{int(top_canal['CrecimientoSubs'])}).
El canal con más vivos: {df_ultimo.sort_values('CantidadVivosMes', ascending=False).iloc[0]['Nombre']}.
Top 3 por vistas: {', '.join(df_ultimo.sort_values('VistasTotales', ascending=False).head(3)['Nombre'].tolist())}.
{FIRMA}
"""
with open(OUTDIR / "informe_linkedin.txt", "w", encoding="utf-8") as f:
    f.write(linkedin_txt.strip())

# Texto breve para Instagram
insta_txt = f""" Top 3 canales más vistos en {df_ultimo['Periodo'].iloc[0]}:
1️⃣ {df_ultimo.sort_values('VistasTotales', ascending=False).iloc[0]['Nombre']}
2️⃣ {df_ultimo.sort_values('VistasTotales', ascending=False).iloc[1]['Nombre']}
3️⃣ {df_ultimo.sort_values('VistasTotales', ascending=False).iloc[2]['Nombre']}
by Andrés Poblete"""
with open(OUTDIR / "informe_instagram.txt", "w", encoding="utf-8") as f:
    f.write(insta_txt.strip())
print("Análisis y reportes generados en:", OUTDIR.resolve())
