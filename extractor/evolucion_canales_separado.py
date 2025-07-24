import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

# === CONFIG ===
input_dir = Path("data/canales")
output_dir = input_dir / "graficos"
output_dir.mkdir(parents=True, exist_ok=True)

# === Buscar archivos mensuales ===
csv_files = sorted(input_dir.glob("report_*.csv"))

dataframes = []
for file in csv_files:
    match = re.search(r'report_(\d{2})-(\d{4})\.csv', file.name)
    if not match:
        continue
    mes, anio = match.groups()
    fecha = datetime.strptime(f"{mes}-{anio}", "%m-%Y")
    periodo = fecha.strftime("%b %y")  # Ej: Jul 25
    df = pd.read_csv(file)
    df['Periodo'] = periodo
    dataframes.append(df)

if not dataframes:
    print("⚠️ No se encontraron reportes.")
    exit()

df_total = pd.concat(dataframes, ignore_index=True)

# === Asegurar tipo numérico ===
for col in ['Suscriptores', 'VistasTotales', 'CantidadVivosMes']:
    df_total[col] = pd.to_numeric(df_total[col], errors='coerce')
df_total = df_total.dropna(subset=['Suscriptores'])

# === Generar 3 gráficos por canal ===
canales = df_total['Nombre'].unique()

for canal in canales:
    canal_df = df_total[df_total['Nombre'] == canal].sort_values('Periodo')
    nombre_archivo = canal.replace(" ", "_").replace("/", "_")

    # 1. Suscriptores
    plt.figure(figsize=(10, 4))
    plt.plot(canal_df['Periodo'], canal_df['Suscriptores'], marker='o', color='tab:blue')
    plt.title(f"{canal} - Suscriptores por mes")
    plt.xlabel("Periodo")
    plt.ylabel("Suscriptores")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / f"{nombre_archivo}_suscriptores.png")
    plt.close()

    # 2. Vistas Totales
    plt.figure(figsize=(10, 4))
    plt.plot(canal_df['Periodo'], canal_df['VistasTotales'], marker='s', color='tab:orange')
    plt.title(f"{canal} - Visualizaciones Totales por mes")
    plt.xlabel("Periodo")
    plt.ylabel("Vistas Totales")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / f"{nombre_archivo}_vistas.png")
    plt.close()

    # 3. Cantidad de Vivos
    plt.figure(figsize=(10, 4))
    plt.plot(canal_df['Periodo'], canal_df['CantidadVivosMes'], marker='^', color='tab:green')
    plt.title(f"{canal} - Cantidad de Vivos por mes")
    plt.xlabel("Periodo")
    plt.ylabel("Vivos")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / f"{nombre_archivo}_vivos.png")
    plt.close()

print(f"✅ Gráficos separados generados por canal en: {output_dir}")
