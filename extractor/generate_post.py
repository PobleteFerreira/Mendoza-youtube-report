import pandas as pd
import matplotlib.pyplot as plt
import os

print("🚀 Iniciando script generate_post.py...")

# 📁 Definir rutas
DATA_DIR = "data"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🔍 Buscar último archivo CSV en /data
csv_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
if not csv_files:
    print("❌ ERROR: No se encontró ningún archivo CSV en la carpeta /data/")
    exit()

latest_csv = csv_files[-1]
report_month = latest_csv.split("_")[1].replace(".csv", "")
csv_path = os.path.join(DATA_DIR, latest_csv)

print(f"📄 Archivo detectado: {csv_path}")

# 📥 Leer el CSV
try:
    df = pd.read_csv(csv_path)
    print(f"✅ CSV leído correctamente. Filas: {len(df)}")
except Exception as e:
    print(f"❌ ERROR al leer el CSV: {e}")
    exit()

# ❌ Excluir canal Brava
df = df[df["Nombre"].str.lower() != "brava"]
print(f"🧹 Brava excluido. Canales restantes: {len(df)}")

# 🧮 Calcular métricas
video_cols = [f"Video{i}_Vistas" for i in range(1, 6)]
likes_cols = [f"Video{i}_Likes" for i in range(1, 6)]
com_cols = [f"Video{i}_Comentarios" for i in range(1, 6)]

df["PromVistas"] = df[video_cols].mean(axis=1)
df["Ratio"] = df["PromVistas"] / df["Suscriptores"]
df["TotalLikes"] = df[likes_cols].sum(axis=1)
df["TotalComentarios"] = df[com_cols].sum(axis=1)
df["TotalVistas"] = df[video_cols].sum(axis=1)
df["Engagement100"] = ((df["TotalLikes"] + df["TotalComentarios"]) / df["TotalVistas"]) * 100

print("📊 Métricas calculadas.")

# 🏆 Top 10 por vistas/suscriptor
top = df.sort_values("Ratio", ascending=False).head(10).reset_index(drop=True)
print("🏅 Top 10 generado.")

# 📈 Gráfico
try:
    plt.figure(figsize=(6, 4))
    plt.barh(top["Nombre"], top["Ratio"])
    plt.xlabel("Vistas por suscriptor")
    plt.title(f"Ranking Streaming Mendoza – {report_month}")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    image_path = os.path.join(OUTPUT_DIR, f"ranking_{report_month}.png")
    plt.savefig(image_path)
    print(f"🖼️ Imagen guardada: {image_path}")
except Exception as e:
    print(f"❌ ERROR al generar imagen: {e}")

# 📱 Texto Instagram
instagram_text = f"""🔥 RANKING STREAMING MZA 🔥
¿Quién tiene más vistas por cada seguidor?

"""
for i, row in top.iterrows():
    estrella = "*" if "inactivo" in str(row.get("Estado", "")).lower() else ""
    instagram_text += f"{i+1}️⃣ {row['Nombre']} — {int(row['Ratio'])} vistas x seguidor{estrella}\n"

instagram_text += f"""
💡 ¿Qué significa esto?
Cuanto más alto este número, más "activa" está la comunidad. ¡No es solo cuántos te siguen, sino cuántos te ven!

#YouTubeMendoza #StreamingArgentino #Datos
"""

insta_path = os.path.join(OUTPUT_DIR, f"resumen_instagram_{report_month}.txt")
with open(insta_path, "w", encoding="utf-8") as f:
    f.write(instagram_text)
print(f"📱 Texto para Instagram generado: {insta_path}")

# 💼 Texto LinkedIn
linkedin_text = f"""📊 Informe mensual – YouTube Mendoza – {report_month}

Este ranking muestra cuántas vistas obtiene cada canal por cada suscriptor. Es un buen indicador de fidelidad y activación de comunidad.

🏆 Top 10 por vistas/suscriptor:
"""

for i, row in top.iterrows():
    linkedin_text += f"{i+1}. {row['Nombre']} — {int(row['Ratio'])} vistas por suscriptor\n"

linkedin_text += f"""

💬 ¿Por qué importa esto?
Un canal con pocos suscriptores pero muchas vistas puede tener una comunidad más activa que uno grande y pasivo. Este tipo de métricas nos ayuda a pensar más allá del “número de seguidores”.

#YouTubeMendoza #StreamingInteligente #EconomiaDePlataformas #AnálisisDigital
"""

linkedin_path = os.path.join(OUTPUT_DIR, f"resumen_linkedin_{report_month}.txt")
with open(linkedin_path, "w", encoding="utf-8") as f:
    f.write(linkedin_text)
print(f"💼 Texto para LinkedIn generado: {linkedin_path}")

print("✅ Script finalizado exitosamente.")

