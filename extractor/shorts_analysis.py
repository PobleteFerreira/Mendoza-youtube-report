#!/usr/bin/env python3
"""
Analiza Shorts de YouTube de una lista de canales.
Extrae métricas de videos de hasta 60 segundos publicados recientemente,
y registra el uso de cuota de la API para debug.

Requiere:
- extractor/channels.csv con CanalID/Nombre o channel_id/channel_url
- YOUTUBE_API_KEY en variables de entorno

Salida:
- data/shorts/shorts_YYYY-MM.csv
"""

import os
import time
import requests
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from isodate import parse_duration
from dotenv import load_dotenv

# ————— Configuración logging —————
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

# ————— Carga API key —————
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY", "")
if not API_KEY:
    log.error("YOUTUBE_API_KEY no está configurada.")
    exit(1)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

# ————— Contadores de cuota —————
SEARCH_COST = 100    # unidades por search.list call
VIDEOS_COST = 1      # unidades por videos.list call (por chunk)
search_calls = 0
videos_calls = 0

# ————— Paths —————
CHANNELS_FILE = Path("extractor/channels.csv")
OUTPUT_DIR = Path("data/shorts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_recent_videos(channel_id, max_results=50):
    global search_calls
    search_calls += 1

    url = f"{YOUTUBE_API_URL}/search"
    params = {
        "key": API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "maxResults": max_results,
        "order": "date",
        "type": "video"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    log.info(f"🔍 search.list para canal {channel_id}: {len(items)} videos obtenidos")
    # Log de ejemplo
    if items:
        ejemplo = items[0]
        log.debug(f"   Ejemplo search item: {ejemplo}")
    return items

def get_video_details(video_ids):
    global videos_calls
    all_items = []
    url = f"{YOUTUBE_API_URL}/videos"
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        videos_calls += 1
        params = {
            "key": API_KEY,
            "id": ",".join(chunk),
            "part": "snippet,contentDetails,statistics"
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        log.info(f"🔍 videos.list (chunk {i//50+1}) → {len(items)} detalles obtenidos")
        for v in items:
            stats = v.get("statistics", {})
            if "viewCount" not in stats:
                log.warning(f"⚠️ Faltan estadísticas para {v['id']}: {stats}")
        if items:
            log.debug(f"   Ejemplo videos item: {items[0]}")
        all_items.extend(items)
    return all_items

def extract_shorts_metrics(canal_id, canal_nombre):
    videos = get_recent_videos(canal_id)
    video_ids = [v["id"]["videoId"] for v in videos if v.get("id", {}).get("videoId")]
    if not video_ids:
        return []
    details = get_video_details(video_ids)
    shorts = []
    for v in details:
        try:
            duration = parse_duration(v["contentDetails"]["duration"]).total_seconds()
            if duration > 60:
                continue
            snippet = v["snippet"]
            stats = v.get("statistics", {})
            vistas = int(stats.get("viewCount", 0))
            shorts.append({
                "CanalID": canal_id,
                "Nombre": canal_nombre,
                "VideoID": v["id"],
                "Titulo": snippet["title"],
                "Fecha": snippet["publishedAt"][:10],
                "Vistas": vistas,
                "Likes": int(stats.get("likeCount", 0)),
                "Comentarios": int(stats.get("commentCount", 0)),
                "DuracionSeg": int(duration),
                "URL": f"https://youtube.com/shorts/{v['id']}"
            })
        except Exception as e:
            log.error(f"⚠️ Error procesando video {v.get('id')}: {e}")
    return shorts

def main():
    global search_calls, videos_calls

    df_canales = pd.read_csv(CHANNELS_FILE)
    # detectar esquema
    if {"CanalID","Nombre"}.issubset(df_canales.columns):
        id_col, name_col = "CanalID","Nombre"
    elif {"channel_id","channel_url"}.issubset(df_canales.columns):
        id_col, name_col = "channel_id","channel_url"
    else:
        log.error("El CSV no tiene columnas esperadas.")
        return

    mes = datetime.utcnow().strftime("%Y-%m")
    salida = OUTPUT_DIR / f"shorts_{mes}.csv"
    all_data = []

    for _, row in df_canales.iterrows():
        cid, cname = row[id_col], row[name_col]
        log.info(f"🔄 Procesando canal: {cname} ({cid})")
        data = extract_shorts_metrics(cid, cname)
        all_data.extend(data)
        time.sleep(1)

    if all_data:
        pd.DataFrame(all_data).to_csv(salida, index=False)
        log.info(f"✅ Archivo guardado: {salida}")
    else:
        log.warning("⚠️ No se encontraron Shorts este mes.")

    # Reporte de cuota
    total_quota = search_calls * SEARCH_COST + videos_calls * VIDEOS_COST
    log.info("––––––––––––––––––––––––––––––––")
    log.info(f"📊 Llamadas search.list: {search_calls} × {SEARCH_COST}u = {search_calls*SEARCH_COST}u")
    log.info(f"📊 Llamadas videos.list: {videos_calls} × {VIDEOS_COST}u = {videos_calls*VIDEOS_COST}u")
    log.info(f"⚖️ Cuota total aproximada gastada: {total_quota} unidades")
    log.info("––––––––––––––––––––––––––––––––")

if __name__ == "__main__":
    main()
