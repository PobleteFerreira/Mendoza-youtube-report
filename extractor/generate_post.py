import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# 📁 Carpeta donde están los CSV mensuales
DATA_DIR = "data"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🧠 Detectar el último CSV automáticamente
csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
latest_csv = csv_files[-1]
report_month = latest_csv.split("_")[1].replace(".csv", "")
csv_path = os.path.join(DATA_DIR, latest_csv)

# 📥 Leer datos
df = pd.read_csv(csv_path)
df = df[df["Nombre"].str.lower() != "brava"]  # excluir Brava

# 🔢 Calcular promedio de vistas de los últimos 5 videos
video_cols = [f"Video{i}_Vistas" for i in range(1, 6)]
df["PromVistas"] = df[video_cols].mean(axis=1)

# ⚖️ Calcular ratio vistas por suscriptor
df["Ratio"] = df["PromVistas"] / df["Suscriptores"]

# 💬 Engagement: likes + comentarios por cada 100 vistas
likes_cols = [f"Video{i}_Likes" for i in range(1, 6)]
com_cols = [f"Video{i}_Comentarios" for i in range(1, 6)]
df["TotalLikes"] = df[likes_cols].sum(axis=1)
df["TotalComentarios"] = df[com_cols].sum(axis=1)
df["TotalVistas"] = df[video_cols].sum(axis=1)
df["Engagement100"] = ((df["TotalLikes"] + df["TotalComentarios"]) / df["TotalVistas"]) * 100

# 🎯 Top 10 por ratio
top = df.sort_values("Ratio", ascending=False).head(10).reset_index(drop=True)

# 📊 Gráfico horizontal
plt.figure(figsize=(6, 4))
plt.barh(top["Nombre"], top["Ratio"])
plt.xlabel("Vistas por suscriptor")
plt.title(f"Ranking Streaming Mendoza – {report_month}")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, f"ranking_{report_month}.png"))

# 📱 Texto para Instagram
instagram_text = f"""🔥 RANKING STREAMING MZA 🔥
¿Quién tiene más vistas por cada seguidor?

"""
for i, row in top.iterrows():
    estrella = "*" if "inactivo" in str(row["Estado"]).lower() else ""
    instagram_text += f"{i+1}️⃣ {row['Nombre']} — {int(row['Ratio'])} vistas x seguidor{estrella}\n"

instagram_text += f"""
💡 ¿Qué significa esto?
Muestra qué tan "activa" está la comunidad de un canal. No importa solo cuántos te siguen, sino cuántos te ven.

#YouTubeMendoza #StreamingArgentino #Datos
"""

with open(os.path.join(OUTPUT_DIR, f"resumen_instagram_{report_month}.txt"), "w", encoding="utf-8") as f:
    f.write(instagram_text)

# 💼 Texto para LinkedIn
linkedin_text = f"""📊 Informe mensual – YouTube Mendoza – {report_month}

Este ranking muestra cuántas vistas obtiene cada canal por cada suscriptor. Es un buen indicador de fidelidad y activación de comunidad.

🏆 Top 10 por vistas/suscriptor:
"""

for i, row in top.iterrows():
    linkedin_text += f"{i+1}. {row['Nombre']} — {int(row['Ratio'])} vistas por suscriptor\n"

linkedin_text += f"""

💬 ¿Por qué importa esto?
Un canal con pocos suscriptores pero muchas vistas puede tener una comunidad más activa que uno grande y pasivo. Este tipo de métricas nos ayuda a pensar más allá del “número de seguidores”.

Datos extraídos automáticamente desde la API de YouTube y analizados con herramientas de código abierto.

#YouTubeMendoza #StreamingInteligente #EconomiaDePlataformas #AnálisisDigital
"""

with open(os.path.join(OUTPUT_DIR, f"resumen_linkedin_{report_month}.txt"), "w", encoding="utf-8") as f:
    f.write(linkedin_text)
