"""Generar un MP4 y, opcionalmente, programarlo en YouTube."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
from datetime import datetime, timedelta, timezone

BASE = Path(__file__).resolve().parent
TOKEN = BASE / 'token.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
ESCENAS = [
    ('Automatización de videos', 'LOS PANCHOS TITANICOS\nPython + GitHub Actions + YouTube'),
    ('1. Crear el video', 'Python dibuja las diapositivas y FFmpeg las convierte en un archivo MP4.'),
    ('2. Guardar el proyecto', 'GitHub conserva el script y sus dependencias para repetir el proceso.'),
    ('3. Ejecutar automáticamente', 'GitHub Actions instala las dependencias y ejecuta este mismo script.'),
    ('4. Subir a YouTube', 'OAuth autoriza la subida al canal. Las credenciales se guardan como secretos.'),
    ('5. Publicar', 'El video queda programado para las 21:00 de Argentina.'),
]


def autorizar():
    from google_auth_oauthlib.flow import InstalledAppFlow
    archivo = BASE / 'client_secret.json'
    if not archivo.exists():
        raise ValueError('Guardá el OAuth de aplicación de escritorio como client_secret.json junto al script.')
    flow = InstalledAppFlow.from_client_secrets_file(str(archivo), SCOPES)
    credentials = flow.run_local_server(port=0, access_type='offline', prompt='consent')
    if not credentials.refresh_token:
        raise ValueError('Google no devolvió un refresh token; repetí la autorización.')
    TOKEN.write_text(credentials.to_json(), encoding='utf-8')
    TOKEN.chmod(0o600)
    print('Autorización guardada en token.json. No compartas ni subas este archivo.')


def credenciales():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    names = ['YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN']
    values = [os.environ.get(name) for name in names]
    if all(values):
        credentials = Credentials(None, client_id=values[0], client_secret=values[1],
                                  refresh_token=values[2], token_uri='https://oauth2.googleapis.com/token')
    elif any(values):
        raise ValueError('Faltan secretos: ' + ', '.join(n for n, v in zip(names, values) if not v))
    elif TOKEN.exists():
        credentials = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    else:
        raise ValueError('Primero ejecutá --autorizar o configurá los tres secretos de YouTube.')
    credentials.refresh(Request())
    return credentials


def generar(segundos):
    from PIL import Image, ImageDraw, ImageFont
    from imageio_ffmpeg import get_ffmpeg_exe
    salida = BASE / 'salida' / 'video.mp4'
    salida.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        font = ImageFont.load_default(size=34)
        title = ImageFont.load_default(size=48)
        for index, (heading, body) in enumerate(ESCENAS):
            image = Image.new('RGB', (1280, 720), '#101827')
            draw = ImageDraw.Draw(image)
            draw.rectangle((70, 80, 1200, 90), fill='#38bdf8')
            draw.text((80, 160), heading, font=title, fill='white')
            lines = '\n'.join(textwrap.fill(line, 52) for line in body.splitlines())
            draw.multiline_text((80, 290), lines, font=font, fill='#dce8f5', spacing=20)
            draw.text((80, 630), f'{index + 1} / {len(ESCENAS)}', font=font, fill='#38bdf8')
            image.save(tmp / f'{index}.png')
        command = [get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-y',
                   '-framerate', str(len(ESCENAS) / segundos), '-i', str(tmp / '%d.png'),
                   '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', str(segundos),
                   '-r', '24', '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
                   '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', str(salida)]
        subprocess.run(command, check=True)
    print(f'Video generado: {salida}')
    return salida


def subir(archivo, credentials):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    argentina = timezone(timedelta(hours=-3))
    now = datetime.now(argentina)
    fecha = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if fecha <= now + timedelta(minutes=15):
        fecha += timedelta(days=1)
    body = {
        'snippet': {'title': f'Automatización de videos | {fecha:%Y-%m-%d}',
                    'description': 'Demostración de Python, GitHub Actions y YouTube. LOS PANCHOS TITANICOS.',
                    'categoryId': '27'},
        'status': {'privacyStatus': 'private', 'publishAt': fecha.astimezone(timezone.utc).isoformat()}
    }
    with build('youtube', 'v3', credentials=credentials, cache_discovery=False) as youtube:
        request = youtube.videos().insert(part='snippet,status', body=body,
            media_body=MediaFileUpload(str(archivo), mimetype='video/mp4', resumable=True))
        response = None
        while response is None:
            _, response = request.next_chunk(num_retries=3)
    print(f"Subido: https://www.youtube.com/watch?v={response['id']} | Programado: {fecha.isoformat()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--autorizar', action='store_true')
    actions.add_argument('--subir', action='store_true')
    parser.add_argument('--segundos', type=int, default=330, help='Duración; por defecto 330 (5:30).')
    args = parser.parse_args()
    if args.autorizar:
        autorizar()
        return
    if args.segundos < len(ESCENAS):
        parser.error('La duración mínima es de 6 segundos.')
    credentials = credenciales() if args.subir else None
    archivo = generar(args.segundos)
    if args.subir:
        subir(archivo, credentials)


if __name__ == '__main__':
    main()
