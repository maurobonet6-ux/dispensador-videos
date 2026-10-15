# Índice — dispensador-videos

Vídeos 3D del dispensador automático de jabón en espuma (Blender + Cycles), renderizados gratis en GitHub Actions.

| Necesito… | Archivo |
|---|---|
| Escena 3D (dispensador, espuma, baño, luz, cámara) | `escena.py` |
| Pantalla LED | `pantalla_led.py`, `recursos/led.png` |
| Montaje final (escala, etalonaje, textos, sonido → teaser.mp4) | `montaje.py` |
| Efectos de sonido (ElevenLabs) | `sonidos.py`, `sonidos/*.mp3` |
| HDRI y texturas (Poly Haven, CC0) | `recursos/` |
| Vídeo completo en el baño (8 planos, 570 fotogramas) | `escena_bano.py` |
| Montaje del vídeo completo (mano real, textos, música) | `montaje_bano.py` |
| Recorte de la mano real (una vez, con IA) | `mascaras_mano.py`, `mano/orig`, `mano/recorte` |
| Baño «Modern Bathroom» (dylanheyes, CC BY 4.0) | `recursos/bano/` |
| Lanzar el render | `.github/workflows/render.yml` |

## Render
Push a `main` con «[render]» (máxima calidad) o «[render prueba]» (baja calidad, rápido). El vídeo sale como artefacto `video`. 40 trozos; el final (1080, 128 muestras) tarda ~5 h.

## Relacionados
`rio-videos` usa el mismo método para los vídeos de RÍO.

## Mantenimiento
Si añades un archivo importante, añade una línea aquí. Máximo ~50 líneas.
