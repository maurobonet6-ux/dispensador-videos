# Arranque del vídeo: entras al baño (escena «Modern Bathroom» de dylanheyes, Sketchfab, CC BY 4.0) grabando con el móvil,
# te acercas al lavabo y el dispensador, ya instalado junto al espejo, enciende su pantalla al detectarte.
# Luz real: sol por la ventana en arco, cielo exterior (HDRI), lámpara colgante y LED del espejo encendidos.
# Uso: python3.11 escena_bano.py --salida DIR [--ancho 1080] [--muestras 256] [--lista 1,40,90] [--desde 1 --hasta 105]
import sys, os, math, argparse, glob

AQUI = os.path.dirname(os.path.abspath(__file__)); REC = os.path.join(AQUI, 'recursos')
a = argparse.ArgumentParser()
a.add_argument('--salida', required=True); a.add_argument('--ancho', type=int, default=1080); a.add_argument('--muestras', type=int, default=256)
a.add_argument('--desde', type=int, default=1); a.add_argument('--hasta', type=int, default=105); a.add_argument('--lista', default='')
args = a.parse_args()

# ---------- 1. el dispensador (el mismo modelo de escena.py, en metros, con la espalda en y=0 mirando a -y) ----------
src = open(os.path.join(AQUI, 'escena.py')).read(); src = src[:src.index('# ---------- espuma')]
sys.argv = ['escena.py', '--salida', args.salida, '--ancho', str(args.ancho), '--muestras', str(args.muestras)]
g = {'__file__': os.path.join(AQUI, 'escena.py'), '__name__': '__main__'}
exec(compile(src, g['__file__'], 'exec'), g)
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
sc = g['sc']; principled, tex_pbr = g['principled'], g['tex_pbr']
piezas = [o for o in sc.objects if o.parent is None]
raiz = bpy.data.objects.new('Dispensador', None); sc.collection.objects.link(raiz)
for o in piezas: o.parent = raiz
FPS, TOTAL = 30, 105
T_LED = 64                                   # la pantalla se enciende al detectarte (te acercas al lavabo)
on = g['on']; g['mp_'].node_tree.animation_data_clear()
for f, v in ((1, 0), (T_LED, 0), (T_LED + 1, 1.4), (T_LED + 2, 0.3), (T_LED + 4, 2.0)):
    on.outputs[0].default_value = v; on.outputs[0].keyframe_insert('default_value', frame=f)
for fc in g['curvas'](g['mp_'].node_tree):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ---------- 2. el baño (FBX) a escala real ----------
_l = bpy.data.lights.new('_x', 'POINT'); type(_l.cycles).cast_shadow = bpy.props.BoolProperty(); bpy.data.lights.remove(_l)  # fallo del importador FBX
antes = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=glob.glob(os.path.join(REC, 'bano', 'src', '**', '*.fbx'), recursive=True)[0])
nuevos = [o for o in bpy.data.objects if o not in antes]
ESC = 0.47                                    # el modelo está a ~2,1x: el mueble del lavabo pasa a medir ~98 cm
for o in [o for o in nuevos if o.type == 'LIGHT']: bpy.data.objects.remove(o)
nuevos = [o for o in bpy.data.objects if o not in antes]
for o in nuevos:
    if o.parent is None: o.matrix_world = Matrix.Scale(ESC, 4) @ o.matrix_world
bano = bpy.data.objects['Bathroom']; bpy.context.view_layer.update()

# quitar la balda estrecha de detrás del lavabo y sus botes (estorbaban al dispensador); las plantas bajan a la encimera
bm = bmesh.new(); bm.from_mesh(bano.data)
fuera = {i for i, m in enumerate(bano.data.materials) if m.name in ('SkirtingBoard', 'Bottles')}
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in fuera], context='FACES'); bm.to_mesh(bano.data); bm.free()
plantas = bpy.data.objects['Plants']; bb = [plantas.matrix_world @ Vector(c) for c in plantas.bound_box]
ENCIMERA = 2.36 * ESC + 0.002
plantas.location += Vector((-0.70 - min(v.x for v in bb), 0, ENCIMERA - min(v.z for v in bb)))

# pared del fondo exacta (rayo hacia la pared) y sitio del dispensador: a la derecha del espejo, sobre el lavabo
dg = bpy.context.evaluated_depsgraph_get()
ok, loc, *_ = sc.ray_cast(dg, Vector((-0.04, 0.0, 1.30)), Vector((0, 1, 0)))
PARED_Y = loc.y if ok else 1.80
raiz.location = (-0.04, PARED_Y - 0.0005, 1.30)
# tapa el hueco que deja la balda quitada (por detrás de la pared, solo se ve por el hueco)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, PARED_Y + 0.003, 1.24), rotation=(math.radians(90), 0, 0))
tapa_hueco = bpy.context.object; tapa_hueco.scale = (3.0, 0.2, 1); tapa_hueco.name = 'TapaHueco'

