import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
from datetime import datetime

# 1. Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# '..' sube un nivel para salir de /extractor y entrar a /data/canales
RUTAS_REPORTES = os.path.join(BASE_DIR, '..', 'data', 'canales', 'report_*.csv')
ARCHIVO_SALIDA_GRAFICO = os.path.join(BASE_DIR, '..', 'grafico_ecosistema_mendoza.png')

def extraer_fecha(nombre_archivo):
    # Busca el formato report_MM-YYYY.csv
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

    # Ordenamos por fecha para que el cálculo de diferencia sea correcto
    df_final = pd.DataFrame(datos_mensuales).sort_values('fecha')
    
    if len(df_final) > 1:
        # CALCULAMOS DIFERENCIAS (Aquí Agosto usa a Julio para compararse)
        df_final['vistas_mensuales'] = df_final['vistas_acumuladas'].diff()
        df_final['nuevos_canales'] = df_final['cantidad_canales'].diff()
        
        # Guardamos cuántos canales hay en el primer mes visible (Agosto)
        canales_base_agosto = df_final['cantidad_canales'].iloc[1]
        
        # FILTRADO: Quitamos el primer mes (Julio) de la visualización 
        # pero ya habiendo usado sus datos para el cálculo de Agosto
        df_grafico = df_final.iloc[1:].copy()
        df_grafico.attrs['base_canales'] = canales_agosto_base = canales_base_agosto
        return df_grafico
    
    return df_final

def generar_visualizacion(df):
    # Estilo y colores (Oscuro y sobrio para investigación)
    fig, ax = plt.subplots(figsize=(13, 7), dpi=150, facecolor='white')
    df['mes_label'] = df['fecha'].dt.strftime('%b %Y')
    
    # Gráfico de área y línea principal
    ax.fill_between(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', alpha=0.1)
    ax.plot(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', linewidth=3, marker='o', markersize=7)

    # --- LÍNEA DE INICIO (Base de canales) ---
    ax.axvline(x=0, color='#34495e', linestyle='-', linewidth=2, alpha=0.8)
    canales_base = df.attrs.get('base_canales', 0)
    ax.text(0.05, ax.get_ylim()[1]*0.9, f"Inicio: {int(canales_base)} canales", 
            rotation=90, color='#34495e', fontsize=11, fontweight='bold', verticalalignment='top')

    # Líneas para canales nuevos (Hitos del corpus)
    # i=0 es Agosto, por eso empezamos a buscar hitos desde ahí
    for i, (idx, row) in enumerate(df.iterrows()):
        if row['nuevos_canales'] > 0:
            ax.axvline(x=i, color='#bdc3c7', linestyle='--', alpha=0.6)
            ax.text(i, ax.get_ylim()[1]*0.8, f"+{int(row['nuevos_canales'])} canales", 
                    rotation=90, color='#7f8c8d', fontsize=9)

    # Títulos y Etiquetas
    ultima_fecha = df['fecha'].iloc[-1].strftime('%B %Y')
    plt.title(f'Ecosistema de Streaming Mendoza: Crecimiento de Vistas ({ultima_fecha})', 
              fontsize=15, fontweight='bold', pad=25, color='#2c3e50')
    
    # Formato de números en eje Y (M para Millones, k para Miles)
    def format_vistas(x, pos):
        if x >= 1e6: return f'{x*1e-6:.1f}M'
        if x >= 1e3: return f'{x*1e-3:.0f}k'
        return f'{x:.0f}'
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_vistas))
    
    # Limpieza visual
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.grid(axis='y', linestyle=':', alpha=0.4)
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()

    # Guardado en la raíz para el README o el bot
    plt.savefig(ARCHIVO_SALIDA_GRAFICO, facecolor='white', bbox_inches='tight')
    print(f"Éxito: Gráfico guardado en {ARCHIVO_SALIDA_GRAFICO}")

if __name__ == "__main__":
    df_procesado = procesar_datos()
    if not df_procesado.empty:
        generar_visualizacion(df_procesado)
    else:
        print("Error: No hay datos suficientes para graficar.")
