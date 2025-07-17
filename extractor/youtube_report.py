import os
import csv
import re
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from googleapiclient.discovery import build
from dotenv import load_dotenv
from dateutil import parser as dtparser

# ==== Configuración de carpetas ====
def ensure_dirs():
    (Path("data") / "canales").mkdir(parents=True, exist_ok=True)
    (Path("data") / "videos").mkdir(parents=True, exist_ok=True)

# ==== Detección de plataformas ====
PLATAFORMAS_PATTERNS = {
    "Cafecito": r"cafecito\\.app",
    "MercadoPago": r"mercadopago\\.com|mpago\\.la",
    "PayPal": r"paypal\\.me|paypal\\.com",
    "Patreon": r"patreon\\.com",
    "Twitch": r"twitch\\.tv",
    "Instagram": r"instagram\\.com|instagr\\.am",
    "TikTok": r"tiktok\\.com",
    "Discord": r"discord\\.gg|discord\\.com",
    "Telegram": r"t\\.me|telegram\\.me|telegram\\.org",
    "Facebook": r"facebook\\.com|fb\\.me",
    "WebPropia": r"\\.com\\.ar|\\.com|\\.net|\\.org",
    "OnlyFans": r"onlyfans\\.com",
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
        return None, None, None
    fechas = sorted([dtparser.parse(f) for f in fecha_list])
    dias = [(fechas[i] - fechas[i-1]).days for i in range(1, len(fechas))]
    promedio_dias = sum(dias) / len(dias) if dias else None
    frecuencia_mensual = len(fechas)
    frecuencia_semanal = frecuencia_mensual / 4
    frecuencia_diaria = frecuencia_mensual / 31
    return round(promedio_dias, 2), round(frecuencia_semanal, 2), round(frecuencia_diaria, 2)

# ==== MAIN ====
def main():
    ensure_dirs()
    load_dotenv()
    API_KEY = os.getenv('YOUTUBE_API_KEY')
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    month_year = get_month_year()

    # Leer canales
    with open('extractor/channels.csv', newline='', encoding='utf-8') as csvfile:
        canales = list(csv.DictReader(csvfile))

    resumen_canales = []

    for canal in canales:
        channel_id = canal['channel_id']
        channel_url = canal.get('channel_url', f'https://www.youtube.com/channel/{channel_id}')

        # Datos generales canal
        channel_resp = youtube.channels().list(part='snippet,statistics', id=channel_id).execute()
        if not channel_resp['items']:
            continue
        info = channel_resp['items'][0]
        snippet, stats = info['snippet'], info['statistics']
        desc = snippet.get('description', '')
        plataformas_canal = detect_platforms(desc)
        links_canal = extract_links(desc)
        monet_canal = ', '.join(plataformas_canal) if plataformas_canal else 'No'

        nombre = snippet.get('title', '')
        pais = snippet.get('country', 'Argentina')
        fecha_creacion = snippet.get('publishedAt', '')
        subs = stats.get('subscriberCount', '0')
        vistas = stats.get('viewCount', '0')
        video_count = stats.get('videoCount', '0')

        # Buscar todos los vivos del mes (paginando)
        fecha_hace_un_mes = (datetime.utcnow() - timedelta(days=31)).isoformat("T") + "Z"
        vivos = []
        next_token = None
        while True:
            resp = youtube.search().list(
                part='id,snippet', channelId=channel_id,
                type='video', eventType='completed', publishedAfter=fecha_hace_un_mes,
                maxResults=50, pageToken=next_token
            ).execute()
            for item in resp.get('items', []):
                vivos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt']
                })
            next_token = resp.get('nextPageToken')
            if not next_token:
                break

        # Obtener detalles de cada video
        vivos_detalles, fechas_vivos = [], []
        for v in vivos:
            v_resp = youtube.videos().list(
                part='snippet,statistics,liveStreamingDetails', id=v['video_id']
            ).execute()
            if not v_resp['items']:
                continue
            d = v_resp['items'][0]
            snip, stats = d['snippet'], d['statistics']
            live_det = d.get('liveStreamingDetails', {})
            desc_video = snip.get('description', '')
            plataformas_video = detect_platforms(desc_video)
            links_video = extract_links(desc_video)
            fecha_video = snip.get('publishedAt', '')
            fechas_vivos.append(fecha_video)
            start = live_det.get('actualStartTime')
            end = live_det.get('actualEndTime')
            dur = (dtparser.parse(end) - dtparser.parse(start)).total_seconds() if start and end else None
            vivos_detalles.append({
                'channel_id': channel_id,
                'channel_title': nombre,
                'month': month_year,
                'video_id': v['video_id'],
                'video_url': f"https://www.youtube.com/watch?v={v['video_id']}",
                'title': snip.get('title', ''),
                'published_at': fecha_video,
                'duration_sec': dur,
                'view_count': stats.get('viewCount', '0'),
                'like_count': stats.get('likeCount', '0'),
                'comment_count': stats.get('commentCount', '0'),
                'description': desc_video,
                'monetizacion': ', '.join(plataformas_video) if plataformas_video else 'No',
                'platforms': ', '.join(plataformas_video),
                'links': ', '.join(links_video),
                'notas': ''
            })

        # Periodicidad y frecuencia
        promedio_dias, frecuencia_sem, frecuencia_dia = calculate_periodicity(fechas_vivos)
        cantidad_vivos = len(vivos_detalles)
        primer_vivo = min(fechas_vivos) if fechas_vivos else ""
        ultimo_vivo = max(fechas_vivos) if fechas_vivos else ""

        # Top 10 más vistos
        df_videos = pd.DataFrame(vivos_detalles)
        df_top10 = df_videos.sort_values(by='view_count', ascending=False).head(10)

        # Guardar archivos
        canal_videos_dir = Path("data/videos") / f"canal_{channel_id}"
        canal_videos_dir.mkdir(parents=True, exist_ok=True)
        df_videos.to_csv(canal_videos_dir / f"videos_{month_year}.csv", index=False)
        df_top10.to_csv(canal_videos_dir / f"top10_videos_{month_year}.csv", index=False)
        df_videos.to_excel(canal_videos_dir / f"videos_{month_year}.xlsx", index=False)
        df_top10.to_excel(canal_videos_dir / f"top10_videos_{month_year}.xlsx", index=False)

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
            'PromedioDiasEntreVivos': promedio_dias or '',
            'FrecuenciaSemanal': frecuencia_sem or '',
            'FrecuenciaDiaria': frecuencia_dia or '',
            'FechaPrimerVivoMes': primer_vivo,
            'FechaUltimoVivoMes': ultimo_vivo,
            'MonetizacionAlternativa_desc': monet_canal,
            'Links_desc': ', '.join(links_canal),
            'Plataformas_desc': ', '.join(plataformas_canal),
            'notas': ''
        })

    # Guardar archivo resumen de canales
    out_general = Path("data/canales") / f"report_{month_year}.csv"
    df_general = pd.DataFrame(resumen_canales)
    df_general.to_csv(out_general, index=False)
    df_general.to_excel(Path("data/canales") / f"report_{month_year}.xlsx", index=False)
    print(f"✅ Reporte generado: {out_general}")

if __name__ == "__main__":
    main()
