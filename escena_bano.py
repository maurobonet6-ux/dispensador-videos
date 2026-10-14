# Arranque del vídeo: entras al baño (escena «Modern Bathroom» de dylanheyes, Sketchfab, CC BY 4.0) grabando con el móvil,
# te acercas al lavabo y el dispensador, ya instalado junto al espejo, enciende su pantalla al detectarte.
# Luz real: sol por la ventana en arco, cielo exterior (HDRI), lámpara colgante y LED del espejo encendidos.
# Uso: python3.11 escena_bano.py --salida DIR [--ancho 1080] [--muestras 256] [--lista 1,40,90] [--desde 1 --hasta 105]
import sys, os, math, argparse, glob

AQUI = os.path.dirname(os.path.abspath(__file__)); REC = os.path.join(AQUI, 'recursos')
a = argparse.ArgumentParser()
a.add_argument('--salida', required=True); a.add_argument('--ancho', type=int, default=1080); a.add_argument('--muestras', type=int, default=256)
a.add_argument('--desde', type=int, default=1); a.add_argument('--hasta', type=int, default=570); a.add_argument('--lista', default='')
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
FPS = 30
# Planos (fotogramas globales): entrada, mano real, pantalla, botones, apagado, adhesivo, USB-C, dos versiones
PLANOS = [('entrada', 1, 105), ('mano', 106, 153), ('pantalla', 154, 225), ('botones', 226, 285), ('apagado', 286, 345),
          ('adhesivo', 346, 405), ('usb', 406, 450), ('versiones', 451, 570)]
TOTAL = PLANOS[-1][2]
P = {n: (a_, b_) for n, a_, b_ in PLANOS}
T_LED = 64                                   # la pantalla se enciende al detectarte (te acercas al lavabo)
on = g['on']; g['mp_'].node_tree.animation_data_clear()
a5 = P['apagado'][0]
for f, v in ((1, 0), (T_LED, 0), (T_LED + 1, 1.4), (T_LED + 2, 0.3), (T_LED + 4, 2.0), (a5 + 22, 2.0), (a5 + 40, 0.0),    # se apaga sola
             (P['adhesivo'][1], 0.0), (P['usb'][0], 2.0), (TOTAL, 2.0)):
    on.outputs[0].default_value = v; on.outputs[0].keyframe_insert('default_value', frame=f)
for fc in g['curvas'](g['mp_'].node_tree):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
# cristal con huellas y marcas casi invisibles (lo que delata que es real)
g['micro'](bpy.data.materials['CristalM'], escala=120, fuerza=0.004, rug=(0.0, 0.07))

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
ok, loc, *_ = sc.ray_cast(dg, Vector((0.06, 0.0, 1.43)), Vector((0, 1, 0)))
PARED_Y = loc.y if ok else 1.80
X0, Z0 = 0.06, 1.43                                # anclado a la pared, 13 cm por encima del resalte
raiz.location = (X0, PARED_Y - 0.0005, Z0)
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

rosa = tex_pbr(principled('ParedRosa'), 'painted_plaster_wall', 3.5, tinte=(1.0, 0.64, 0.56), sat=0.0, valor=1.3, normal=0.22, coords='Object')
blanca = tex_pbr(principled('ParedBlanca'), 'painted_plaster_wall', 3.5, tinte=(0.92, 0.90, 0.86), sat=0.0, valor=1.1, normal=0.3, coords='Object')
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
rebote = bpy.data.lights.new('Rebote', 'AREA'); rebote.energy = 40; rebote.size = 1.2; rebote.color = (1.0, 0.95, 0.9)
ro = bpy.data.objects.new('Rebote', rebote); sc.collection.objects.link(ro); ro.location = (0.2, -1.0, 1.9)
ro.rotation_euler = (Vector((-0.2, PARED_Y, 1.2)) - ro.location).to_track_quat('-Z', 'Y').to_euler(); ro.visible_camera = False

