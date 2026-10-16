# YouTube automático simple

Proyecto mínimo con temáticas editables e historial persistente.
Genera un video de diapositivas de 5 minutos y 30 segundos, sin narración
(pista de audio silenciosa), y puede subirlo a YouTube. FFmpeg viene en la
dependencia `imageio-ffmpeg` para Windows x64 y Linux x64 habituales.
No necesita n8n ni instalar FFmpeg manualmente.

## Probar en Windows

Desde la carpeta del proyecto, en PowerShell:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" video.py
```

El resultado está en `salida/video.mp4`. Si Python está en PATH, podés usar
`python` en lugar de la ruta completa. Requiere Python 3.10 o superior.
Para una prueba rápida agregá `--segundos 6`.
Editá `tematicas.json` para cambiar las temáticas, títulos y escenas. El script elige una al azar entre las que no figuran en `historial.json`.

## Autorizar YouTube una sola vez

1. En Google Cloud, activá **YouTube Data API v3** y configurá la pantalla de consentimiento OAuth.
2. Creá un cliente OAuth de tipo **Aplicación de escritorio**. Si la app está en pruebas, agregá tu cuenta como usuario de prueba.
3. Descargá su JSON y guardalo junto al script con el nombre `client_secret.json`.
4. Ejecutá y elegí la cuenta/canal correcto en la ventana de Google:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" video.py --autorizar
```

Esto guarda `token.json` localmente. Para generar y subir desde tu PC:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" video.py --subir
```

No subas `token.json` ni `client_secret.json` a GitHub ni los compartas en el chat.
Ambos están excluidos por `.gitignore`. La cuenta debe tener un canal de YouTube.

## Activar la subida diaria

En el repositorio nuevo: **Settings → Secrets and variables → Actions → New repository secret**.
Abrí `token.json` solamente en tu PC y copiá estos valores en tres secretos:

| Secreto de GitHub | Campo de token.json |
| --- | --- |
| `YOUTUBE_CLIENT_ID` | `client_id` |
| `YOUTUBE_CLIENT_SECRET` | `client_secret` |
| `YOUTUBE_REFRESH_TOKEN` | `refresh_token` |

En **Actions → Generar y subir video → Run workflow**, dejá desmarcada
la opción de subir para probar solamente la generación. Descargá el resultado
desde el artefacto `video`. Después ejecutalo marcando la opción de subir.

El horario diario es 20:17 de Argentina. El script solicita a YouTube publicar
a las 21:00; si faltan menos de 15 minutos, programa para el día siguiente.
GitHub puede retrasar los cron y YouTube necesita procesar el video: no es una
garantía de publicación puntual. Antes de esa hora el video queda privado.
Cada ejecución con subida crea un video nuevo, incluso si repetís una ejecución.

Los secretos son propios de cada repositorio: no se copian desde el anterior.
Sin ellos, la ejecución automática falla con un mensaje indicando que falta
la autorización. El workflow manual sin subida funciona sin credenciales.
Desactivá el workflow en Actions cuando no quieras más subidas.

Si Google devuelve `invalid_grant`, repetí `--autorizar` y actualizá el secreto.
Las apps OAuth externas en modo de prueba pueden emitir refresh tokens de corta
vigencia; revisá el estado de publicación de tu app para funcionamiento continuo.
Los límites, permisos y restricciones de YouTube también pueden impedir publicar.
En repositorios públicos inactivos GitHub puede desactivar las tareas programadas.

Documentación: [YouTube uploads](https://developers.google.com/youtube/v3/docs/videos/insert),
[OAuth](https://developers.google.com/identity/protocols/oauth2),
[GitHub schedules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Temáticas sin repetir

Cada entrada de `tematicas.json` tiene `id`, `titulo`, `descripcion` y `escenas` (pares de título y texto). Copiá una entrada para agregar otro tema y usá un id nuevo y único. No cambies ids ya utilizados. Títulos de escenas: hasta 38 caracteres; textos: hasta 230.

El historial se registra después de generar correctamente el MP4, antes de subirlo. Una prueba sin subida también consume el tema. Si falla YouTube, reintentá ese mismo video localmente con `python video.py --subir-existente`; no vuelvas a generar para reintentar. Este comando explícito puede duplicar una subida si el intento anterior sí llegó a YouTube.

Cuando se agotan los temas, el script termina sin generar ni subir nada. Agregá temas nuevos para continuar: nunca reinicia la lista automáticamente.

GitHub Actions guarda el historial con un commit antes de subir; necesita permiso de escritura en Contents y que las reglas de main permitan ese commit. Si no puede guardarlo, no sube el video. No edites el historial durante una ejecución. No ejecutes dos procesos locales simultáneamente. El historial de tu PC es independiente: para compartirlo con Actions, sincronizá el repositorio con git antes y después de usarlo localmente, sin ejecuciones simultáneas en PC y Actions.
