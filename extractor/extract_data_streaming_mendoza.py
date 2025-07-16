#!/usr/bin/env python3
# extract_data_streaming_mendoza.py

import os
import csv
import re
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

import pandas as pd
from dateutil import parser as dtparser

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    raise ImportError("Falta instalar google-api-python-client. Ejecuta: pip install google-api-python-client")

# =======================
# CONFIGURACIÓN GENERAL
# =======================

DATA_DIR = Path(__file__).parent.parent / "data"
CANALES_DIR = DATA_DIR / "canales"
VIDEOS_DIR = DATA_DIR / "videos"
CHANNELS_CSV = Path(__file__).parent / "channels.csv"
MAX_VIDEOS_PER_CHANNEL = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# =======================
# CREDENCIALES API YOUTUBE
# =======================

def get_youtube_service():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if api_key:
        logging.info("Usando API Key de variable de entorno.")
        return build("youtube", "v3", developerKey=api_key)
    else:
        raise EnvironmentError(
            "No se encontró YOUTUBE_API_KEY en las variables de entorno."
        )

# =======================
# LECTURA DE CANALES
# =======================

def read_channels_csv(csv_path: Path) -> List[str]:
    channel_ids = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            channel_id = row.get("channel_id") or row.get("CanalID")
            if channel_id:
                channel_ids.append(channel_id.strip())
    logging.info(f"Se cargaron {len(channel_ids)} canales desde {csv_path}")
    return channel_ids

# =======================
# UTILIDADES DE FECHA Y ARCHIVOS
# =======================

def get_current_month_year():
    now = datetime.now()
    return f"{now.month:02d}-{now.year}"

def ensure_dirs():
    for directory in [CANALES_DIR, VIDEOS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

# =======================
# EXTRACCIÓN DE DATOS DEL CANAL
# =======================

def get_channel_data(youtube, channel_id: str) -> Dict:
    try:
        response = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()
        if not response["items"]:
            logging.warning(f"No se encontró el canal {channel_id}")
            return {}

        info = response["items"][0]
        snippet = info["snippet"]
        stats = info["statistics"]

        data = {
            "channel_id": channel_id,
            "channel_title": snippet.get("title", ""),
            "channel_url": f"https://www.youtube.com/channel/{channel_id}",
            "channel_description": snippet.get("description", ""),
            "channel_published_at": snippet.get("publishedAt", ""),
            "country": snippet.get("country", "Argentina"),
            "subscribers": int(stats.get("subscriberCount", 0)),
            "view_count": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0)),
        }
        return data
    except HttpError as e:
        logging.error(f"Error al consultar canal {channel_id}: {e}")
        return {}

# =======================
# BUSQUEDA DE VIVOS DEL MES
# =======================

def get_top_live_videos_last_month(youtube, channel_id: str, max_videos=10) -> List[Dict]:
    now = datetime.now()
    last_month = now - timedelta(days=31)
    iso_after = last_month.isoformat("T") + "Z"

    videos = []
    next_page = None

    while True:
        search_response = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            type="video",
            eventType="completed",
            publishedAfter=iso_after,
            maxResults=50,
            pageToken=next_page
        ).execute()

        for item in search_response["items"]:
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            published_at = snippet.get("publishedAt", "")
            videos.append({
                "video_id": video_id,
                "published_at": published_at,
                "title": snippet.get("title", ""),
            })

        next_page = search_response.get("nextPageToken")
        if not next_page or len(videos) >= 100:
            break

    if not videos:
        return []

    video_ids = [v["video_id"] for v in videos]
    video_details = []
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        details_response = youtube.videos().list(
            part="snippet,statistics,liveStreamingDetails",
            id=",".join(batch_ids)
        ).execute()
        for item in details_response["items"]:
            ls = item.get("liveStreamingDetails", {})
            vid = {
                "video_id": item["id"],
                "title": item["snippet"].get("title", ""),
                "description": item["snippet"].get("description", ""),
                "published_at": item["snippet"].get("publishedAt", ""),
                "view_count": int(item["statistics"].get("viewCount", 0)),
                "like_count": int(item["statistics"].get("likeCount", 0)),
                "comment_count": int(item["statistics"].get("commentCount", 0)),
                "video_url": f"https://www.youtube.com/watch?v={item['id']}",
                "liveStreamingDetails": ls
            }
            video_details.append(vid)

    video_details = sorted(video_details, key=lambda v: v["view_count"], reverse=True)
    return video_details[:max_videos]

# =======================
# ANÁLISIS DE DESCRIPCIONES Y PROGRAMAS
# =======================

PLATAFORMAS_PATTERNS = {
    "Cafecito": r"cafecito\.app",
    "MercadoPago": r"mercadopago\.com|mpago\.la",
    "PayPal": r"paypal\.me|paypal\.com",
    "Patreon": r"patreon\.com",
    "Twitch": r"twitch\.tv",
    "Instagram": r"instagram\.com|instagr\.am",
    "TikTok": r"tiktok\.com",
    "Discord": r"discord\.gg|discord\.com",
    "Telegram": r"t\.me|telegram\.me|telegram\.org",
    "Facebook": r"facebook\.com|fb\.me",
    "WebPropia": r"\.com\.ar|\.com|\.net|\.org",
    "OnlyFans": r"onlyfans\.com",
    "Sponsors/Apuestas": r"bet|casino|apuesta|sponsor|promo|descuento|código"
}

def detect_platforms(text: str) -> List[str]:
    detected = []
    if not text:
        return detected
    for plat, pattern in PLATAFORMAS_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            detected.append(plat)
    return detected

def extract_links(text: str) -> List[str]:
    if not text:
        return []
    return re.findall(r'https?://[^\s)]+', text)

