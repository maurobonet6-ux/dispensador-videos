# Plano «mano real»: recorta la mano y el chorro de espuma del vídeo del fabricante (720x960) y los pone sobre el fondo 3D
# (plano_mano.py). Sombra de la mano en la pared, color igualado con la pared 3D, grano. Uso: python3.11 composicion.py FONDO.png SALIDA_DIR
import os, sys, glob
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session

AQUI = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(AQUI, 'mano', 'orig')
FONDO, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
W, H, ESC, BAJA = 1080, 1920, 1.5, 200
Y0, Y1 = 540, 872                       # franja del vídeo con la mano (por encima de los subtítulos grabados)
BOQ_X, BOQ_Y = 352, 527                 # boquilla real en el vídeo
ses = new_session('isnet-general-use')
fondo = np.asarray(Image.open(FONDO).convert('RGB').resize((W, H), Image.LANCZOS)).astype(np.float32)
rng = np.random.default_rng(1)

def a_final(arr):                       # imagen o máscara del vídeo (720x960) → posición en el plano final
    im = Image.fromarray(arr).resize((int(720 * ESC), int(960 * ESC)), Image.LANCZOS)
    lienzo = Image.new(im.mode, (W, H)); lienzo.paste(im, (0, BAJA)); return np.asarray(lienzo).astype(np.float32)

for i, ruta in enumerate(sorted(glob.glob(os.path.join(ORIG, 'm*.png'))), 1):
    im = Image.open(ruta).convert('RGB'); a = np.asarray(im).astype(np.float32)
    # mano: recorte con IA solo en la franja de abajo (si no, elige el dispensador)
    m = np.zeros((960, 720), np.float32)
    m[Y0:Y1] = np.asarray(remove(im.crop((0, Y0, 720, Y1)), session=ses, only_mask=True)).astype(np.float32) / 255
    m = np.clip((m - 0.15) / 0.7, 0, 1)
    # chorro de espuma: lo que es más claro que la pared, en una columna estrecha bajo la boquilla
    lum = a.mean(2); pared = np.median(lum[560:640, 560:700])
    filas_mano = np.where(m[:, BOQ_X - 18:BOQ_X + 18].max(1) > 0.5)[0]
    tope = int(filas_mano.min()) + 12 if len(filas_mano) else Y1            # el chorro acaba donde empieza la mano
    chorro = np.zeros_like(m); xs = slice(BOQ_X - 14, BOQ_X + 14); ys = slice(BOQ_Y + 4, tope)
    chorro[ys, xs] = np.clip((lum[ys, xs] - pared - 18) / 20, 0, 1)
    alfa = np.maximum(m, chorro); alfa[Y1 - 6:] = 0
    alfa = np.asarray(Image.fromarray((alfa * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255
    # color: la luz del vídeo se lleva a la de la pared 3D (ganancia por canal medida en la pared junto a la mano)
    ref = a[560:640, 560:700].reshape(-1, 3).mean(0)
    yF, xF = int(600 * ESC + BAJA), int(630 * ESC)
    obj = fondo[yF - 50:yF + 50, xF - 90:xF + 90].reshape(-1, 3).mean(0)
    a = np.clip(a * (obj / ref), 0, 255)
    A = a_final((alfa * 255).astype(np.uint8))[..., None] / 255; C = a_final(a.astype(np.uint8))
    # sombra suave de la mano en la pared (luz arriba a la izquierda → cae abajo a la derecha)
    s = Image.fromarray((A[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28))
    S = np.zeros((H, W), np.float32); S[40:, 30:] = np.asarray(s).astype(np.float32)[:-40, :-30] / 255
    base = fondo * (1 - 0.32 * S[..., None])
    out = base * (1 - A) + C * A
    out += rng.normal(0, 2.2, out.shape[:2])[..., None]                       # mismo grano en todo
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f'f{i:04d}.png'))
print('composición ok', i)
