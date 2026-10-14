# dispensador-videos

Vídeos 3D del dispensador automático de jabón en espuma (Blender + Cycles), renderizados gratis en GitHub Actions.

- `escena.py`: escena 3D (dispensador, espuma con burbujas, baño, luz de estudio, cámara). `pantalla_led.py`: pantalla LED.
- `montaje.py`: escala, brillo del LED, etalonaje, textos y sonido → `teaser.mp4`. `sonidos.py`: efectos (ElevenLabs).
- `recursos/`: HDRI, texturas y suculenta de Poly Haven (CC0).
- Render: push a `main` con «[render]» (máxima calidad) o «[render prueba]» (baja calidad, rápido). El vídeo sale como artefacto `teaser`.

## Arranque en el baño (`escena_bano.py` + `montaje_bano.py`)
Escena «Modern Bathroom» de dylanheyes (Sketchfab), licencia CC BY 4.0 — hay que citarlo en la descripción del anuncio:
«Escena 3D: "Modern Bathroom" de dylanheyes (Sketchfab), CC BY 4.0». Se reilumina con luz real (sol por la ventana, cielo HDRI).
