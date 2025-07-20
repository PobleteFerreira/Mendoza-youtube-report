# Shorts Stats Script

Este documento explica cómo funciona `extractor/shorts_stats.py`:

## Objetivo

Para cada canal listado en `extractor/channels.csv`, el script:

1. Obtiene todos los vídeos cortos (“Shorts”, < 4 min) publicados en los últimos **30 días**.
2. Recupera sus métricas: título, vistas, me gusta y comentarios.
3. Genera dos CSV en `data/shorts_stats/`:
   - **shorts_summary_YYYY‑MM.csv**  
     | CanalID | Nombre | CantidadShorts | PrimerShort | UltimoShort |
   - **shorts_details_YYYY‑MM.csv**  
     | CanalID | Nombre | VideoID | Titulo | Fecha | Vistas | Likes | Comentarios |

## Requisitos

- Python ≥ 3.10  
- Paquetes:  
  ```bash
  pip install pandas requests python-dotenv isodate