# ---------- 5. piezas de los planos de producto ----------
D_, W_, H_ = g['D'], g['W'], g['H']
FRENTE = PARED_Y - D_ - 0.006                                   # cara del cristal
CENTRO = Vector((X0, PARED_Y - D_ / 2, Z0))
def ocultar_fuera(o, a_, b_):
    """Visible solo entre los fotogramas a_ y b_."""
    for f, v in ((1, True), (a_, False), (b_ + 1, True)):
        o.hide_render = v; o.keyframe_insert('hide_render', frame=f)
# placas adhesivas transparentes en la pared (se ven cuando el dispensador se separa)
acril = principled('Acrilico', (0.96, 0.96, 0.95), rug=0.22, coat=0.6, **{'Alpha': 0.45})   # almohadilla adhesiva translúcida
for dx in (-0.045, 0.045):
    pl = g['caja']('Adhesivo', (0.045, 0.0025, 0.045), (X0 + dx, PARED_Y - 0.0013, Z0), acril, bisel=0.0007)
    ocultar_fuera(pl, *P['adhesivo'])
# puerto USB-C en el lateral derecho y el cable que entra (plano USB)
negro_mate = principled('PuertoM', (0.003, 0.003, 0.003), rug=0.6)
puerto = g['caja']('Puerto', (0.004, 0.0092, 0.0034), (W_ / 2 - 0.0012, -D_ * 0.62, -0.004), negro_mate, bisel=0.0012); puerto.parent = raiz
blanco_cable = principled('CableM', (0.92, 0.92, 0.9), rug=0.35, coat=0.2)
metal_c = principled('ClavijaM', (0.85, 0.85, 0.87), metal=1.0, rug=0.15)
clavija = bpy.data.objects.new('Clavija', None); sc.collection.objects.link(clavija); clavija.parent = raiz
for nombre, tam, loc, mat in (('Funda', (0.022, 0.012, 0.0068), (0.016, 0, 0), blanco_cable), ('Punta', (0.0068, 0.0083, 0.0026), (0.0012, 0, 0), metal_c)):
    o = g['caja'](nombre, tam, loc, mat, bisel=min(tam) * 0.35); o.parent = clavija
cable = g['cilindro']('Cable', 0.0019, 0.45, (0.027 + 0.225, 0, 0), blanco_cable, rot=(0, math.radians(90), 0)); cable.parent = clavija
u0, u1 = P['usb']
for f, x in ((1, 0.08), (u0 + 6, 0.06), (u0 + 24, 0.0002), (TOTAL, 0.0002)):
    clavija.location = (W_ / 2 + x, -D_ * 0.62, -0.004); clavija.keyframe_insert('location', frame=f)
for o in [clavija] + list(clavija.children): ocultar_fuera(o, u0, u1)
# botones del lateral: tres pulsaciones (niveles 1 → 2 → 3)
botones = sorted([o for o in raiz.children if o.name.startswith('Boton')], key=lambda o: -o.location.z)
for o in botones:                                              # botones algo mayores y con aro de oro rosa, como los reales
    o.scale = (1.35, 1.35, 1.5); o.data.materials[0] = bpy.data.materials['TapaM']; o.location.x = W_ / 2 + 0.0004   # sobresalen del lateral
    aro = g['cilindro']('AroBoton', 0.0086, 0.0016, o.location + Vector((-0.0016, 0, 0)), bpy.data.materials['OroRosa'], rot=tuple(o.rotation_euler))
    aro.parent = raiz
b0 = P['botones'][0]
for o in botones:
    base = o.location.copy()
    for f in (1, b0 + 10, b0 + 13, b0 + 16, b0 + 26, b0 + 29, b0 + 32, b0 + 42, b0 + 45, b0 + 48):
        dentro = f in (b0 + 13, b0 + 29, b0 + 45) and o is botones[0]
        o.location = base - Vector((0.0016 if dentro else 0, 0, 0)); o.keyframe_insert('location', frame=f)
