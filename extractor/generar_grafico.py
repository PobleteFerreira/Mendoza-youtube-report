import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
from datetime import datetime

# 1. Configuración de rutas y estilo
# ... (inicio del script)
import os

# Usamos rutas absolutas basadas en la ubicación del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTAS_REPORTES = os.path.join(BASE_DIR, 'report_*.csv')
# ...
ARCHIVO_SALIDA_GRAFICO = 'grafico_ecosistema_mendoza.png'
plt.style.use('default') # Fondo blanco por defecto

def extraer_fecha(nombre_archivo):
    # Extrae MM-YYYY del nombre del archivo usando regex
    match = re.search(r'report_(\d{2})-(\d{4})', nombre_archivo)
    if match:
        return datetime.strptime(f"{match.group(1)}-{match.group(2)}", "%m-%Y")
    return None

def procesar_datos():
    # Buscamos en la raíz directamente
    archivos = glob.glob('report_*.csv')
    
    print(f"Archivos encontrados: {archivos}") # Esto saldrá en el log de GitHub
    
    if not archivos:
        print("ERROR: No se encontró ningún archivo que empiece con 'report_' y termine en '.csv'")
        return pd.DataFrame()

    datos_mensuales = []
    for archivo in archivos:
        fecha = extraer_fecha(archivo)
        if fecha:
            try:
                df = pd.read_csv(archivo)
                # Verificamos si la columna existe antes de sumar
                if 'VistasTotales' in df.columns:
                    vistas_totales = df['VistasTotales'].sum()
                    cantidad_canales = len(df)
                    datos_mensuales.append({
                        'fecha': fecha,
                        'vistas_acumuladas': vistas_totales,
                        'cantidad_canales': cantidad_canales
                    })
                else:
                    print(f"Advertencia: El archivo {archivo} no tiene la columna 'VistasTotales'")
            except Exception as e:
                print(f"Error procesando {archivo}: {e}")

    df_final = pd.DataFrame(datos_mensuales).sort_values('fecha')
    if not df_final.empty:
        df_final['vistas_mensuales'] = df_final['vistas_acumuladas'].diff().fillna(0)
        df_final['nuevos_canales'] = df_final['cantidad_canales'].diff().fillna(0)
    
    return df_final

    # Ordenar por fecha cronológicamente
    df_final = pd.DataFrame(datos_mensuales).sort_values('fecha')

    # Calcular Variación Mensual (Diferencia entre el mes actual y el anterior)
    # El primer mes (Julio 2025) no tendrá variación previa, aparecerá como 0 o NaN
    df_final['vistas_mensuales'] = df_final['vistas_acumuladas'].diff().fillna(0)
    
    # Calcular si entraron canales nuevos
    df_final['nuevos_canales'] = df_final['cantidad_canales'].diff().fillna(0)
    
    return df_final

def generar_visualizacion(df):
    # Crear figura con fondo blanco y alta resolución para redes
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150, facecolor='white')
    ax.set_facecolor('white')

    # Configurar el eje X con los nombres de los meses
    df['mes_label'] = df['fecha'].dt.strftime('%b %Y')
    
    # Dibujar el área sombreada y la línea principal
    ax.fill_between(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', alpha=0.1)
    ax.plot(df['mes_label'], df['vistas_mensuales'], color='#2c3e50', linewidth=3, marker='o', markersize=8)

    # Añadir líneas verticales suaves cuando entran nuevos canales
    for i, row in df.iterrows():
        if row['nuevos_canales'] > 0:
            ax.axvline(x=i, color='#bdc3c7', linestyle='--', linewidth=1, alpha=0.7)
            ax.text(i, ax.get_ylim()[1]*0.9, f"+{int(row['nuevos_canales'])} canales", 
                    color='#7f8c8d', rotation=90, verticalalignment='top', fontsize=9, fontweight='bold')

    # Título dinámico
    ultima_fecha = df['fecha'].iloc[-1].strftime('%B %Y')
    plt.title(f'Ecosistema de Streaming Mendoza: Reporte {ultima_fecha}', 
              fontsize=16, pad=20, fontweight='bold', color='#2c3e50')
    
    # Subtítulo con el estado actual
    total_canales = int(df['cantidad_canales'].iloc[-1])
    plt.suptitle(f'Monitoreo de {total_canales} canales locales | Datos: YouTube API', 
                 fontsize=10, y=0.92, color='#7f8c8d')

    # Formatear eje Y para que sea legible (ej: 1.5M en lugar de 1500000)
    def format_vistas(x, pos):
        if x >= 1e6: return f'{x*1e-6:.1f}M'
        if x >= 1e3: return f'{x*1e-3:.0f}k'
        return f'{x:.0f}'
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_vistas))
    
    # Estética de los ejes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', colors='#34495e')
    ax.set_ylabel('Visualizaciones del Mes', fontsize=11, fontweight='bold', color='#2c3e50')
    
    plt.grid(axis='y', linestyle=':', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Guardar imagen
    plt.savefig(ARCHIVO_SALIDA_GRAFICO, facecolor='white', bbox_inches='tight')
    print(f"Gráfico actualizado: {ARCHIVO_SALIDA_GRAFICO}")

if __name__ == "__main__":
    df_procesado = procesar_datos()
    if not df_procesado.empty:
        generar_visualizacion(df_procesado)
    else:
        print("No se encontraron archivos de reporte en la ruta especificada.")
