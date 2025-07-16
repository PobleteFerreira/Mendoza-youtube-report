import pandas as pd
import matplotlib.pyplot as plt
import os
from glob import glob
from datetime import datetime

# Configuración
LIVE_DATA_DIR = "data/live_tracking"
OUTPUT_DIR = "output/live_analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Leer todos los CSV
csv_files = sorted(glob(os.path.join(LIVE_DATA_DIR, "*.csv")))

if not csv_files:
    print("❌ No se encontraron archivos de seguimiento en vivo.")
    exit()

# Concatenar todos los CSV en un solo DataFrame
df_list = []
for file in csv_files:
    temp = pd.read_csv(file)
    temp["timestamp"] = os.path.basename(file).replace(".csv", "")
    temp["timestamp"] = pd.to_datetime(temp["timestamp"], format="%Y%m%d_%H%M")
    df_list.append(temp)

df = pd.concat(df_list)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Agrupar por canal y fecha
df["hora"] = df["timestamp"].dt.time
df["fecha"] = df["timestamp"].dt.date
grouped = df.groupby(["channel_name", "fecha"]).agg({
    "views": ["mean", "max", "count"]
}).reset_index()
grouped.columns = ["Canal", "Fecha", "Promedio Vistas", "Máx Vistas", "Cantidad Capturas"]

# Graficar evolución de vistas por canal
for canal in grouped["Canal"].unique():
    canal_df = grouped[grouped["Canal"] == canal]
    plt.figure(figsize=(10, 5))
    plt.plot(canal_df["Fecha"], canal_df["Promedio Vistas"], marker='o', label="Promedio")
    plt.plot(canal_df["Fecha"], canal_df["Máx Vistas"], marker='s', linestyle="--", label="Máximo")
    plt.title(f"📈 Evolución de Vistas en Vivo - {canal}")
    plt.xlabel("Fecha")
    plt.ylabel("Vistas")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    # Guardar gráfico
    safe_name = canal.replace(" ", "_").replace("/", "_")
    plt.savefig(f"{OUTPUT_DIR}/evolucion_{safe_name}.png")
    plt.close()

print(f"✅ Análisis completado. Gráficos guardados en {OUTPUT_DIR}")
