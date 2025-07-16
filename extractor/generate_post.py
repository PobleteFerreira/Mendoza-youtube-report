import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Configuraciones generales
DATA_DIR = "data"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Detectar archivo del mes actual
def get_current_report_filename():
    now = datetime.now()
    return f"report_{now.strftime('%Y%m')}.csv"

# Leer CSV mensual
def load_data():
    file_path = os.path.join(DATA_DIR, get_current_report_filename())
    print(f"📄 Archivo detectado: {file_path}")
    df = pd.read_csv(file_path)
    return df

# Limpieza y preparación
def clean_data(df):
    df = df[df['Nombre'].str.contains("BRAVA") == False]  # Excluir BRAVA
    df['TotalVistas5Videos'] = df[[f"Video{i}_Vistas" for i in range(1,6)]].sum(axis=1)
    df['PromedioVistas5'] = df['TotalVistas5Videos'] / 5
    df['RatioVistasSuscriptor'] = df['PromedioVistas5'] / df['Suscriptores'].replace(0, 1)
    df['Engagement'] = (
        df[[f"Video{i}_Likes" for i in range(1,6)]].sum(axis=1) +
        df[[f"Video{i}_Comentarios" for i in range(1,6)]].sum(axis=1)
    ) / df['TotalVistas5Videos'].replace(0, 1)
    return df.sort_values(by='RatioVistasSuscriptor', ascending=False)

# Gráfico ranking
def generate_ranking_chart(df):
    top10 = df.head(10)
    plt.figure(figsize=(10, 6))
    sns.barplot(y='Nombre', x='RatioVistasSuscriptor', data=top10)
    plt.title("Top 10 canales por vistas/suscriptor")
    plt.xlabel("Vistas por suscriptor")
    plt.ylabel("Canal")
    now = datetime.now()
    output_file = os.path.join(OUTPUT_DIR, f"ranking_{now.strftime('%Y%m')}.png")
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"🖼️ Imagen guardada: {output_file}")

# Texto resumen para Instagram
def generate_instagram_text(df):
    now = datetime.now()
    top5 = df.head(5)
    resumen = f"\U0001F3C6 Top 5 por vistas/suscriptor ({now.strftime('%B %Y')}):\n"
    for idx, row in top5.iterrows():
        resumen += f"{row['Nombre']} — {round(row['RatioVistasSuscriptor'], 2)} vistas/suscriptor\n"
    resumen += "\n\U0001F4CA Medimos los últimos 5 videos en base a vistas, engagement, y relación con su base de seguidores."
    output_txt = os.path.join(OUTPUT_DIR, f"resumen_instagram_{now.strftime('%Y%m')}.txt")
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(resumen)
    print(f"📱 Texto para Instagram generado: {output_txt}")

# Texto resumen para LinkedIn
def generate_linkedin_text(df):
    now = datetime.now()
    resumen = (
        f"\U0001F4C8 Análisis mensual del ecosistema de streaming mendocino en YouTube ({now.strftime('%B %Y')}):\n\n"
        "Comparando los últimos 5 videos de cada canal según vistas promedio, engagement (likes y comentarios sobre vistas)"
        " y su relación con el total de suscriptores.\n\n"
    )
    for idx, row in df.head(5).iterrows():
        resumen += f"{idx+1}. {row['Nombre']} — {round(row['PromedioVistas5'])} vistas promedio\n"
    resumen += "\n#StreamingFederal #YouTubeMendoza #DatosQueHablan"
    output_txt = os.path.join(OUTPUT_DIR, f"resumen_linkedin_{now.strftime('%Y%m')}.txt")
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(resumen)
    print(f"💼 Texto para LinkedIn generado: {output_txt}")

# Ejecutar
if __name__ == "__main__":
    print("\U0001F680 Iniciando script generate_post.py...")
    df = load_data()
    df = clean_data(df)
    generate_ranking_chart(df)
    generate_instagram_text(df)
    generate_linkedin_text(df)
    print("✅ Script finalizado exitosamente.")


