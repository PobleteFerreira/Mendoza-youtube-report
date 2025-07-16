#!/usr/bin/env python3
"""
Script actualizado para monitorear transmisiones en vivo de canales de YouTube.
Registra vistas en vivo cada 30 minutos entre las 19:00 y las 22:00.
Guarda los datos en `data/live_tracking/live_data_YYYYMMDD.csv` sin sobrescribir, para análisis longitudinal.
"""

import os
import csv
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import time

# Cargar claves desde config.json
with open('config.json', 'r') as f:
    config = json.load(f)

API_KEY = config['YOUTUBE_API_KEY']
YOUTUBE = build('youtube', 'v3', developerKey=API_KEY)
CHANNELS_CSV = 'extractor/channels.csv'
OUTPUT_DIR = 'data/live_tracking'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Obtener canales a monitorear
def cargar_canales():
    canales = []
    with open(CHANNELS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            canales.append({"id": row['CanalID'], "nombre": row['Nombre']})
    return canales

# Verificar si canal está en vivo y obtener vistas en tiempo real
def verificar_en_vivo(canal_id):
    try:
        response = YOUTUBE.search().list(
            part='snippet', channelId=canal_id, type='video', eventType='live', maxResults=1
        ).execute()
        items = response.get('items', [])
        if not items:
            return None  # No hay live

        video_id = items[0]['id']['videoId']
        title = items[0]['snippet']['title']

        stats = YOUTUBE.videos().list(part='liveStreamingDetails', id=video_id).execute()
        viewers = stats['items'][0]['liveStreamingDetails'].get('concurrentViewers', '0')
        return video_id, title, int(viewers)

    except HttpError as e:
        print(f"⚠️ Error con el canal {canal_id}: {e}")
        return None

# Guardar resultados en archivo CSV

def guardar_resultado(fecha_hora, canal, estado, vistas, titulo):
    fecha_str = fecha_hora.strftime('%Y%m%d')
    archivo_csv = os.path.join(OUTPUT_DIR, f'live_data_{fecha_str}.csv')
    existe = os.path.isfile(archivo_csv)

    with open(archivo_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(['Timestamp', 'Canal', 'Estado', 'VistasEnVivo', 'Titulo'])
        writer.writerow([fecha_hora.isoformat(), canal, estado, vistas, titulo])

# Ejecución principal

def monitorear():
    ahora = datetime.now()
    canales = cargar_canales()
    print(f"\n⏱️ {ahora.strftime('%Y-%m-%d %H:%M:%S')} — Verificando canales...")

    for canal in canales:
        resultado = verificar_en_vivo(canal['id'])
        if resultado:
            video_id, titulo, vistas = resultado
            estado = 'En vivo'
        else:
            titulo = ''
            vistas = 0
            estado = 'Offline'

        guardar_resultado(ahora, canal['nombre'], estado, vistas, titulo)
        print(f"  - {canal['nombre']}: {estado} — {vistas} vistas")

if __name__ == '__main__':
    monitorear()

