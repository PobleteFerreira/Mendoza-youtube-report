#!/usr/bin/env python3
"""
Analiza Shorts de YouTube de una lista de canales.
Extrae métricas de videos de hasta 60 segundos publicados recientemente.

Requiere:
- Archivo extractor/channels.csv con columnas: CanalID,Nombre
- Variable de entorno YOUTUBE_API_KEY (configurada como secret en GitHub Actions)

Salida:
- data/shorts/shorts_YYYY-MM.csv
"""

import os
import csv
import time
import requests
from datetime import datetime
from pathlib import Path

import pandas as pd
from isodate import parse_duration
from dotenv import load_dotenv

# Cargar API Key desde variable de entorno
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

# Cargar lista de canales
CHANNELS_FILE = Path("extractor/channels.csv")
OUTPUT_DIR = Path("data/shorts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_recent_videos(channel_id, max_results=50):
    """Devuelve los últimos videos de un canal."""
    url = f"{YOUTUBE_API_URL}/search"
    params = {
        "key": API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "maxResults": max_results,
        "order": "date",
        "type": "video"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("items", [])

def get_video_details(video_ids):
    """Devuelve los detalles de una lista de videos."""
    url = f"{YOUTUBE_API_URL}/videos"
    params = {
        "key": API_KEY,
        "id": ",".join(video_ids),
        "part": "snippet,contentDetails,statistics"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("items", [])

def extract_shorts_metrics(canal_id, canal_nombre):
    videos = get_recent_videos(canal_id, max_results=50)
    video_ids = [v["id"]["videoId"] for v in videos]

    if not video_ids:
        return []

    details = get_video_details(video_ids)
    shorts = []

    for v in details:
        try:
            duration = parse_duration(v["contentDetails"]["duration"]).total_seconds()
            if duration > 60:
                continue  # no es un Short

            snippet = v["snippet"]
            stats = v.get("statistics", {})
            shorts.append({
                "CanalID": canal_id,
                "Nombre": canal_nombre,
                "VideoID": v["id"],
                "Titulo": snippet["title"],
                "Fecha": snippet["publishedAt"][:10],
                "Vistas": int(stats.get("viewCount", 0)),
                "Likes": int(stats.get("likeCount", 0)),
                "Comentarios": int(stats.get("commentCount", 0)),
                "DuracionSeg": int(duration),
                "URL": f"https://youtube.com/shorts/{v['id']}"
            })
        except Exception as e:
            print(f"⚠️ Error con video {v.get('id')}: {e}")
    return shorts

def main():
    df_canales = pd.read_csv(CHANNELS_FILE)
    mes_actual = datetime.utcnow().strftime("%Y-%m")
    salida = OUTPUT_DIR / f"shorts_{mes_actual}.csv"

    todos_los_datos = []

    for _, row in df_canales.iterrows():
        canal_id = row["CanalID"]
        nombre = row["Nombre"]
        print(f"🔍 Procesando canal: {nombre}")
        datos = extract_shorts_metrics(canal_id, nombre)
        todos_los_datos.extend(datos)
        time.sleep(1)

    if todos_los_datos:
        df = pd.DataFrame(todos_los_datos)
        df.to_csv(salida, index=False)
        print(f"✅ Archivo guardado: {salida}")
    else:
        print("⚠️ No se encontraron Shorts este mes.")

if __name__ == "__main__":
    main()
