# Montaje del vídeo completo (19 s): mano real en el plano 2, aspecto de vídeo de móvil, brillo del LED, etalonaje, textos por plano,
# indicador de 3 niveles, música y efectos. Uso: python3 montaje_bano.py DIR_RENDER SALIDA.mp4
import os, sys, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DIR, SALIDA = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(AQUI, 'post'); os.makedirs(TMP, exist_ok=True)
W, H, FPS = 1080, 1920, 30
PLANOS = [('entrada', 1, 105), ('mano', 106, 153), ('pantalla', 154, 225), ('botones', 226, 285), ('apagado', 286, 345),
          ('adhesivo', 346, 405), ('usb', 406, 450), ('versiones', 451, 570)]
P = {n: (a, b) for n, a, b in PLANOS}; N = PLANOS[-1][2]
LED_ON = 64
F = '/usr/share/fonts/opentype/inter/InterDisplay-'
BLANCO = (250, 248, 246); ORO = (246, 186, 152)

def suave(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def plano(f): return next(n for n, a, b in PLANOS if a <= f <= b)

def letras(d, x, y, t, fnt, fill, trk):
    for ch in t: d.text((x, y), ch, font=fnt, fill=fill); x += d.textlength(ch, font=fnt) + trk
def ancho(d, t, fnt, trk): return sum(d.textlength(ch, font=fnt) for ch in t) + trk * (len(t) - 1)

def texto(im, partes, cy, tam, k, fuente='Black', trk=0.0, sube=0.012):
    """Una línea centrada hecha de (texto, color); entra con desenfoque y subiendo un poco (k: 0 → 1)."""
    if k <= 0: return im
    fnt = ImageFont.truetype(F + fuente + '.otf', tam); d0 = ImageDraw.Draw(im); tr = tam * trk
    total = sum(ancho(d0, t, fnt, tr) for t, _ in partes)
    x = (W - total) / 2; y = H * cy - tam * 0.6 + (1 - k) * H * sube
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
    for t, col in partes:
        letras(dc, x, y, t, fnt, col + (int(255 * k),), tr); x += ancho(dc, t, fnt, tr)
    if k < 1: capa = capa.filter(ImageFilter.GaussianBlur(12 * (1 - k)))
    sombra = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sombra.putalpha(capa.split()[3].filter(ImageFilter.GaussianBlur(16)).point(lambda p: int(p * 0.6)))
    im = Image.alpha_composite(im.convert('RGBA'), sombra); return Image.alpha_composite(im, capa)

def pastilla(im, t, cy, tam, k, fondo=(246, 186, 152), color=(30, 22, 20)):
    if k <= 0: return im
    fnt = ImageFont.truetype(F + 'Bold.otf', tam); d = ImageDraw.Draw(im); bb = d.textbbox((0, 0), t, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; px, py = tam * 0.9, tam * 0.5
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
    x0 = (W - tw) / 2 - px; y0 = H * cy - th / 2 - py + (1 - k) * 30
    dc.rounded_rectangle((x0, y0, x0 + tw + 2 * px, y0 + th + 2 * py), radius=(th + 2 * py) / 2, fill=fondo + (int(255 * k),))
    dc.text((x0 + px - bb[0], y0 + py - bb[1]), t, font=fnt, fill=color + (int(255 * k),))
    return Image.alpha_composite(im.convert('RGBA'), capa)

def niveles(im, f, k):
    """Tres pastillas de nivel que se encienden con cada pulsación del botón."""
    if k <= 0: return im
    b0 = P['botones'][0]; n = sum(f >= b0 + t for t in (13, 29, 45))
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa); w, h, sep = 120, 22, 26
    x0 = (W - (3 * w + 2 * sep)) / 2; y0 = H * 0.215
    for i in range(3):
        col = ORO if i < n else (255, 255, 255)
        dc.rounded_rectangle((x0 + i * (w + sep), y0, x0 + i * (w + sep) + w, y0 + h), radius=h / 2, fill=col + (int((255 if i < n else 90) * k),))
    return Image.alpha_composite(im.convert('RGBA'), capa)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIN = (1 - 0.38 * np.clip(((xx - W / 2) / (W / 2)) ** 2 * 0.55 + ((yy - H / 2) / (H / 2)) ** 2 * 0.45, 0, 1))[..., None]
R2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
rng = np.random.default_rng(3)

def acabado(a):
    """Brillo del LED azul, etalonaje cálido suave, viñeta y grano fino (sobre un array float 0..1)."""
    lum = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    brillo = np.clip(a[..., 2:3] - a[..., 0:1] - 0.25, 0, 1) * np.array([0.35, 0.6, 1.0], np.float32) * 2
    b = np.asarray(Image.fromarray((np.clip(brillo, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(22))).astype(np.float32) / 255
    a = a + b * 0.45
    a = a + (1 - lum) ** 4 * np.array([0.008, 0.004, 0.0], np.float32)
    a = a * (1 + lum ** 2 * np.array([0.025, 0.008, -0.025], np.float32))
    return a * VIN + rng.normal(0, 0.011, a.shape[:2])[..., None]

def movil(a):
    """Leve barril de gran angular y aberración cromática en los bordes, como la cámara de un móvil."""
    out = np.empty_like(a)
    for c, k in ((0, 0.012), (1, 0.010), (2, 0.008)):
        f_ = 1 - k * R2; sx = np.clip((xx - W / 2) * f_ + W / 2, 0, W - 1).astype(np.int32); sy = np.clip((yy - H / 2) * f_ + H / 2, 0, H - 1).astype(np.int32)
        out[..., c] = a[sy, sx, c]
    return out

# ---- mano real (recortes de mascaras_mano.py): mismo encuadre que el vídeo del fabricante (x1,5, bajado 200 px) ----
ESC, BAJA = 1.5, 200
def mano(fondo, f):
    i = f - P['mano'][0] + 1
    rec = Image.open(os.path.join(AQUI, 'mano', 'recorte', f'm{i:03d}.png')).convert('RGBA').resize((int(720 * ESC), int(960 * ESC)), Image.LANCZOS)
    lienzo = Image.new('RGBA', (W, H)); lienzo.paste(rec, (0, BAJA)); c = np.asarray(lienzo).astype(np.float32) / 255
    A = c[..., 3:4]; C = c[..., :3]
    orig = np.asarray(Image.open(os.path.join(AQUI, 'mano', 'orig', f'm{i:03d}.png')).convert('RGB')).astype(np.float32) / 255
    ref = orig[560:640, 560:700].reshape(-1, 3).mean(0)                      # pared del vídeo junto a la mano
    yF, xF = int(600 * ESC + BAJA), int(630 * ESC); obj = fondo[yF - 50:yF + 50, xF - 90:xF + 90].reshape(-1, 3).mean(0)
    Cg = np.clip(C * (obj / ref) * 0.97, 0, 1)                                # misma luz que la pared rosa (un pelín más oscura: piel)
    blanco = np.clip((C.mean(2, keepdims=True) - 0.78) / 0.12, 0, 1)          # la espuma se queda blanca
    C = Cg * (1 - blanco) + C * blanco
    s = np.asarray(Image.fromarray((A[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30))).astype(np.float32) / 255
    S = np.zeros((H, W), np.float32); S[45:, 35:] = s[:-45, :-35]
    base = fondo * (1 - 0.30 * S[..., None])
    return base * (1 - A) + C * A

TEXTOS = {   # plano: [(partes, cy, tam, desde, hasta)] en fotogramas relativos al plano
    'mano': [([('Espuma ', BLANCO), ('al instante', ORO)], 0.13, 92, 4, None)],
    'pantalla': [([('Hora y ', BLANCO), ('temperatura', ORO)], 0.13, 92, 4, None)],
    'botones': [([('3 niveles ', ORO), ('de espuma', BLANCO)], 0.13, 92, 4, None)],
    'apagado': [([('Se apaga ', BLANCO), ('solo', ORO)], 0.13, 100, 18, None)],
    'adhesivo': [([('Se pega. ', BLANCO), ('Sin taladros.', ORO)], 0.13, 92, 6, None)],
    'usb': [([('Recargable ', BLANCO), ('USB-C', ORO)], 0.13, 92, 4, None)],
    'versiones': [([('Negro ', BLANCO), ('o blanco', ORO)], 0.13, 100, 6, None)],
}
SOLO = [int(x) for x in os.environ.get('SOLO', '').split(',') if x]     # prueba: solo estos fotogramas, sin sonido
for f in (SOLO or range(1, N + 1)):
    n = plano(f); a0, a1 = P[n]; r = f - a0
    a = np.asarray(Image.open(os.path.join(DIR, f'f{f:04d}.png')).convert('RGB').resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    if n == 'mano': a = mano(a, f)
    a = acabado(a)
    if n in ('entrada', 'mano'): a = movil(a)                                # los planos «grabados con el móvil»
    im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).filter(ImageFilter.UnsharpMask(radius=1.6, percent=50, threshold=2))
    sale = suave((a1 - f) / 5) if f > a1 - 5 else 1.0
    if n == 'entrada':
        k1 = 1.0 if f < LED_ON - 4 else suave((LED_ON - f) / 4)
        im = texto(im, [('Mi baño ahora', BLANCO)], 0.13, 96, k1)
        im = texto(im, [('hace ', BLANCO), ('esto…', ORO)], 0.19, 96, k1)
        im = texto(im, [('Ni lo ', BLANCO), ('toques.', ORO)], 0.15, 120, suave((f - LED_ON) / 8) * sale)
    for partes, cy, tam, d_, h_ in TEXTOS.get(n, []):
        im = texto(im, partes, cy, tam, suave((r - d_) / 8) * sale)
    if n == 'botones': im = niveles(im, f, suave((r - 8) / 8) * sale)
    if n == 'versiones': im = pastilla(im, 'Pídelo hoy', 0.80, 84, suave((r - 50) / 10))
    im.convert('RGB').save(os.path.join(TMP, f'p{f:04d}.png'))

if SOLO: sys.exit()
# ---- sonido: música + efectos en su sitio ----
SR = 48000; n_ = int(SR * N / FPS)
def leer(nombre):
    x = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(AQUI, 'sonidos', nombre + '.mp3'), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True, check=True).stdout
    x = np.frombuffer(x, np.float32).reshape(-1, 2).copy(); return x / (np.abs(x).max() + 1e-9)
mezcla = np.zeros((n_, 2), np.float32)
def poner(nombre, f, g):
    x = leer(nombre); i = int((f - 1) / FPS * SR); x = x[: n_ - i]; mezcla[i:i + len(x)] += x * g
musica = leer('musica')[:n_]; mezcla[:len(musica)] += musica * 0.5
b0 = P['botones'][0]
for nombre, f, g in (('ambiente', 1, 0.3), ('pasos', 1, 0.45), ('encendido', LED_ON, 0.6), ('espuma', P['mano'][0] + 4, 0.7),
                     ('clic', b0 + 13, 0.6), ('clic', b0 + 29, 0.6), ('clic', b0 + 45, 0.6), ('apagado', P['apagado'][0] + 22, 0.5),
                     ('pegado', P['adhesivo'][0] + 37, 0.7), ('conector', P['usb'][0] + 22, 0.7), ('encendido', P['versiones'][0] + 2, 0.35)):
    poner(nombre, f, g)
fin = np.clip((n_ - np.arange(n_)) / (SR * 0.6), 0, 1)[:, None]; mezcla *= fin
mezcla /= max(1.0, np.abs(mezcla).max() / 0.95)
wav = os.path.join(TMP, 'audio.wav')
with wave.open(wav, 'wb') as w_:
    w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((mezcla * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(TMP, 'p%04d.png'), '-i', wav,
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart',
                '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-14:TP=-1.5', '-shortest', SALIDA], check=True)
print('vídeo ok', SALIDA)
