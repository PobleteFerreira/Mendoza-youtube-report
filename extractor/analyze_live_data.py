import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import matplotlib.ticker as ticker

# Configuración general
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10
})

def cargar_datos(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df['Canal'] = df['Canal'].astype(str)
    return df

def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    resumen = df.groupby('Canal').agg({
        'Visualizaciones': ['sum', 'count']
    }).reset_index()
    resumen.columns = ['Canal', 'TotalVisualizaciones', 'Transmisiones']
    resumen['PromedioPorTransmision'] = (resumen['TotalVisualizaciones'] / resumen['Transmisiones']).fillna(0).round(1)
    return resumen.sort_values('TotalVisualizaciones', ascending=False)

def generar_graficos(df: pd.DataFrame, fecha_analisis: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Tonos pasteles
    colores = plt.cm.Pastel1.colors

    # Gráfico 1: Visualizaciones totales por canal
    plt.figure(figsize=(10, 6))
    df_plot = df.sort_values("TotalVisualizaciones", ascending=True)
    plt.barh(df_plot["Canal"], df_plot["TotalVisualizaciones"], color=colores)
    plt.title(f"🔴 Visualizaciones en Vivo por Canal — {fecha_analisis}")
    plt.xlabel("Visualizaciones Totales")
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'.replace(',', '.')))
    plt.tight_layout()
    plt.savefig(output_dir / f"vivo_total_{fecha_analisis.replace('-', '')}.png")
    plt.close()

    # Gráfico 2: Promedio por transmisión
    plt.figure(figsize=(10, 6))
    df_plot = df.sort_values("PromedioPorTransmision", ascending=True)
    plt.barh(df_plot["Canal"], df_plot["PromedioPorTransmision"], color=colores)
    plt.title(f"📊 Promedio de Visualizaciones por Transmisión — {fecha_analisis}")
    plt.xlabel("Visualizaciones promedio")
    plt.tight_layout()
    plt.savefig(output_dir / f"vivo_promedio_{fecha_analisis.replace('-', '')}.png")
    plt.close()

def generar_resumen_redes(df_resultado: pd.DataFrame, fecha_analisis: str, output_dir: Path):
    resumen_lines = [f"📊 Resumen de Transmisiones en Vivo — {fecha_analisis}", ""]
    
    top_canales = df_resultado.sort_values("TotalVisualizaciones", ascending=False).head(5)
    resumen_lines.append("🏆 Top 5 canales por visualizaciones en vivo:")
    for _, row in top_canales.iterrows():
        resumen_lines.append(f"• {row['Canal']} — {row['TotalVisualizaciones']} vistas en {row['Transmisiones']} transmisiones")
    
    promedio_transmisiones = df_resultado['Transmisiones'].mean()
    resumen_lines.append("")
    resumen_lines.append(f"📈 Promedio de transmisiones por canal: {promedio_transmisiones:.1f}")
    
    df_inactivos = df_resultado[df_resultado['Transmisiones'] == 0]
    if not df_inactivos.empty:
        resumen_lines.append("")
        resumen_lines.append("🛑 Canales sin transmisiones en vivo este mes:")
        for _, row in df_inactivos.iterrows():
            resumen_lines.append(f"• {row['Canal']}")
    
    resumen_txt = "\n".join(resumen_lines)
    resumen_path = output_dir / f"resumen_vivo_{fecha_analisis.replace('-', '')}.txt"
    with open(resumen_path, "w", encoding="utf-8") as f:
        f.write(resumen_txt)
    
    print(f"📝 Resumen para redes guardado en: {resumen_path}")

def main():
    fecha_analisis = datetime.now().strftime("%B %Y")
    carpeta_input = Path("data/live")
    carpeta_output = Path("output/live_analysis")
    
    archivos = sorted(carpeta_input.glob("*.csv"))
    if not archivos:
        print("⚠️ No se encontraron archivos de datos en 'data/live'")
        return

    archivo_mas_reciente = archivos[-1]
    print(f"📄 Procesando archivo: {archivo_mas_reciente.name}")
    
    df = cargar_datos(archivo_mas_reciente)
    df_resultado = procesar_datos(df)
    generar_graficos(df_resultado, fecha_analisis, carpeta_output)
    generar_resumen_redes(df_resultado, fecha_analisis, carpeta_output)
    print("✅ Análisis finalizado.")

if __name__ == "__main__":
    main()

