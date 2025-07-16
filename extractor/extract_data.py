import os
import csv
import json
import time
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build

# Config
API_KEY = os.getenv("YOUTUBE_API_KEY")  # definida como secret en GitHub Actions o `.env`
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Directorios
CHANNELS_CSV = "extractor/channels.csv"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Fecha actual para nombrar el archivo
today = datetime.today().strftime("%Y%m%d")
output_path = os.path.join(DATA_DIR, f"live_{today}.csv")

# Inicializar API
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def get_live_stream_data(channel_id):
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        eventType="live",
        type="video",
        maxResults=1
    )
    response = request.execute()
    items = response.get("items", [])
    
    if not items:
        return None  # No está en vivo

    video = items[0]
    video_id = video["id"]["videoId"]

    # Obtener estadísticas del video en vivo
    stats_req = youtube.videos().list(part="snippet,liveStreamingDetails", id=video_id)
    stats_res = stats_req.execute()

    details = stats_res["items"][0]
    snippet = details["snippet"]
    live = details.get("liveStreamingDetails", {})

    return {
        "channel_id": channel_id,
        "video_id": video_id,
        "title": snippet.get("title"),
        "published_at": snippet.get("publishedAt"),
        "live_start_time": live.get("actualStartTime"),
        "concurrent_viewers": live.get("concurrentViewers"),
    }

# Leer canales
channels_df = pd.read_csv(CHANNELS_CSV)
data = []

for _, row in channels_df.iterrows():
    channel_id = row["CanalID"]
    result = get_live_stream_data(channel_id)
    if result:
        print(f"🔴 EN VIVO: {row['Nombre']} — {result['concurrent_viewers']} viewers")
        result["channel_name"] = row["Nombre"]
        result["fecha_reporte"] = today
        data.append(result)
    else:
        print(f"⚫ No en vivo: {row['Nombre']}")

# Guardar CSV
if data:
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"✅ Datos guardados en: {output_path}")
else:
    print("❌ Ningún canal en vivo hoy.")
