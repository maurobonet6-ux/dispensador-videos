# Pantalla LED del dispensador: temperatura arriba y hora abajo, en dígitos de 7 segmentos azules, como el producto real.
# Uso: python3 pantalla_led.py HORA TEMP SALIDA.png   (p. ej. 07:30 22 led.png). Fondo negro: en la escena es emisión.
import sys
from PIL import Image, ImageDraw, ImageFilter

W, H = 2048, 1060                     # misma proporción que el cristal frontal (0,228 x 0,118 m)
AZUL = (70, 130, 255)
SEG = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc',
       '8': 'abcdefg', '9': 'abfgcd'}

def segmento(d, x0, y0, x1, y1, grosor, col):
    """Segmento con puntas en bisel (como un display LED real)."""
    g = grosor / 2
    if y0 == y1:   # horizontal
        pts = [(x0 + g, y0), (x0 + 2 * g, y0 - g), (x1 - 2 * g, y0 - g), (x1 - g, y0), (x1 - 2 * g, y0 + g), (x0 + 2 * g, y0 + g)]
    else:          # vertical
        pts = [(x0, y0 + g), (x0 + g, y0 + 2 * g), (x0 + g, y1 - 2 * g), (x0, y1 - g), (x0 - g, y1 - 2 * g), (x0 - g, y0 + 2 * g)]
    d.polygon(pts, fill=col)

def digito(d, ch, x, y, w, h, grosor, col):
    """Un dígito de 7 segmentos con su esquina de arriba a la izquierda en (x, y), algo inclinado."""
    k = 0.08 * w                                        # inclinación (los LED reales van un poco en cursiva)
    P = {'a': (x + k, y, x + w + k, y), 'g': (x + k / 2, y + h / 2, x + w + k / 2, y + h / 2), 'd': (x, y + h, x + w, y + h),
         'f': (x + k, y, x + k / 2, y + h / 2), 'b': (x + w + k, y, x + w + k / 2, y + h / 2),
         'e': (x + k / 2, y + h / 2, x, y + h), 'c': (x + w + k / 2, y + h / 2, x + w, y + h)}
    for s in SEG[ch]:
        x0, y0, x1, y1 = P[s]
        if y0 == y1: segmento(d, x0, y0, x1, y1, grosor, col)
        else:        # los verticales inclinados: polígono a mano
            g = grosor / 2
            d.polygon([(x0, y0 + g), (x0 + g, y0 + 2 * g), (x1 + g, y1 - 2 * g), (x1, y1 - g), (x1 - g, y1 - 2 * g), (x0 - g, y0 + 2 * g)], fill=col)

def pantalla(hora, temp, salida):
    im = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    # temperatura (arriba, centrada a la izquierda) + «°C» + icono de persona y batería
    w, h, gr = 120, 200, 26
    tx = W / 2 - 150; ty = 250
    for i, ch in enumerate(temp): digito(d, ch, tx + i * (w + 50), ty, w, h, gr, AZUL)
    d.ellipse((tx + 2 * (w + 50) + 10, ty, tx + 2 * (w + 50) + 34, ty + 24), outline=AZUL, width=6)        # °
    d.text((tx + 2 * (w + 50) + 40, ty - 6), 'C', fill=AZUL, font=None)
    px, py = tx - 120, ty + 10                                                                              # persona (sensor)
    d.ellipse((px, py, px + 34, py + 34), outline=AZUL, width=7); d.arc((px - 14, py + 36, px + 48, py + 96), 180, 360, fill=AZUL, width=7)
    bx, by = tx + 2 * (w + 50) + 70, ty + 120                                                               # batería (verde)
    d.rounded_rectangle((bx, by, bx + 60, by + 30), radius=5, outline=(70, 220, 120), width=6)
    d.rectangle((bx + 10, by + 9, bx + 44, by + 21), fill=(70, 220, 120)); d.rectangle((bx + 60, by + 9, bx + 66, by + 21), fill=(70, 220, 120))
    # hora (abajo, más grande): HH:MM
    w, h, gr = 150, 250, 30
    total = 4 * w + 3 * 60 + 80; hx = (W - total) / 2; hy = 560
    xs = []
    x = hx
    for i, ch in enumerate(hora):
        if ch == ':':
            for cy in (hy + h * 0.3, hy + h * 0.72): d.rectangle((x + 20, cy - 15, x + 50, cy + 15), fill=AZUL)
            x += 80; continue
        digito(d, ch, x, hy, w, h, gr, AZUL); x += w + 60
    im = im.filter(ImageFilter.GaussianBlur(2))         # bordes suaves de LED tras el cristal
    im.save(salida)

if __name__ == '__main__':
    pantalla(sys.argv[1], sys.argv[2], sys.argv[3])
