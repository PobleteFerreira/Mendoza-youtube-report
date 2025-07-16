import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import matplotlib.ticker as ticker

# Configuración de estilos
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'axes.edgecolor': '#333333',
    'axes.linewidth': 1.2,
    'axes.facecolor': '#f9f9f9',
    'figure.facecolor': '#ffffff',
    'grid.color': '#dddddd',
})

# Carpeta de entrada y salida
DATA_DIR = "data"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Detectar último archivo
def detectar_csv():
    archivos = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv") and f.startswith("report_")]
    if not archivos:
        print("❌ No se encontraron archivos CSV en data/")
        return None
    return sorted(archivos)[-1]

# Leer y procesar datos
csv_actual = detectar_csv()
if not csv_actual:
    exit()

print(f"🚀 Iniciando análisis: {csv_actual}")
df = pd.read_csv(os.path.join(DATA_DIR, csv_actual))

# Normalizar columnas
df = df[~df["Nombre"].str.lower().str.contains("brava")]

# Calcular vistas totales últimos 5 videos y ratio
df["Vistas5"] = df[["Video1_Vistas", "Video2_Vistas", "Video3_Vistas", "Video4_Vistas", "Video5_Vistas"]].sum(axis=1)
df["Promedio"] = df["Vistas5"] / 5

# Ratio de vistas por suscriptor (evitar división por cero)
df["Ratio"] = df.apply(lambda row: row["Vistas5"] / row["Suscriptores"] if row["Suscriptores"] > 0 else 0, axis=1)

# Formatear título de mes/año para gráficos
mes_anio = csv_actual.replace("report_", "").replace(".csv", "")
dt = datetime.strptime(mes_anio, "%Y%m")
titulo_periodo = dt.strftime("%B %Y").capitalize()

# Gráfico de ratio vistas/suscriptor
df_top = df.sort_values("Ratio", ascending=False).head(10)
plt.figure(figsize=(8, 6))
plt.barh(df_top["Nombre"], df_top["Ratio"], color=plt.cm.Pastel1.colors)
plt.xlabel("Vistas por suscriptor")
plt.title(f"Top 10 canales por Ratio de Visualización – {titulo_periodo}")
plt.gca().invert_yaxis()
plt.grid(True, axis='x', linestyle='--', alpha=0.6)
plt.tight_layout()

# Guardar gráfico
img_path = os.path.join(OUTPUT_DIR, f"ranking_{mes_anio}.png")
plt.savefig(img_path)
print(f"📊 Gráfico guardado: {img_path}")

# Texto para Instagram
txt_instagram = f"""
🏆 Top 10 Streaming Mendoza ({titulo_periodo})

📊 ¿Quién logra más vistas por suscriptor?

{chr(10).join([f"{i+1}. {row['Nombre']} — {round(row['Ratio'], 2)} vistas/suscriptor" for i, row in df_top.iterrows()])}

🔍 Análisis basado en los últimos 5 videos publicados por cada canal. Esta métrica muestra cuánto rinde cada seguidor en términos de visualización.

#StreamingMZA #YouTube #AnálisisDigital
"""

with open(os.path.join(OUTPUT_DIR, f"resumen_instagram_{mes_anio}.txt"), "w", encoding="utf-8") as f:
    f.write(txt_instagram)
    print(f"📱 Resumen Instagram guardado")

# Texto para LinkedIn
txt_linkedin = f"""
📊 Informe mensual de streaming mendocino ({titulo_periodo})

Analizamos la performance de canales locales en YouTube.

✔️ Indicador: Vistas por suscriptor (últimos 5 videos)
✔️ Muestra la eficacia de cada canal para activar a su audiencia.

Top 3 destacados:

{chr(10).join([f"➡️ {row['Nombre']}: {round(row['Ratio'], 2)}" for i, row in df_top.head(3).iterrows()])}

👉 Este reporte se genera automáticamente y considera solo emisiones en vivo completas, no recortes.

#DataMendoza #StreamingInteligente #YouTubeAnalytics
"""

with open(os.path.join(OUTPUT_DIR, f"resumen_linkedin_{mes_anio}.txt"), "w", encoding="utf-8") as f:
    f.write(txt_linkedin)
    print(f"💼 Resumen LinkedIn guardado")

print("✅ Análisis completado.")


