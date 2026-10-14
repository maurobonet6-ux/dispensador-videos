# Montaje del arranque en el baño: aspecto de vídeo de móvil (leve distorsión de lente, aberración, grano, nitidez), brillo del LED,
# gancho de texto desde el primer fotograma y sonido (pasos, ambiente, campanilla del sensor). Uso: python3 montaje_bano.py DIR_RENDER SALIDA.mp4
import os, sys, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DIR, SALIDA = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(AQUI, 'post'); os.makedirs(TMP, exist_ok=True)
W, H, FPS, N = 1080, 1920, 30, 105
LED_ON = 64
F = '/usr/share/fonts/opentype/inter/InterDisplay-'
BLANCO = (247, 245, 242); ORO = (232, 168, 136)

def suave(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

def letras(d, x, y, t, fnt, fill, trk):
    for ch in t: d.text((x, y), ch, font=fnt, fill=fill); x += d.textlength(ch, font=fnt) + trk
def ancho(d, t, fnt, trk): return sum(d.textlength(ch, font=fnt) for ch in t) + trk * (len(t) - 1)

def texto(im, partes, cy, tam, k, fuente='Bold', trk=0.02, sube=0.0):
    """Una línea centrada hecha de (texto, color); entra con desenfoque y subiendo un poco (k: 0 → 1)."""
    if k <= 0: return im
    fnt = ImageFont.truetype(F + fuente + '.otf', tam); d0 = ImageDraw.Draw(im); tr = tam * trk
    total = sum(ancho(d0, t, fnt, tr) for t, _ in partes) + tr * (len(partes) - 1)
    x = (W - total) / 2; y = H * cy - tam * 0.6 + (1 - k) * H * sube
    capa = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
    for t, col in partes:
        letras(dc, x, y, t, fnt, col + (int(255 * k),), tr); x += ancho(dc, t, fnt, tr) + tr
    if k < 1: capa = capa.filter(ImageFilter.GaussianBlur(14 * (1 - k)))
    sombra = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sombra.putalpha(capa.split()[3].filter(ImageFilter.GaussianBlur(18)).point(lambda p: int(p * 0.55)))
    im = Image.alpha_composite(im.convert('RGBA'), sombra); return Image.alpha_composite(im, capa)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIN = (1 - 0.42 * np.clip(((xx - W / 2) / (W / 2)) ** 2 * 0.55 + ((yy - H / 2) / (H / 2)) ** 2 * 0.45, 0, 1))[..., None]
rng = np.random.default_rng(3)

def acabado(im):
    a = np.asarray(im).astype(np.float32) / 255
    lum = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    brillo = np.clip(a - 0.9, 0, 1) * 4                                         # bloom: solo lo más brillante (LED, reflejos), no la pared
    b = np.asarray(Image.fromarray((brillo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(26))).astype(np.float32) / 255
    b2 = np.asarray(Image.fromarray((brillo * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(70))).astype(np.float32) / 255
    a = a + b * 0.5 + b2 * 0.3
    a = a + (1 - lum) ** 4 * np.array([0.010, 0.006, 0.0], np.float32)       # sombras algo cálidas
    a = a * (1 + lum ** 2 * np.array([0.03, 0.01, -0.03], np.float32))        # luces cálidas
    a = a * VIN + rng.normal(0, 0.010, a.shape[:2])[..., None]                  # viñeta y grano fino
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))

def movil(im):
    """Aspecto de vídeo grabado con móvil: leve barril de gran angular y aberración cromática en los bordes."""
    a = np.asarray(im).astype(np.float32)
    r2 = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    out = np.empty_like(a)
    for c, k in ((0, 0.012), (1, 0.010), (2, 0.008)):
        f_ = 1 - k * r2; sx = np.clip((xx - W / 2) * f_ + W / 2, 0, W - 1).astype(np.int32); sy = np.clip((yy - H / 2) * f_ + H / 2, 0, H - 1).astype(np.int32)
        out[..., c] = a[sy, sx, c]
    return Image.fromarray(out.astype(np.uint8))

for f in range(1, N + 1):
    im = Image.open(os.path.join(DIR, f'f{f:04d}.png')).convert('RGB').resize((W, H), Image.LANCZOS)
    im = movil(acabado(im)).filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    # gancho desde el primer fotograma; al encenderse la pantalla cambia a «Ni lo toques.»
    k1 = 1.0 if f < LED_ON - 4 else suave((LED_ON - f) / 4)
    im = texto(im, [('Mi baño ahora', BLANCO)], 0.14, 92, k1, fuente='Black', trk=0.0)
    im = texto(im, [('hace ', BLANCO), ('esto…', ORO)], 0.195, 92, k1, fuente='Black', trk=0.0)
    k2 = suave((f - LED_ON) / 8)
    im = texto(im, [('Ni lo ', BLANCO), ('toques.', ORO)], 0.16, 118, k2, fuente='Black', trk=0.0, sube=0.015)
    im.convert('RGB').save(os.path.join(TMP, f'p{f:04d}.png'))

# sonido: ambiente + barrido al empezar + campanilla al encenderse + espuma
SR = 48000; n = int(SR * N / FPS)
def leer(nombre):
    x = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(AQUI, 'sonidos', nombre + '.mp3'), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                       capture_output=True, check=True).stdout
    x = np.frombuffer(x, np.float32).reshape(-1, 2).copy(); return x / (np.abs(x).max() + 1e-9)
mezcla = np.zeros((n, 2), np.float32)
for nombre, f, g in (('ambiente', 1, 0.45), ('pasos', 1, 0.5), ('encendido', LED_ON, 0.7)):
    x = leer(nombre); i = int((f - 1) / FPS * SR); x = x[: n - i]; mezcla[i:i + len(x)] += x * g
fin = np.clip((n - np.arange(n)) / (SR * 0.25), 0, 1)[:, None]; mezcla *= fin
mezcla /= max(1.0, np.abs(mezcla).max() / 0.95)
wav = os.path.join(TMP, 'audio.wav')
with wave.open(wav, 'wb') as w_:
    w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(SR); w_.writeframes((mezcla * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(TMP, 'p%04d.png'), '-i', wav,
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart',
                '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-14:TP=-1.5', '-shortest', SALIDA], check=True)
print('teaser ok', SALIDA)
