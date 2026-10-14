# Fondo 3D del plano «mano real»: la cámara fija se coloca para que el dispensador 3D quede exactamente donde estaba el real en el
# vídeo del fabricante (boquilla en el mismo píxel, mismo ancho). Un solo fotograma: LED encendido, sin espuma 3D.
# Uso: python3.11 plano_mano.py SALIDA.png [ANCHO] [MUESTRAS]
import sys, os, math
AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = sys.argv[1]; ANCHO = sys.argv[2] if len(sys.argv) > 2 else '1080'; MU = sys.argv[3] if len(sys.argv) > 3 else '256'
src = open(os.path.join(AQUI, 'escena.py')).read(); src = src[:src.index('LISTA = ')]
sys.argv = ['escena.py', '--salida', os.path.dirname(os.path.abspath(SALIDA)), '--ancho', ANCHO, '--muestras', MU]
g = {'__file__': os.path.join(AQUI, 'escena.py'), '__name__': '__main__'}
exec(compile(src, g['__file__'], 'exec'), g)
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sc, cam, cd, D, W, H, BOQ = g['sc'], g['cam'], g['cd'], g['D'], g['W'], g['H'], g['BOQ']

# Dónde estaba el dispensador real (vídeo 720x960 escalado x1,5 y bajado 200 px en el plano final 1080x1920)
ESC, BAJA = 1.5, 200
def obj(px, py): return (px * ESC / 1080, 1 - (py * ESC + BAJA) / 1920)      # → coordenadas de cámara (0..1, y hacia arriba)
BOQ_OBJ = obj(352, 527); IZQ_OBJ = obj(100, 330)[0]; DER_OBJ = obj(715, 330)[0]

sc.frame_set(80)
for o in (cam, g['mira']): o.animation_data_clear()
cam.constraints.clear(); cam.rotation_mode = 'QUATERNION'; cd.lens = 42
g['espuma'].animation_data_clear(); g['espuma'].hide_render = True
mp = g['mp_']; mp.node_tree.animation_data_clear(); g['on'].outputs[0].default_value = 2.0
DIR = Vector((0.22, -1.0, 0.02)).normalized()                                 # un poco desde la derecha, como en el vídeo
mira = Vector((0.0, -D, -0.03)); dist = 0.5
punta = BOQ - Vector((0, 0, 0.009))
for _ in range(60):                                                           # ajuste: ancho del aparato y posición de la boquilla
    cam.location = mira + DIR * dist
    cam.rotation_quaternion = (mira - cam.location).to_track_quat('-Z', 'Y'); bpy.context.view_layer.update()
    xs = [world_to_camera_view(sc, cam, Vector((sx * W / 2, sy, 0.0))).x for sx in (-1, 1) for sy in (-D - 0.005, 0.0)]
    p = world_to_camera_view(sc, cam, punta)
    ancho, ancho_obj = max(xs) - min(xs), DER_OBJ - IZQ_OBJ
    dist *= ancho / ancho_obj
    mira.x += (p.x - BOQ_OBJ[0]) * 0.25; mira.z += (p.y - BOQ_OBJ[1]) * 0.35
print('boquilla', round(p.x, 3), round(p.y, 3), 'objetivo', [round(v, 3) for v in BOQ_OBJ], 'ancho', round(ancho, 3), round(ancho_obj, 3))
g['foco'].location = Vector((0, -D - 0.005, -0.01)); cd.dof.aperture_fstop = 4.0
sc.render.filepath = SALIDA; bpy.ops.render.render(write_still=True); print('fondo ok', SALIDA)
