# Mapa del proyecto

Se carga solo en cada sesión. Antes de buscar en el repo, usa esta tabla para ir directo al archivo.

@docs/INDEX.md

## Mantenimiento automático (sin que te lo pidan)

- Si creas, mueves, renombras o borras un archivo importante, actualiza `docs/INDEX.md` en el mismo commit. No preguntes.
- Antes de cada commit ejecuta `bash docs/check-index.sh`: no imprime nada si el índice está bien; si avisa, corrígelo.
- Ahorra tokens sin perder calidad: localiza con Grep/Glob antes de leer, lee solo el rango necesario, no releas lo ya leído, limita las salidas (`| head`, `--quiet`) y no explores partes ajenas a la tarea.