# ---------- 3. materiales: superficies grandes en alta resolución con luz real; muebles con su textura ----------
def textura(m):
    return next((n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'), None) if m and m.node_tree else None
def con_textura(nombre, img, rug=0.5, coat=0.0, metal=0.0, brillo=1.0):
    m = principled(nombre, rug=rug, coat=coat, metal=metal); N, L = m.node_tree.nodes, m.node_tree.links
    t = N.new('ShaderNodeTexImage'); t.image = img; col = t.outputs['Color']
    if brillo != 1.0:
        hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = brillo; L.new(col, hs.inputs['Color']); col = hs.outputs['Color']
    L.new(col, N['Principled BSDF'].inputs['Base Color']); return m

rosa = tex_pbr(principled('ParedRosa'), 'painted_plaster_wall', 1.2, tinte=(0.95, 0.58, 0.50), sat=0.0, valor=1.1, normal=0.35, coords='Object')
blanca = tex_pbr(principled('ParedBlanca'), 'painted_plaster_wall', 1.2, tinte=(0.92, 0.90, 0.86), sat=0.0, valor=1.1, normal=0.3, coords='Object')
techo = principled('Techo', (0.86, 0.85, 0.82), rug=0.9)
suelo = tex_pbr(principled('Suelo'), 'large_floor_tiles_02', 0.9, tinte=(0.95, 0.90, 0.82), sat=0.3, normal=0.5, coords='Object')
for m_ in (rosa, blanca, suelo):                    # proyección en caja: la textura no se estira en las paredes verticales
    for n_ in m_.node_tree.nodes:
        if n_.type == 'TEX_IMAGE': n_.projection = 'BOX'; n_.projection_blend = 0.25
espejo = principled('EspejoReal', (0.92, 0.92, 0.92), metal=1.0, rug=0.01)
led_espejo = bpy.data.materials.new('LEDespejo'); Ne = led_espejo.node_tree.nodes
Ne.remove(Ne['Principled BSDF']); em = Ne.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.82, 0.62, 1); em.inputs['Strength'].default_value = 6
led_espejo.node_tree.links.new(em.outputs[0], Ne['Material Output'].inputs['Surface'])
ventana = bpy.data.materials.new('Hueco'); Nv = ventana.node_tree.nodes; Nv.remove(Nv['Principled BSDF'])
tr = Nv.new('ShaderNodeBsdfTransparent'); ventana.node_tree.links.new(tr.outputs[0], Nv['Material Output'].inputs['Surface'])
cromo = principled('CromoReal', (0.9, 0.9, 0.92), metal=1.0, rug=0.06)
AJUSTE = {'Cabinet': dict(rug=0.28, coat=0.35, brillo=1.15), 'Toilet': dict(rug=0.12, coat=0.7, brillo=1.15), 'MirrorTrim': dict(rug=0.3, brillo=1.1),
          'WindowTrim': dict(rug=0.4, brillo=1.15), 'Picture': dict(rug=0.6), 'PictureFrame': dict(rug=0.4), 'ToiletRug': dict(rug=0.95),
          'ToiletRoll': dict(rug=0.8), 'ToiletRolls': dict(rug=0.8), 'ToiletFlushButton': dict(rug=0.2, metal=0.6), 'Light': dict(rug=0.3)}
for o in [o for o in nuevos if o.type == 'MESH']:
    me = o.data
    for i, m in enumerate(me.materials):
        if m is None: continue
        n = m.name.split('.')[0]
        if n == 'BackWall': me.materials[i] = rosa
        elif n in ('SideWalls', 'Floor'): me.materials[i] = blanca
        elif n == 'Mirror': me.materials[i] = espejo
        elif n == 'MirrorLight': me.materials[i] = led_espejo
        elif n == 'WindowLight': me.materials[i] = ventana
        elif n == 'Chrome': me.materials[i] = cromo
        elif textura(m) is not None: me.materials[i] = con_textura(n + '_real', textura(m), **AJUSTE.get(n, {'rug': 0.6}))
bpy.data.objects['TapaHueco'].data.materials.append(rosa)
# paredes laterales, suelo y techo vienen juntos: se separan por la orientación de cada cara
me = bano.data
for mat in (suelo, techo): me.materials.append(mat)
i_suelo, i_techo, i_blanca = len(me.materials) - 2, len(me.materials) - 1, list(me.materials).index(blanca)
for p in me.polygons:
    if p.material_index != i_blanca: continue
    if p.normal.z > 0.9 and p.center.z * ESC < 0.2: p.material_index = i_suelo
    elif p.normal.z < -0.9: p.material_index = i_techo

# ---------- 4. luz real ----------
w = bpy.data.worlds.new('Cielo'); sc.world = w; WN, WL = w.node_tree.nodes, w.node_tree.links
env = WN.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(REC, 'sunny_rose_garden_2k.hdr'))
WL.new(env.outputs['Color'], WN['Background'].inputs['Color']); WN['Background'].inputs['Strength'].default_value = 1.2
sol = bpy.data.lights.new('Sol', 'SUN'); sol.energy = 5.5; sol.angle = math.radians(1.2); sol.color = (1.0, 0.93, 0.82)
so = bpy.data.objects.new('Sol', sol); sc.collection.objects.link(so)
so.rotation_euler = (Vector((1.0, 0.35, -0.75))).to_track_quat('-Z', 'Y').to_euler()   # entra por la ventana de la izquierda, alto
VX = -3.17 * ESC                                                                          # ventana (pared izquierda)
port = bpy.data.lights.new('Portal', 'AREA'); port.shape = 'RECTANGLE'; port.size = 2.6 * ESC; port.size_y = 4.0 * ESC
if hasattr(port.cycles, 'is_portal'): port.cycles.is_portal = True
po = bpy.data.objects.new('Portal', port); sc.collection.objects.link(po); po.location = (VX + 0.01, 1.04 * ESC, 2.3 * ESC)
po.rotation_euler = (0, math.radians(90), 0)
bombilla = bpy.data.lights.new('Colgante', 'POINT'); bombilla.energy = 25; bombilla.color = (1.0, 0.78, 0.55); bombilla.shadow_soft_size = 0.05
bo = bpy.data.objects.new('Colgante', bombilla); sc.collection.objects.link(bo); bo.location = (1.07 * ESC, 3.0 * ESC, 3.45 * ESC)
rebote = bpy.data.lights.new('Rebote', 'AREA'); rebote.energy = 18; rebote.size = 1.2; rebote.color = (1.0, 0.95, 0.9)
ro = bpy.data.objects.new('Rebote', rebote); sc.collection.objects.link(ro); ro.location = (0.2, -1.0, 1.9)
ro.rotation_euler = (Vector((-0.2, PARED_Y, 1.2)) - ro.location).to_track_quat('-Z', 'Y').to_euler(); ro.visible_camera = False

