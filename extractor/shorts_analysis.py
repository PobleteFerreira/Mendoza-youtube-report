#!/usr/bin/env python3
"""
Analytics de YouTube Shorts para canales listados en extractor/channels.csv.

Para cada canal:
 - Obtiene todos los vídeos “short” (< 4 min) publicados en los últimos 30 días
   vía search.list con videoDuration=short + publishedAfter.
 - Recupera detalles (título, reproducciones, me gusta, comentarios).
 - Genera dos CSV:
     • shorts_summary_YYYY‑MM.csv: resumen por canal (cantidad + fechas primero/último).
     • shorts_details_YYYY‑MM.csv: fila por cada Short con sus métricas.
"""

import os
import time
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from isodate import parse_duration
from dotenv import load_dotenv

# — logging —
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger()

# — cargar API key —
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY", "")
if not API_KEY:
    log.error("YOUTUBE_API_KEY no está configurada.")
    exit(1)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

# — paths de entrada/salida —
CHANNELS_FILE = Path("extractor/channels.csv")
OUTPUT_DIR = Path("data/shorts_stats")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_shorts_for_channel(channel_id):
    """Trae todos los vídeos <4min de los últimos 30 días para un canal (search.list paginado)."""
    threshold = datetime.now(timezone.utc) - timedelta(days=30)
    params = {
        "key": API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "maxResults": 50,
        "order": "date",
        "type": "video",
        "videoDuration": "short",
        "publishedAfter": threshold.isoformat()
    }
    items = []
    while True:
        resp = requests.get(f"{YOUTUBE_API_URL}/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("items", [])
        log.info(f"🔍 search.list: obtuvo {len(batch)} vídeos")
        items.extend(batch)
        token = data.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
    return items

def get_video_details(video_ids):
    """Trae snippet+contentDetails+statistics para hasta 50 IDs por llamada."""
    details = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        resp = requests.get(
            f"{YOUTUBE_API_URL}/videos",
            params={
                "key": API_KEY,
                "id": ",".join(chunk),
                "part": "snippet,contentDetails,statistics"
            }
        )
        resp.raise_for_status()
        batch = resp.json().get("items", [])
        log.info(f"🔍 videos.list: obtuvo {len(batch)} detalles")
        details.extend(batch)
    return details

def main():
    df = pd.read_csv(CHANNELS_FILE)
    if {"CanalID","Nombre"}.issubset(df.columns):
        id_col, name_col = "CanalID","Nombre"
    elif {"channel_id","channel_url"}.issubset(df.columns):
        id_col, name_col = "channel_id","channel_url"
    else:
        log.error("El CSV no tiene columnas esperadas.")
        return

    summary_rows = []
    detail_rows = []

    for _, row in df.iterrows():
        cid, cname = row[id_col], row[name_col]
        log.info(f"🔄 Procesando canal: {cname} ({cid})")
        items = get_shorts_for_channel(cid)
        ids = [i["id"]["videoId"] for i in items if i.get("id",{}).get("videoId")]
        if not ids:
            log.warning(f"No se encontraron Shorts para {cname}")
            continue

        vids = get_video_details(ids)
        fechas = []
        for v in vids:
            try:
                pub = datetime.fromisoformat(
                    v["snippet"]["publishedAt"].replace("Z","+00:00")
                )
                fechas.append(pub.date())
                stats = v.get("statistics", {})
                detail_rows.append({
                    "CanalID": cid,
                    "Nombre": cname,
                    "VideoID": v["id"],
                    "Titulo": v["snippet"]["title"],
                    "Fecha": pub.date().isoformat(),
                    "Vistas": int(stats.get("viewCount",0)),
                    "Likes": int(stats.get("likeCount",0)),
                    "Comentarios": int(stats.get("commentCount",0))
                })
            except Exception as e:
                log.error(f"Error en video {v.get('id')}: {e}")

        count = len(fechas)
        first = min(fechas).isoformat() if fechas else ""
        last  = max(fechas).isoformat() if fechas else ""
        summary_rows.append({
            "CanalID": cid,
            "Nombre": cname,
            "CantidadShorts": count,
            "PrimerShort": first,
            "UltimoShort": last
        })

        time.sleep(1)  # respetar rate limits

    mes = datetime.utcnow().strftime("%Y-%m")
    pd.DataFrame(summary_rows).to_csv(
        OUTPUT_DIR / f"shorts_summary_{mes}.csv", index=False
    )
    pd.DataFrame(detail_rows).to_csv(
        OUTPUT_DIR / f"shorts_details_{mes}.csv", index=False
    )
    log.info(f"✅ Archivos guardados en {OUTPUT_DIR}")

if __name__=="__main__":
    main()

