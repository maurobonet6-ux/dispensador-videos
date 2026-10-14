# Recorta (una sola vez, con IA) la mano y el chorro de espuma de los 48 fotogramas del vídeo del fabricante (mano/orig/m*.png)
# y guarda mano/recorte/m*.png en RGBA (720x960). El montaje solo los pega encima: la nube no necesita la IA.
# Uso: /home/user/venv_rembg/bin/python mascaras_mano.py
import os, glob
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session

AQUI = os.path.dirname(os.path.abspath(__file__)); ORIG = os.path.join(AQUI, 'mano', 'orig'); OUT = os.path.join(AQUI, 'mano', 'recorte')
os.makedirs(OUT, exist_ok=True)
Y0, Y1 = 540, 872                       # franja de la mano (por encima de los subtítulos grabados)
BOQ_X, BOQ_Y = 352, 527                 # boquilla real
ses = new_session('isnet-general-use')
for ruta in sorted(glob.glob(os.path.join(ORIG, 'm*.png'))):
    im = Image.open(ruta).convert('RGB'); a = np.asarray(im).astype(np.float32)
    m = np.zeros((960, 720), np.float32)
    m[Y0:Y1] = np.asarray(remove(im.crop((0, Y0, 720, Y1)), session=ses, only_mask=True)).astype(np.float32) / 255
    m = np.clip((m - 0.15) / 0.7, 0, 1)
    lum = a.mean(2); pared = np.median(lum[560:640, 560:700])
    filas = np.where(m[:, BOQ_X - 18:BOQ_X + 18].max(1) > 0.5)[0]
    tope = int(filas.min()) + 12 if len(filas) else Y1
    chorro = np.zeros_like(m); xs = slice(BOQ_X - 14, BOQ_X + 14); ys = slice(BOQ_Y + 4, tope)
    chorro[ys, xs] = np.clip((lum[ys, xs] - pared - 18) / 20, 0, 1)
    alfa = np.maximum(m, chorro); alfa[Y1 - 6:] = 0
    alfa = np.asarray(Image.fromarray((alfa * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)))
    rgba = np.dstack([np.asarray(im), alfa]); Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, os.path.basename(ruta)))
print('recortes ok', len(os.listdir(OUT)))
