import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
from datetime import datetime

# 1. Configuración de rutas (Saliendo de 'extractor' hacia 'data/canales')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTAS_REPORTES = os.path.join(BASE_DIR, '..', 'data', 'canales', 'report_*.csv')
ARCHIVO_SALIDA_GRAFICO = os.path.join(BASE_DIR, '..', 'grafico_ecosistema_mendoza.png')

def extraer_fecha(nombre_archivo):
    match = re.search(r'report_(\d{2})-(\d{4})', nombre_archivo)
    if match:
        return datetime.strptime(f"{match.group(1)}-{match.group(2)}", "%m-%Y")
    return None

def procesar_datos():
    archivos = glob.glob(RUTAS_REPORTES)
    print(f"Archivos encontrados: {len(archivos)}")
    
    if not archivos:
        return pd.DataFrame()

    datos_mensuales = []
    for archivo in archivos:
        fecha = extraer_fecha(archivo)
        if fecha:
            try:
                df = pd.read_csv(archivo)
                if 'VistasTotales' in df.columns:
                    vistas_totales = df['VistasTotales'].sum()
                    cantidad_canales = len(df)
                    datos_mensuales.append({
                        'fecha': fecha,
                        'vistas_acumuladas': vistas_totales,
                        'cantidad_canales': cantidad_canales
                    })
            except Exception as e:
                print(f"Error procesando {archivo}: {e}")

    df_final = pd.DataFrame(datos_mensuales).sort_values('fecha')
    if not df_final.empty:
        # Calcula la variación mensual real (vistas del mes)
        df_final['vistas_mensuales'] = df_final['vistas_acumuladas'].diff().fillna(df_final['vistas_acumuladas'].iloc[0])
        df_final['nuevos_canales'] = df_final['cantidad_canales'].diff().fillna(0)
    
    return df_final

def generar_visualizacion(df):
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150, facecolor='white')
    ax.set_facecolor('white')

    df['mes_label'] = df['fecha'].dt.strftime('%b %Y')
    
    # Gráfico de área y línea
    ax.fill_between(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', alpha=0.1)
    ax.plot(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', linewidth=3, marker='o', markersize=8)

    # Líneas verticales para nuevos canales (Hitos)
    for i, row in df.iterrows():
        if row['nuevos_canales'] > 0:
            ax.axvline(x=i, color='#bdc3c7', linestyle='--', linewidth=1, alpha=0.7)
            ax.text(i, ax.get_ylim()[1]*0.9, f"+{int(row['nuevos_canales'])} canales", 
                    color='#7f8c8d', rotation=90, verticalalignment='top', fontsize=9, fontweight='bold')

    # Títulos dinámicos
    ultima_fecha = df['fecha'].iloc[-1].strftime('%B %Y')
    plt.title(f'Ecosistema de Streaming Mendoza: Reporte {ultima_fecha}', 
              fontsize=16, pad=20, fontweight='bold', color='#2c3e50')
    
    total_canales = int(df['cantidad_canales'].iloc[-1])
    plt.suptitle(f'Monitoreo de {total_canales} canales locales | Datos: YouTube API', 
                 fontsize=10, y=0.92, color='#7f8c8d')

    # Formato de números en eje Y
    def format_vistas(x, pos):
        if x >= 1e6: return f'{x*1e-6:.1f}M'
        if x >= 1e3: return f'{x*1e-3:.0f}k'
        return f'{x:.0f}'
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_vistas))
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.grid(axis='y', linestyle=':', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(ARCHIVO_SALIDA_GRAFICO, facecolor='white', bbox_inches='tight')
    print(f"Éxito: Gráfico guardado en {ARCHIVO_SALIDA_GRAFICO}")

if __name__ == "__main__":
    df_procesado = procesar_datos()
    if not df_procesado.empty:
        generar_visualizacion(df_procesado)
    else:
        print("Error: No se pudieron procesar datos de los CSV.")
