import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
from datetime import datetime

# 1. Configuración de rutas
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
        # Guardamos la cantidad inicial antes de filtrar
        canales_iniciales = df_final['cantidad_canales'].iloc[0]
        
        df_final['vistas_mensuales'] = df_final['vistas_acumuladas'].diff()
        df_final['nuevos_canales'] = df_final['cantidad_canales'].diff()
        
        # Eliminamos la primera fila para limpiar la escala de vistas
        df_final = df_final.dropna(subset=['vistas_mensuales'])
        
        # Guardamos el valor inicial como atributo del DataFrame para usarlo en el gráfico
        df_final.attrs['base_canales'] = canales_iniciales
        
    return df_final

def generar_visualizacion(df):
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150, facecolor='white')
    df['mes_label'] = df['fecha'].dt.strftime('%b %Y')
    
    # Gráfico de área y línea
    ax.fill_between(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', alpha=0.1)
    ax.plot(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', linewidth=3, marker='o')

    # --- NUEVA LÍNEA DE INICIO ---
    # Colocamos una línea al principio indicando la base
    ax.axvline(x=0, color='#34495e', linestyle='-', linewidth=1.5, alpha=0.8)
    canales_base = df.attrs.get('base_canales', 0)
    ax.text(0, ax.get_ylim()[1]*0.95, f"Inicio: {int(canales_base)} canales", 
            rotation=90, color='#34495e', fontsize=10, fontweight='bold', verticalalignment='top')

    # Líneas para los canales que se van sumando (igual que antes)
    for i, (idx, row) in enumerate(df.iterrows()):
        if row['nuevos_canales'] > 0:
            ax.axvline(x=i, color='#bdc3c7', linestyle='--', alpha=0.7)
            ax.text(i, ax.get_ylim()[1]*0.85, f"+{int(row['nuevos_canales'])} canales", 
                    rotation=90, color='#7f8c8d', fontsize=9)

    # Títulos y formato
    ultima_fecha = df['fecha'].iloc[-1].strftime('%B %Y')
    plt.title(f'Ecosistema de Streaming Mendoza: Crecimiento Mensual ({ultima_fecha})', 
              fontsize=14, fontweight='bold', pad=20)
    
    def format_vistas(x, pos):
        if x >= 1e6: return f'{x*1e-6:.1f}M'
        return f'{x*1e-3:.0f}k' if x >= 1e3 else f'{x:.0f}'
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_vistas))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle=':', alpha=0.3)
    plt.tight_layout()

    plt.savefig(ARCHIVO_SALIDA_GRAFICO, bbox_inches='tight')
    print(f"Gráfico actualizado guardado en {ARCHIVO_SALIDA_GRAFICO}")

if __name__ == "__main__":
    df_procesado = procesar_datos()
    if not df_procesado.empty:
        generar_visualizacion(df_procesado)