def guess_program_title(titles: List[str], min_count=2) -> Dict[str, int]:
    prefix_counter = {}
    for title in titles:
        m = re.match(r"(.+?)[\s\-:|]+", title)
        prefix = m.group(1).strip() if m else title.split()[0]
        if prefix in prefix_counter:
            prefix_counter[prefix] += 1
        else:
            prefix_counter[prefix] = 1
    return {k: v for k, v in prefix_counter.items() if v >= min_count}

def assign_program_name(title: str, program_prefixes: List[str]) -> str:
    for prefix in sorted(program_prefixes, key=len, reverse=True):
        if title.startswith(prefix):
            return prefix
    return ""

def calculate_periodicity(video_dates: List[str]) -> Tuple[int, Optional[float]]:
    if len(video_dates) < 2:
        return len(video_dates), None
    sorted_dates = sorted(datetime.fromisoformat(d.replace('Z', '')) for d in video_dates)
    diffs = [(sorted_dates[i] - sorted_dates[i-1]).days for i in range(1, len(sorted_dates))]
    periodicity = sum(diffs) / len(diffs)
    return len(video_dates), periodicity

# =======================
# GUARDADO DE CSV Y EXCEL
# =======================

def save_general_csv_excel(resumen_canales: List[Dict], month_year: str):
    general_path = CANALES_DIR / f"report_{month_year}.csv"
    df = pd.DataFrame(resumen_canales)
    df.to_csv(general_path, index=False, encoding="utf-8")
    general_path_xlsx = CANALES_DIR / f"report_{month_year}.xlsx"
    df.to_excel(general_path_xlsx, index=False)
    logging.info(f"CSV y Excel general guardados en {CANALES_DIR}")

def save_videos_csv_excel(channel_id: str, videos: List[Dict], month_year: str):
    canal_dir = VIDEOS_DIR / f"canal_{channel_id}"
    canal_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(videos)
    videos_path = canal_dir / f"videos_{month_year}.csv"
    df.to_csv(videos_path, index=False, encoding="utf-8")
    videos_path_xlsx = canal_dir / f"videos_{month_year}.xlsx"
    df.to_excel(videos_path_xlsx, index=False)
    logging.info(f"CSV y Excel de videos guardados en {canal_dir}")

# =======================
# MAIN FLUJO INTEGRADO
# =======================

def main():
    ensure_dirs()
    youtube = get_youtube_service()
    channel_ids = read_channels_csv(CHANNELS_CSV)
    month_year = get_current_month_year()
    logging.info(f"Procesando canales para el periodo: {month_year}")

    resumen_canales = []
    error_log = []
    units_used_total = 0

    for channel_id in channel_ids:
        try:
            logging.info(f"Extrayendo canal: {channel_id}")
            canal_data = get_channel_data(youtube, channel_id)
            if not canal_data:
                continue

            canal_platforms = detect_platforms(canal_data.get("channel_description", ""))
            canal_links = extract_links(canal_data.get("channel_description", ""))

            top_vivos = get_top_live_videos_last_month(youtube, channel_id, MAX_VIDEOS_PER_CHANNEL)
            titles = [v["title"] for v in top_vivos]
            program_freqs = guess_program_title(titles)
            program_prefixes = list(program_freqs.keys())

            video_dates = [v["published_at"] for v in top_vivos]
            vivos_count, vivos_periodicidad = calculate_periodicity(video_dates)

            resumen_canales.append({
                **canal_data,
                "month": month_year,
                "live_videos_count": vivos_count,
                "live_periodicity_days": vivos_periodicidad,
                "first_live_date": min(video_dates) if video_dates else "",
                "last_live_date": max(video_dates) if video_dates else "",
                "channel_platforms": ",".join(canal_platforms),
                "channel_links": ",".join(canal_links),
                "active_programs": ",".join(program_prefixes),
                "extract_datetime": datetime.now().isoformat(),
                "notas": ""
            })

            detailed_videos = []
            for i, v in enumerate(top_vivos):
                video_platforms = detect_platforms(v["description"])
                video_links = extract_links(v["description"])
                programa = assign_program_name(v["title"], program_prefixes)
                # Duración (segundos), si existe info
                ls = v.get("liveStreamingDetails", {})
                start = ls.get("actualStartTime")
                end = ls.get("actualEndTime")
                if start and end:
                    dur_sec = (dtparser.parse(end) - dtparser.parse(start)).total_seconds()
                else:
                    dur_sec = None

                detailed_videos.append({
                    "channel_id": channel_id,
                    "channel_title": canal_data.get("channel_title"),
                    "month": month_year,
                    "video_id": v["video_id"],
                    "video_url": v["video_url"],
                    "title": v["title"],
                    "program_name": programa,
                    "ranking_mes": i + 1,
                    "published_at": v["published_at"],
                    "duration_sec": dur_sec,
                    "view_count": v["view_count"],
                    "like_count": v["like_count"],
                    "comment_count": v["comment_count"],
                    "description": v["description"],
                    "platforms": ",".join(video_platforms),
                    "links": ",".join(video_links),
                    "extract_datetime": datetime.now().isoformat(),
                    "notas": ""
                })
            save_videos_csv_excel(channel_id, detailed_videos, month_year)

        except Exception as e:
            error_log.append(f"{channel_id}: {e}")
            logging.error(f"{channel_id}: {e}")

    save_general_csv_excel(resumen_canales, month_year)

    # Log de errores
    errors_path = DATA_DIR / f"errors_{month_year}.log"
    with open(errors_path, "w", encoding="utf-8") as ferr:
        for error in error_log:
            ferr.write(error + "\n")
    logging.info(f"Extracción finalizada. Log de errores en {errors_path}")

if __name__ == "__main__":
    main()

