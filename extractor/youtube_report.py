import os
import csv
import re
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from googleapiclient.discovery import build
from dotenv import load_dotenv

# ==== Configuración ====
def ensure_dirs():
    (Path("data") / "canales").mkdir(parents=True, exist_ok=True)
    (Path("data") / "videos").mkdir(parents=True, exist_ok=True)

# Palabras y patrones para detectar plataformas/redes/monetización
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

def detect_platforms(text: str):
    detected = []
    if not text:
        return detected
    for plat, pattern in PLATAFORMAS_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            detected.append(plat)
    return detected

def extract_links(text: str):
    if not text:
        return []
    return re.findall(r'https?://[^\s)]+', text)

def get_month_year():
    now = datetime.now()
    return f"{now.month:02d}-{now.year}"

def calculate_periodicity(fecha_list):
    if len(fecha_list) < 2:
        return None
    fechas = sorted([datetime.strptime(f, '%Y-%m-%dT%H:%M:%SZ') for f in fecha_list])
    dias = [(fechas[i] - fechas[i-1]).days for i in range(1, len(fechas))]
    return sum(dias) / len(dias) if dias else None

# ==== MAIN ====

def main():
    ensure_dirs()
    load_dotenv()
    API_KEY = os.getenv('YOUTUBE_API_KEY')
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # Leer canales desde CSV
    canales = []
    with open('extractor/channels.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            canales.append(row)

    # Variables generales
    month_year = get_month_year()
    resumen_canales = []
    
    for canal in canales:
        channel_id = canal['channel_id']
        channel_url = canal.get('channel_url', f'https://www.youtube.com/channel/{channel_id}')
        # 1. Datos generales canal
        channel_resp = youtube.channels().list(part='snippet,statistics', id=channel_id).execute()
        if not channel_resp['items']:
            continue
        info = channel_resp['items'][0]
        snippet = info['snippet']
        stats = info['statistics']
        desc = snippet.get('description', '')
        plataformas_canal = detect_platforms(desc)
        links_canal = extract_links(desc)
        monet_canal = ', '.join(plataformas_canal) if plataformas_canal else 'No'
        fecha_creacion = snippet.get('publishedAt', '')
        subs = stats.get('subscriberCount', '0')
        vistas = stats.get('viewCount', '0')
        video_count = stats.get('videoCount', '0')
        nombre = snippet.get('title', '')
        pais = snippet.get('country', 'Argentina')
        
        # 2. Buscar vivos del último mes (solo transmisiones en vivo)
        fecha_hace_un_mes = (datetime.utcnow() - timedelta(days=31)).isoformat("T") + "Z"
        search_resp = youtube.search().list(
            part='id,snippet',
            channelId=channel_id,
            type='video',
            eventType='completed',
            publishedAfter=fecha_hace_un_mes,
            maxResults=50
        ).execute()
        vivos = []
        for item in search_resp.get('items', []):
            video_id = item['id']['videoId']
            titulo = item['snippet']['title']
            fecha_pub = item['snippet']['publishedAt']
            vivos.append({
                'video_id': video_id,
                'title': titulo,
                'published_at': fecha_pub
            })
        # Traer detalles y stats para cada video vivo
        vivos_detalles = []
        fechas_vivos = []
        for idx, v in enumerate(sorted(vivos, key=lambda x: x['published_at'], reverse=True)[:10]):
            video_id = v['video_id']
            v_resp = youtube.videos().list(
                part='snippet,statistics,liveStreamingDetails',
                id=video_id
            ).execute()
            if not v_resp['items']:
                continue
            d = v_resp['items'][0]
            snip = d['snippet']
            stats = d['statistics']
            live_det = d.get('liveStreamingDetails', {})
            desc_video = snip.get('description', '')
            plataformas_video = detect_platforms(desc_video)
            links_video = extract_links(desc_video)
            monet_video = ', '.join(plataformas_video) if plataformas_video else 'No'
            fecha_video = snip.get('publishedAt', '')
            fechas_vivos.append(fecha_video)
            start = live_det.get('actualStartTime')
            end = live_det.get('actualEndTime')
            if start and end:
                from dateutil import parser as dtparser
                dur = (dtparser.parse(end) - dtparser.parse(start)).total_seconds()
            else:
                dur = None
            vivos_detalles.append({
                'channel_id': channel_id,
                'channel_title': nombre,
                'month': month_year,
                'video_id': video_id,
                'video_url': f'https://www.youtube.com/watch?v={video_id}',
                'title': snip.get('title', ''),
                'published_at': fecha_video,
                'duration_sec': dur,
                'view_count': stats.get('viewCount', '0'),
                'like_count': stats.get('likeCount', '0'),
                'comment_count': stats.get('commentCount', '0'),
                'description': desc_video,
                'monetizacion': monet_video,
                'platforms': ', '.join(plataformas_video),
                'links': ', '.join(links_video),
                'ranking_mes': idx + 1,
                'notas': ''
            })

        # --- SIGUE EN PARTE 2 ---
        # 3. Calcular periodicidad/frecuencia de vivos
        periodicidad = calculate_periodicity(fechas_vivos)
        cantidad_vivos = len(vivos_detalles)
        primer_vivo = min(fechas_vivos) if fechas_vivos else ""
        ultimo_vivo = max(fechas_vivos) if fechas_vivos else ""
        
        # 4. Guardar archivo de videos (por canal)
        canal_videos_dir = Path("data/videos") / f"canal_{channel_id}"
        canal_videos_dir.mkdir(parents=True, exist_ok=True)
        out_videos = canal_videos_dir / f"videos_{month_year}.csv"
        df_videos = pd.DataFrame(vivos_detalles)
        df_videos.to_csv(out_videos, index=False, encoding='utf-8')
        # Si querés también Excel:
        out_videos_xlsx = canal_videos_dir / f"videos_{month_year}.xlsx"
        df_videos.to_excel(out_videos_xlsx, index=False)

        # 5. Resumen para archivo general de canales
        resumen_canales.append({
            'CanalID': channel_id,
            'Nombre': nombre,
            'URL': channel_url,
            'Descripcion': desc,
            'Pais': pais,
            'FechaCreacion': fecha_creacion,
            'Suscriptores': subs,
            'VistasTotales': vistas,
            'CantidadVideos': video_count,
            'CantidadVivosMes': cantidad_vivos,
            'PeriodicidadVivos_dias': periodicidad if periodicidad is not None else "",
            'FechaPrimerVivoMes': primer_vivo,
            'FechaUltimoVivoMes': ultimo_vivo,
            'MonetizacionAlternativa_desc': monet_canal,
            'Links_desc': ', '.join(links_canal),
            'Plataformas_desc': ', '.join(plataformas_canal),
            'notas': ''
        })

    # 6. Guardar archivo general de canales
    out_general = Path("data/canales") / f"report_{month_year}.csv"
    df_general = pd.DataFrame(resumen_canales)
    df_general.to_csv(out_general, index=False, encoding='utf-8')
    # Si querés también Excel:
    out_general_xlsx = Path("data/canales") / f"report_{month_year}.xlsx"
    df_general.to_excel(out_general_xlsx, index=False)

    print(f"Reportes guardados: {out_general}, archivos de videos en carpeta data/videos/")

if __name__ == "__main__":
    main()