# ---------- 5. cámara de móvil en mano: entras al baño y te acercas al lavabo ----------
cd = bpy.data.cameras.new('Movil'); cam = bpy.data.objects.new('Movil', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_mode = 'QUATERNION'
cd.lens = 24; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 36                         # gran angular del móvil
cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.0; cd.dof.focus_object = None
def suave(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
DISP = Vector((-0.04, PARED_Y - 0.09, 1.30))
P0, P1 = Vector((0.45, -1.75, 1.58)), Vector((0.06, PARED_Y - 0.58, 1.44))               # de la puerta a delante del lavabo
M0, M1 = Vector((-0.35, PARED_Y, 1.25)), DISP + Vector((0, 0, -0.10))
for f in range(1, TOTAL + 1):
    t = suave((f - 1) / 72) if f <= 73 else 1.0
    pos = P0.lerp(P1, t); mira = M0.lerp(M1, suave((f - 1) / 80))
    paso = (1 - t) ** 0.5                                                                   # el balanceo de andar se calma al llegar
    pos += Vector((0.006 * math.sin(f / FPS * 2 * math.pi * 0.95) * paso, 0, 0.011 * abs(math.sin(f / FPS * 2 * math.pi * 0.95)) * paso))
    pos += Vector((0.0015 * math.sin(f * 0.37), 0.001 * math.sin(f * 0.23), 0.0012 * math.sin(f * 0.41 + 1)))   # pulso de la mano
    q = (mira - pos).to_track_quat('-Z', 'Y')
    q = q @ Euler((math.radians(0.35 * math.sin(f * 0.29)), math.radians(0.3 * math.sin(f * 0.21 + 2)), math.radians(0.6 * math.sin(f * 0.13) + 1.2 * paso * math.sin(f / FPS * 2 * math.pi * 0.47)))).to_quaternion()
    cam.location = pos; cam.rotation_quaternion = q
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_quaternion', frame=f)
    cd.dof.focus_distance = (DISP - pos).length if f > 40 else (M0 - pos).length; cd.dof.keyframe_insert('focus_distance', frame=f)
for fc in g['curvas'](cam):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ---------- render ----------
r = sc.render; r.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.cycles.blur_glossy = 0.3; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.image_settings.file_format = 'PNG'
r.resolution_x = args.ancho; r.resolution_y = round(args.ancho * 16 / 9); sc.view_settings.view_transform = 'AgX'
sc.cycles.samples = args.muestras; sc.cycles.max_bounces = 10; sc.cycles.diffuse_bounces = 6
sc.cycles.adaptive_threshold = 0.01; sc.frame_end = TOTAL
sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0.6
LISTA = [int(x) for x in args.lista.split(',')] if args.lista else range(args.desde, args.hasta + 1)
import time
for f in LISTA:
    sc.frame_set(f); r.filepath = os.path.join(args.salida, f'f{f:04d}.png')
    t0 = time.time(); bpy.ops.render.render(write_still=True); print(f'fotograma {f}: {time.time() - t0:.1f} s', flush=True)
