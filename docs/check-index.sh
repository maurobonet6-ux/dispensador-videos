#!/usr/bin/env bash
# Avisa solo si docs/INDEX.md apunta a rutas que ya no existen. Si todo está bien, no imprime nada (0 tokens).
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" || exit 0
[ -f docs/INDEX.md ] || exit 0
missing=""
while IFS= read -r p; do
  case "$p" in *" "*|"") continue;; esac
  case "$p" in */*|*.*) ;; *) continue;; esac
  compgen -G "$p" >/dev/null || [ -e "$p" ] || missing="$missing $p"
done < <(grep '^|' docs/INDEX.md | grep -o '`[^`]*`' | tr -d '`')
[ -n "$missing" ] && echo "INDEX desactualizado: estas rutas de docs/INDEX.md ya no existen:$missing. Corrígelo antes de la tarea."
exit 0