# el dispensador se acerca a la pared y se pega en las placas (plano adhesivo)
d0, d1 = P['adhesivo']
for f, y, interp in ((1, 0.0, 'CONSTANT'), (d0 - 1, 0.0, 'CONSTANT'), (d0, -0.16, 'BEZIER'), (d0 + 10, -0.16, 'BEZIER'), (d0 + 38, 0.001, 'BEZIER'),
                     (d0 + 41, -0.0015, 'BEZIER'), (d0 + 44, 0.0, 'BEZIER')):
    raiz.location = (X0, PARED_Y - 0.0005 + y, Z0); raiz.keyframe_insert('location', frame=f)
for fc in g['curvas'](raiz):
    for k in fc.keyframe_points:
        if k.co[0] < d0: k.interpolation = 'CONSTANT'
# versión blanca al lado (solo en el plano final)
v0, v1 = P['versiones']
blanca_raiz = bpy.data.objects.new('DispensadorBlanco', None); sc.collection.objects.link(blanca_raiz)
blanca_raiz.location = (X0 + 0.30, PARED_Y - 0.0005, Z0)
plast_b = g['micro'](principled('PlasticoBlanco', (0.86, 0.86, 0.84), rug=0.3, coat=0.35, coat_rug=0.15), escala=1400, fuerza=0.03, rug=(0.25, 0.34))
for o in [o for o in raiz.children if o.type == 'MESH' and not o.name.startswith(('Puerto',))]:
    c = o.copy(); c.data = o.data.copy(); sc.collection.objects.link(c); c.parent = blanca_raiz
    c.animation_data_clear(); c.location = o.location.copy(); c.rotation_euler = o.rotation_euler.copy(); c.scale = o.scale.copy()
    c.data.materials.clear()
    for m in o.data.materials: c.data.materials.append(plast_b if m and m.name == 'Plastico' else m)
    ocultar_fuera(c, v0, v1)

