import os
import pandas as pd
from pathlib import Path
import glob

# === Configuración de rutas ===
CANAL_DIR = Path("data/canales")
VIDEOS_ROOT = Path("data/videos")
OUT_DIR = Path("data/informes")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# === Seleccionar el reporte más reciente ===
report_files = sorted(CANAL_DIR.glob('report_*.csv'))
if not report_files:
    raise FileNotFoundError("No se encontró ningún archivo report_*.csv en data/canales")
summary_path = report_files[-1]
# Obtener mes-año del nombre de archivo
month_year = summary_path.stem.replace('report_', '')

# === Leer resumen general ===
df_summary = pd.read_csv(summary_path, encoding='utf-8')
# Excluir Vorterix (radio)
df_summary = df_summary[~df_summary['Nombre'].str.lower().eq('vorterix')]

# === Acumular vistas de vivos ===n
data_records = []
for _, row in df_summary.iterrows():
    canal_id = row['CanalID']
    canal_nombre = row['Nombre']
    subs = pd.to_numeric(row['Suscriptores'], errors='coerce').fillna(0).astype(int)
    vivos_count = pd.to_numeric(row['CantidadVivosMes'], errors='coerce').fillna(0).astype(int)

    # Buscar todos los CSV de videos en la carpeta del canal
    canal_folder = VIDEOS_ROOT / f"canal_{canal_id}"
    view_sum = 0
    if canal_folder.exists():
        for csv_file in canal_folder.glob(f'videos_{month_year}.csv'):
            df_v = pd.read_csv(csv_file)
            if 'view_count' in df_v.columns:
                view_sum += pd.to_numeric(df_v['view_count'], errors='coerce').fillna(0).sum()
    
    # Calcular ratio de vistas de vivos por suscriptor
    ratio_vivos_subs = view_sum / subs if subs > 0 else 0

    data_records.append({
        'CanalID': canal_id,
        'Nombre': canal_nombre,
        'Suscriptores': subs,
        'VistasVivos30': view_sum,
        'CantidadVivos30': vivos_count,
        'RatioVivosSubs': round(ratio_vivos_subs, 4)
    })

# === Crear tabla y exportar ===
df_table = pd.DataFrame(data_records)
# Ordenar de mayor a menor ratio
df_table = df_table.sort_values('RatioVivosSubs', ascending=False)

# Guardar resultados
output_csv = OUT_DIR / f"tabla_vivos_ratio_{month_year}.csv"
df_table.to_csv(output_csv, index=False)
print(f"Tabla generada: {output_csv}")
print(df_table)
