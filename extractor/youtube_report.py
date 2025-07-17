import os
import csv
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv
from pathlib import Path

def ensure_dirs():
    """
    Crea las carpetas data/, data/canales/ y data/videos/ si no existen.
    """
    (Path("data") / "canales").mkdir(parents=True, exist_ok=True)
    (Path("data") / "videos").mkdir(parents=True, exist_ok=True)


# Cargar la API Key desde .env
load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')

# Palabras clave para monetización alternativa
MONETIZATION_KEYWORDS = ['patreon', 'cafecito', 'paypal', 'donación', 'donate', 'mercadopago', 'contribuir', 'apóyanos', 'support']

def detect_monetization(text):
    text = text.lower() if text else ""
    return any(keyword in text for keyword in MONETIZATION_KEYWORDS)

def main():
    ensure_dirs()
    # ... el resto de tu código principal ...

    # Inicializar YouTube API
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    # Leer canales
    channels = []
    with open('extractor/channels.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            channels.append(row)
    
    report_data = []
    for ch in channels:
        channel_id = ch['channel_id']
        channel_url = ch['channel_url']
        
        # Obtener datos generales del canal
        channel_response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()
        if not channel_response['items']:
            continue  # Canal no encontrado
        
        channel_info = channel_response['items'][0]
        snippet = channel_info['snippet']
        stats = channel_info['statistics']
        
        name = snippet.get('title')
        description = snippet.get('description')
        country = snippet.get('country', '')
        published_at = snippet.get('publishedAt', '')
        subscribers = stats.get('subscriberCount', '0')
        views = stats.get('viewCount', '0')
        video_count = stats.get('videoCount', '0')
        monetization_in_desc = detect_monetization(description)
        
        # Obtener los últimos 5 videos
        uploads_playlist_id = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        playlist_items = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=5
        ).execute()['items']
        
        last_video_date = ""
        videos_data = []
        for idx, item in enumerate(playlist_items):
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            video_published = item['snippet']['publishedAt']
            if idx == 0:
                last_video_date = video_published
            video_monetization = detect_monetization(video_title)
            
            # Obtener estadísticas del video
            video_response = youtube.videos().list(
                part='statistics',
                id=video_id
            ).execute()
            if video_response['items']:
                video_stats = video_response['items'][0]['statistics']
                views_video = video_stats.get('viewCount', '0')
                likes_video = video_stats.get('likeCount', '0')
                comments_video = video_stats.get('commentCount', '0')
            else:
                views_video = likes_video = comments_video = '0'
            
            videos_data.extend([
                video_title,
                video_published,
                views_video,
                likes_video,
                comments_video,
                'Sí' if video_monetization else 'No'
            ])
        
        # Estado de actividad
        last_video_dt = datetime.strptime(last_video_date, '%Y-%m-%dT%H:%M:%SZ') if last_video_date else None
        months_since_last = (datetime.utcnow() - last_video_dt).days // 30 if last_video_dt else None
        activo = 'Activo' if last_video_dt and months_since_last < 6 else 'Inactivo'
        
        # Compilar fila
        row = [
            channel_id, name, channel_url, description, country, published_at,
            subscribers, views, video_count, last_video_date, activo,
            'Sí' if monetization_in_desc else 'No'
        ]
        # Añadir datos de los 5 videos
        row.extend(videos_data)
        report_data.append(row)
    
    # Definir columnas
    cols = [
        'CanalID', 'Nombre', 'URL', 'Descripcion', 'Pais', 'FechaCreacion',
        'Suscriptores', 'VistasTotales', 'CantidadVideos', 'FechaUltimoVideo', 'Estado',
        'MonetizacionAlternativa_desc'
    ]
    for i in range(1, 6):
        cols.extend([
            f'Video{i}_Titulo', f'Video{i}_Fecha', f'Video{i}_Vistas', f'Video{i}_Likes', f'Video{i}_Comentarios', f'Video{i}_Monetizacion'
        ])
    
    # Guardar CSV
    df = pd.DataFrame(report_data, columns=cols)
    out_path = f'data/report_{datetime.utcnow().strftime("%Y%m")}.csv'
    df.to_csv(out_path, index=False, encoding='utf-8')
    print(f'Reporte guardado en {out_path}')

if __name__ == "__main__":
    main()