# ---------- 6. cámaras de cada plano (una clave por fotograma; en los cortes, salto limpio) ----------
cd = bpy.data.cameras.new('Movil'); cam = bpy.data.objects.new('Movil', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_mode = 'QUATERNION'; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 36
cd.dof.use_dof = True; cd.dof.aperture_blades = 7
def suave(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def pulso(f, k=1.0):                                            # temblor leve de mano / estabilizador
    return Vector((0.0015 * math.sin(f * 0.37), 0.001 * math.sin(f * 0.23), 0.0012 * math.sin(f * 0.41 + 1))) * k, \
           Euler((math.radians(0.35 * math.sin(f * 0.29) * k), math.radians(0.3 * math.sin(f * 0.21 + 2) * k), math.radians(0.5 * math.sin(f * 0.13) * k))).to_quaternion()
def clave(f, pos, mira, lente, fstop, foco, giro=None, sub=0.0):
    q = (mira - pos).to_track_quat('-Z', 'Y')
    if giro: q = q @ giro
    cam.location = pos; cam.rotation_quaternion = q; cd.lens = lente; cd.dof.aperture_fstop = fstop; cd.dof.focus_distance = foco
    for path, idb in (('location', cam), ('rotation_quaternion', cam), ('lens', cd), ('dof.aperture_fstop', cd), ('dof.focus_distance', cd)):
        idb.keyframe_insert(path, frame=f + sub)
DISP = Vector((X0, FRENTE, Z0))
camino = {}
# 1. entrada: andas con el móvil de la puerta al lavabo
e0, e1 = P['entrada']
P0, P1 = Vector((0.45, -1.75, 1.58)), Vector((X0 + 0.02, PARED_Y - 0.62, Z0 + 0.10))
M0, M1 = Vector((-0.35, PARED_Y, 1.25)), DISP + Vector((0, 0, -0.10))
for f in range(e0, e1 + 1):
    t = suave((f - e0) / 72) if f - e0 <= 72 else 1.0
    pos = P0.lerp(P1, t); mira = M0.lerp(M1, suave((f - e0) / 80)); paso = (1 - t) ** 0.5
    pos += Vector((0.006 * math.sin(f / FPS * 2 * math.pi * 0.95) * paso, 0, 0.011 * abs(math.sin(f / FPS * 2 * math.pi * 0.95)) * paso))
    dp, dq = pulso(f); giro = dq @ Euler((0, 0, math.radians(1.2 * paso * math.sin(f / FPS * 2 * math.pi * 0.47)))).to_quaternion()
    camino[f] = (pos + dp, mira, 24, 2.0, (DISP - pos).length if f - e0 > 40 else (M0 - pos).length, giro)
# 2. mano: cámara fija colocada para que el dispensador quede donde estaba el real en el vídeo del fabricante
from bpy_extras.object_utils import world_to_camera_view
m0, m1 = P['mano']
ESC_V, BAJA = 1.5, 200
def obj(px, py): return (px * ESC_V / 1080, 1 - (py * ESC_V + BAJA) / 1920)
BOQ_OBJ = obj(352, 527); ANCHO_OBJ = obj(715, 0)[0] - obj(100, 0)[0]
punta = Vector((X0, 0, Z0)) + Vector((g['BOQ'].x, PARED_Y + g['BOQ'].y, g['BOQ'].z - 0.009))
sc.frame_set(m0); cd.lens = 42; cd.sensor_fit = 'VERTICAL'
sc.render.resolution_x = args.ancho; sc.render.resolution_y = round(args.ancho * 16 / 9)   # el encaje depende del formato vertical
DIRM = Vector((0.22, -1.0, 0.02)).normalized(); mira_m = Vector((X0, FRENTE, Z0 - 0.03)); dist = 0.5
for _ in range(60):
    cam.location = mira_m + DIRM * dist; cam.rotation_quaternion = (mira_m - cam.location).to_track_quat('-Z', 'Y'); bpy.context.view_layer.update()
    xs = [world_to_camera_view(sc, cam, Vector((X0 + sx * W_ / 2, PARED_Y + sy, Z0))).x for sx in (-1, 1) for sy in (-D_ - 0.005, 0.0)]
    pp = world_to_camera_view(sc, cam, punta)
    dist *= (max(xs) - min(xs)) / ANCHO_OBJ
    mira_m.x += (pp.x - BOQ_OBJ[0]) * 0.25; mira_m.z += (pp.y - BOQ_OBJ[1]) * 0.35
print('mano: boquilla', round(pp.x, 3), round(pp.y, 3), 'objetivo', [round(v, 3) for v in BOQ_OBJ], flush=True)
for f in range(m0, m1 + 1): camino[f] = (mira_m + DIRM * dist, mira_m, 42, 4.0, dist, None)
# 3. pantalla: deslizamiento lento muy cerca del cristal
p0, p1 = P['pantalla']
for f in range(p0, p1 + 1):
    t = suave((f - p0) / (p1 - p0)); pos = Vector((X0 - 0.07 + 0.14 * t, FRENTE - 0.17 + 0.02 * t, Z0 + 0.035 - 0.01 * t))
    mira = Vector((X0 - 0.02 + 0.04 * t, FRENTE, Z0 + 0.005)); dp, dq = pulso(f, 0.25)
    camino[f] = (pos + dp, mira, 55, 4.0, (mira - pos).length, dq)
# 4. botones: lateral derecho, acercamiento lento
b0, b1 = P['botones']
for f in range(b0, b1 + 1):
    t = suave((f - b0) / (b1 - b0)); pos = Vector((X0 + 0.27 - 0.04 * t, FRENTE - 0.07 + 0.01 * t, Z0 + 0.03))
    mira = Vector((X0 + 0.115, PARED_Y - D_ * 0.5, Z0)); dp, dq = pulso(f, 0.25)
    camino[f] = (pos + dp, mira, 50, 5.6, (Vector((X0 + W_ / 2, PARED_Y - D_ / 2, Z0)) - pos).length, dq)
# 5. apagado: plano medio de frente que se aleja despacio
a0_, a1_ = P['apagado']
for f in range(a0_, a1_ + 1):
    t = suave((f - a0_) / (a1_ - a0_)); pos = Vector((X0 + 0.03, FRENTE - 0.40 - 0.12 * t, Z0 + 0.03)); mira = DISP + Vector((0, 0, -0.01))
    dp, dq = pulso(f, 0.3); camino[f] = (pos + dp, mira, 40, 2.8, (mira - pos).length, dq)
# 6. adhesivo: tres cuartos desde la izquierda para ver la separación con la pared
d0_, d1_ = P['adhesivo']
for f in range(d0_, d1_ + 1):
    t = suave((f - d0_) / (d1_ - d0_)); pos = Vector((X0 - 0.30 + 0.04 * t, PARED_Y - 0.40, Z0 + 0.06)); mira = Vector((X0, PARED_Y - 0.08, Z0))
    dp, dq = pulso(f, 0.3); camino[f] = (pos + dp, mira, 40, 3.2, (mira - pos).length, dq)
# 7. USB-C: primer plano del lateral derecho
u0_, u1_ = P['usb']
for f in range(u0_, u1_ + 1):
    t = suave((f - u0_) / (u1_ - u0_)); pos = Vector((X0 + 0.22 - 0.02 * t, PARED_Y - 0.17, Z0 + 0.025))
    mira = Vector((X0 + W_ / 2, PARED_Y - D_ * 0.62, Z0 - 0.004)); dp, dq = pulso(f, 0.25)
    camino[f] = (pos + dp, mira, 55, 5.0, (mira - pos).length, dq)
# 8. dos versiones: de frente, acercamiento suave
v0_, v1_ = P['versiones']; cx = X0 + 0.15
for f in range(v0_, v1_ + 1):
    t = suave((f - v0_) / (v1_ - v0_)); pos = Vector((cx, PARED_Y - 1.0 + 0.10 * t, Z0 + 0.02)); mira = Vector((cx, FRENTE, Z0 - 0.01))
    dp, dq = pulso(f, 0.3); camino[f] = (pos + dp, mira, 26, 2.8, (mira - pos).length, dq)
fines = {b_ for _, _, b_ in PLANOS}
for f in range(1, TOTAL + 1):
    pos, mira, lente, fs, foco, giro = camino[f]; clave(f, pos, mira, lente, fs, foco, giro)
    if f in fines: clave(f, pos, mira, lente, fs, foco, giro, sub=0.6)     # el obturador no mezcla dos planos en el corte
for idb in (cam, cd):
    for fc in g['curvas'](idb):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ---------- render ----------
r = sc.render; r.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.cycles.blur_glossy = 0.3; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.motion_blur_position = 'START'; r.image_settings.file_format = 'PNG'
r.resolution_x = args.ancho; r.resolution_y = round(args.ancho * 16 / 9); sc.view_settings.view_transform = 'AgX'
sc.cycles.samples = args.muestras; sc.cycles.max_bounces = 10; sc.cycles.diffuse_bounces = 6
sc.cycles.adaptive_threshold = 0.01; sc.frame_end = TOTAL
sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0.6
LISTA = [int(x) for x in args.lista.split(',')] if args.lista else range(args.desde, args.hasta + 1)
import time
for f in LISTA:
    sc.frame_set(f); r.filepath = os.path.join(args.salida, f'f{f:04d}.png')
    t0 = time.time(); bpy.ops.render.render(write_still=True); print(f'fotograma {f}: {time.time() - t0:.1f} s', flush=True)
