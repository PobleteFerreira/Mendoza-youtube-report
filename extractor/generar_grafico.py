import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
from datetime import datetime

# Configuramos las rutas para que funcionen desde la carpeta /extractor
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# '..' significa "subir un nivel" para encontrar la carpeta 'data'
RUTAS_REPORTES = os.path.join(BASE_DIR, '..', 'data', 'canales', 'report_*.csv')
# Guardamos el gráfico en la raíz del proyecto para que se vea en el README
ARCHIVO_SALIDA_GRAFICO = os.path.join(BASE_DIR, '..', 'grafico_ecosistema_mendoza.png')

def extraer_fecha(nombre_archivo):
    match = re.search(r'report_(\d{2})-(\d{4})', nombre_archivo)
    if match:
        return datetime.strptime(f"{match.group(1)}-{match.group(2)}", "%m-%Y")
    return None

def procesar_datos():
    archivos = glob.glob(RUTAS_REPORTES)
    if not archivos:
        print(f"No se encontraron archivos en: {RUTAS_REPORTES}")
        return pd.DataFrame()

    datos_mensuales = []
    for archivo in archivos:
        fecha = extraer_fecha(archivo)
        if fecha:
            try:
                df = pd.read_csv(archivo)
                if 'VistasTotales' in df.columns:
                    datos_mensuales.append({
                        'fecha': fecha,
                        'vistas_acumuladas': df['VistasTotales'].sum(),
                        'cantidad_canales': len(df)
                    })
            except Exception as e:
                print(f"Error en {archivo}: {e}")

    df_final = pd.DataFrame(datos_mensuales).sort_values('fecha')
    if not df_final.empty:
        df_final['vistas_mensuales'] = df_final['vistas_acumuladas'].diff().fillna(df_final['vistas_acumuladas'].iloc[0])
        df_final['nuevos_canales'] = df_final['cantidad_canales'].diff().fillna(0)
    return df_final

def generar_visualizacion(df):
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150, facecolor='white')
    df['mes_label'] = df['fecha'].dt.strftime('%b %Y')
    
    ax.fill_between(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', alpha=0.1)
    ax.plot(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', linewidth=3, marker='o')

    for i, row in df.iterrows():
        if row['nuevos_canales'] > 0:
            ax.axvline(x=i, color='#bdc3c7', linestyle='--', alpha=0.7)
            ax.text(i, ax.get_ylim()[1]*0.9, f"+{int(row['nuevos_canales'])} canales", 
                    rotation=90, color='#7f8c8d', fontsize=9)

    ultima_fecha = df['fecha'].iloc[-1].strftime('%B %Y')
    plt.title(f'Ecosistema de Streaming Mendoza: Reporte {ultima_fecha}', fontweight='bold')
    
    def format_vistas(x, pos):
        if x >= 1e6: return f'{x*1e-6:.1f}M'
        return f'{x*1e-3:.0f}k' if x >= 1e3 else f'{x:.0f}'
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_vistas))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(ARCHIVO_SALIDA_GRAFICO, bbox_inches='tight')

if __name__ == "__main__":
    df = procesar_datos()
    if not df.empty:
        generar_visualizacion(df)
        print("Gráfico generado con éxito.")
