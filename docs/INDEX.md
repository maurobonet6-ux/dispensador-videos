# Índice — dispensador-videos

Vídeos 3D del dispensador automático de jabón en espuma (Blender + Cycles), renderizados gratis en GitHub Actions.

| Necesito… | Archivo |
|---|---|
| Escena 3D (dispensador, espuma, baño, luz, cámara) | `escena.py` |
| Pantalla LED | `pantalla_led.py`, `recursos/led.png` |
| Montaje final (escala, etalonaje, textos, sonido → `teaser.mp4`) | `montaje.py` |
| Efectos de sonido (ElevenLabs) | `sonidos.py`, `sonidos/*.mp3` |
| HDRI y texturas (Poly Haven, CC0) | `recursos/` |
| Lanzar el render | `.github/workflows/render.yml` |

## Render
Push a `main` con «[render]» (máxima calidad) o «[render prueba]» (baja calidad, rápido). El vídeo sale como artefacto `teaser`.

## Relacionados
`rio-videos` usa el mismo método para los vídeos de RÍO.

## Mantenimiento
Si añades un archivo importante, añade una línea aquí. Máximo ~50 líneas.
