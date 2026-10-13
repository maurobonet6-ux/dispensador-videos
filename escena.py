# Teaser 3D realista del dispensador automático de jabón en espuma (3 s, 9:16). Blender como librería (pip install bpy), Cycles CPU.
# Plano: baño real (pared lisa beige, espejo de madera, lavabo y grifo desenfocados, suculenta). Luz de estudio de producto.
# 1-25: la cámara se acerca; 26: la pantalla LED se enciende (sensor de presencia); 44-90: sale la espuma (miles de burbujas).
# Uso: python3.11 escena.py --salida DIR [--ancho 1080] [--muestras 256] [--lista 1,30,80] [--desde 1 --hasta 90] [--color negro|blanco]
import bpy, bmesh, math, os, argparse, time, random
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__)); REC = os.path.join(AQUI, 'recursos')
a = argparse.ArgumentParser()
a.add_argument('--salida', required=True); a.add_argument('--ancho', type=int, default=1080); a.add_argument('--muestras', type=int, default=256)
a.add_argument('--desde', type=int, default=1); a.add_argument('--hasta', type=int, default=90); a.add_argument('--lista', default='')
a.add_argument('--color', default='negro')
args = a.parse_args(); os.makedirs(args.salida, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, 90
LED_ON, ESPUMA = 26, (44, 90)
rnd = random.Random(7)

# ---------- utilidades ----------
def estadio(w, h, n=48):
    """Contorno de cápsula (estadio) en el plano XZ, centrado, en sentido antihorario."""
    r = h / 2; c = w / 2 - r; pts = []
    for i in range(n + 1):
        t = -math.pi / 2 + math.pi * i / n; pts.append((c + r * math.cos(t), r * math.sin(t)))
    for i in range(n + 1):
        t = math.pi / 2 + math.pi * i / n; pts.append((-c + r * math.cos(t), r * math.sin(t)))
    return pts

def objeto(nombre, bm):
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nombre, me); sc.collection.objects.link(ob); return ob

def losa(nombre, w, h, y0, y1, bisel_atras=0.0, bisel_delante=0.0, seg=12):
    """Cápsula extruida de y0 (atrás) a y1 (delante, y1 < y0), con biseles redondeados y UV de frente."""
    bm = bmesh.new()
    atras = [bm.verts.new((x, y0, z)) for x, z in estadio(w, h)]
    delante = [bm.verts.new((x, y1, z)) for x, z in estadio(w, h)]
    n = len(atras)
    bm.faces.new(atras); bm.faces.new(list(reversed(delante)))
    for i in range(n): bm.faces.new((atras[i], atras[(i + 1) % n], delante[(i + 1) % n], delante[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.edges.ensure_lookup_table()
    for vs, b in ((atras, bisel_atras), (delante, bisel_delante)):
        if b <= 0: continue
        s = set(vs); bmesh.ops.bevel(bm, geom=[e for e in bm.edges if e.verts[0] in s and e.verts[1] in s], offset=b, segments=seg, profile=0.5, affect='EDGES')
    lay = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for l in f.loops: l[lay].uv = ((l.vert.co.x + w / 2) / w, (l.vert.co.z + h / 2) / h)
    ob = objeto(nombre, bm)
    for p in ob.data.polygons: p.use_smooth = True
    ob.modifiers.new('n', 'WEIGHTED_NORMAL').keep_sharp = True
    return ob

def anillo(nombre, w_ext, h_ext, w_int, h_int, y0, y1, bisel=0.0005):
    """Marco macizo: anillo de cápsula entre dos contornos, extruido de y0 a y1, con aristas redondeadas."""
    bm = bmesh.new(); ext, inte = estadio(w_ext, h_ext), estadio(w_int, h_int); n = len(ext)
    capas = [[bm.verts.new((x, y, z)) for x, z in pts] for y in (y0, y1) for pts in (ext, inte)]
    eA, iA, eD, iD = capas
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((eD[i], eD[j], iD[j], iD[i])); bm.faces.new((eA[i], iA[i], iA[j], eA[j]))
        bm.faces.new((eA[i], eA[j], eD[j], eD[i])); bm.faces.new((iA[i], iD[i], iD[j], iA[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bisel, segments=3, profile=0.5, affect='EDGES', clamp_overlap=True)
    ob = objeto(nombre, bm)
    for p in ob.data.polygons: p.use_smooth = True
    ob.modifiers.new('n', 'WEIGHTED_NORMAL').keep_sharp = True
    return ob

def principled(nombre, base=(0.8, 0.8, 0.8), metal=0.0, rug=0.4, coat=0.0, coat_rug=0.05, **extra):
    m = bpy.data.materials.new(nombre); p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*base, 1); p.inputs['Metallic'].default_value = metal; p.inputs['Roughness'].default_value = rug
    p.inputs['Coat Weight'].default_value = coat; p.inputs['Coat Roughness'].default_value = coat_rug
    for k, v in extra.items(): p.inputs[k].default_value = v
    return m

def micro(m, escala=900, fuerza=0.04, rug=None):
    """Micro-textura (piel del plástico o del metal) y, si se da, variación suave de rugosidad (huellas casi invisibles)."""
    N, L = m.node_tree.nodes, m.node_tree.links; p = N['Principled BSDF']; co = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = escala; nz.inputs['Detail'].default_value = 8
    L.new(co.outputs['Object'], nz.inputs['Vector'])
    bu = N.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = fuerza; bu.inputs['Distance'].default_value = 0.0002
    L.new(nz.outputs['Fac'], bu.inputs['Height']); L.new(bu.outputs['Normal'], p.inputs['Normal'])
    if rug:
        hu = N.new('ShaderNodeTexNoise'); hu.inputs['Scale'].default_value = 40; hu.inputs['Detail'].default_value = 3
        L.new(co.outputs['Object'], hu.inputs['Vector'])
        mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rug[0]; mr.inputs['To Max'].default_value = rug[1]
        L.new(hu.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs['Result'], p.inputs['Roughness'])
    return m

def tex_pbr(m, nombre, escala, tinte=None, sat=None, valor=None, normal=0.6, coords='UV'):
    """Textura de Poly Haven (diff, nor_gl, rough) en un material; con tinte multiplicado y saturación ajustable."""
    N, L = m.node_tree.nodes, m.node_tree.links; p = N['Principled BSDF']; co = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (escala,) * 3; L.new(co.outputs[coords], mp.inputs['Vector'])
    def t(mapa, color=True):
        n = N.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(REC, f'{nombre}_{mapa}_2k.jpg'))
        if not color: n.image.colorspace_settings.name = 'Non-Color'
        L.new(mp.outputs['Vector'], n.inputs['Vector']); return n
    col = t('diff').outputs['Color']
    if sat is not None or valor is not None:
        hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 1 if sat is None else sat
        hs.inputs['Value'].default_value = 1 if valor is None else valor; L.new(col, hs.inputs['Color']); col = hs.outputs['Color']
    if tinte:
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
        L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (*tinte, 1); col = mx.outputs[2]
    L.new(col, p.inputs['Base Color'])
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal; L.new(t('nor_gl', False).outputs['Color'], nm.inputs['Color'])
    L.new(nm.outputs['Normal'], p.inputs['Normal']); L.new(t('rough', False).outputs['Color'], p.inputs['Roughness'])
    return m

def curvas(idb):
    act = idb.animation_data.action
    try: return list(act.fcurves)
    except AttributeError: return [fc for l in act.layers for s_ in l.strips for cb in s_.channelbags for fc in cb.fcurves]

def caja(nombre, tam, loc, material, bisel=0.004):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * tam[0], v.co.y * tam[1], v.co.z * tam[2]))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bisel, segments=4, profile=0.5, affect='EDGES')
    ob = objeto(nombre, bm); ob.location = loc; ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def cilindro(nombre, r, h, loc, material, rot=(0, 0, 0), r2=None, seg=48):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    ob = objeto(nombre, bm); ob.location = loc; ob.rotation_euler = rot; ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth = True
    return ob

# ---------- dispensador (medidas de las fotos: frontal 24 x 13 cm, fondo 9 cm) ----------
W, H, D = 0.24, 0.13, 0.088
GW, GH = W - 0.012, H - 0.012                    # frontal (cristal + marco)
NEGRO = args.color == 'negro'
plast = micro(principled('Plastico', (0.006, 0.006, 0.007) if NEGRO else (0.80, 0.80, 0.78), rug=0.32, coat=0.25, coat_rug=0.15,
                         **{'Specular IOR Level': 0.5}), escala=1400, fuerza=0.03, rug=(0.16, 0.26))
cuerpo = losa('Cuerpo', W, H, 0.0, -D, bisel_atras=0.032, bisel_delante=0.006, seg=16)
cuerpo.data.materials.append(plast)
# junta oscura entre carcasa y frontal
junta = anillo('Junta', GW + 0.003, GH + 0.003, GW - 0.004, GH - 0.004, -D + 0.0005, -D - 0.0012, bisel=0.0002)
junta.data.materials.append(principled('JuntaM', (0.004, 0.004, 0.004), rug=0.6))
# pantalla (negra con el LED) detrás de un cristal de verdad (transmisión, reflejo y algo de tinte)
pant = losa('Pantalla', GW - 0.004, GH - 0.004, -D - 0.0010, -D - 0.0016)
mp_ = principled('PantallaM', (0.002, 0.002, 0.0025), rug=0.35); N, L = mp_.node_tree.nodes, mp_.node_tree.links
led = N.new('ShaderNodeTexImage'); led.image = bpy.data.images.load(os.path.join(REC, 'led.png'))
on = N.new('ShaderNodeValue')
for f, v in ((1, 0), (LED_ON, 0), (LED_ON + 1, 1.4), (LED_ON + 2, 0.3), (LED_ON + 4, 2.0)):
    on.outputs[0].default_value = v; on.outputs[0].keyframe_insert('default_value', frame=f)
for fc in curvas(mp_.node_tree):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
p_ = N['Principled BSDF']; L.new(led.outputs['Color'], p_.inputs['Emission Color']); L.new(on.outputs[0], p_.inputs['Emission Strength'])
pant.data.materials.append(mp_)
cristal = losa('Cristal', GW - 0.002, GH - 0.002, -D - 0.0018, -D - 0.0048, bisel_delante=0.0008, seg=4)
cristal.data.materials.append(principled('CristalM', (0.55, 0.55, 0.58), rug=0.0, **{'Transmission Weight': 1.0, 'IOR': 1.52}))
# marco de oro rosa macizo (pulido, con un leve cepillado)
oro = micro(principled('OroRosa', (0.80, 0.40, 0.26), metal=1.0, rug=0.12, **{'Anisotropic': 0.35}), escala=3000, fuerza=0.02, rug=(0.10, 0.16))
marco = anillo('Marco', GW + 0.002, GH + 0.002, GW - 0.002, GH - 0.002, -D - 0.0008, -D - 0.0056, bisel=0.0007)
marco.data.materials.append(oro)
# sensor (lente pequeña), boquilla con su agujero, tapa de recarga arriba y botones del lateral
lente = principled('Lente', (0.01, 0.01, 0.012), rug=0.04, coat=1.0)
cilindro('Sensor', 0.0040, 0.0004, (0, -D - 0.0017, -0.040), lente, rot=(math.radians(90), 0, 0))   # detrás del cristal
BOQ = Vector((0, -D + 0.018, -H / 2 + 0.003))
cilindro('Boquilla', 0.0034, 0.010, BOQ - Vector((0, 0, 0.004)), oro, r2=0.0038)
cilindro('Agujero', 0.0019, 0.0004, BOQ - Vector((0, 0, 0.0091)), principled('Hueco', (0.0, 0.0, 0.0), rug=0.9))
tapa = cilindro('Tapa', 0.017, 0.003, (0, -D / 2 + 0.006, H / 2 - 0.0005), principled('TapaM', (0.006, 0.006, 0.007), rug=0.3, coat=0.6), r2=0.0165)
tapa.scale = (1.7, 0.85, 1)
for z in (0.013, -0.013): cilindro('Boton', 0.0055, 0.003, (W / 2 - 0.0035, -D / 2 - 0.004, z), plast, rot=(0, math.radians(90), 0), r2=0.005)

# ---------- espuma: cuerpo blando + miles de burbujas que asoman en la superficie ----------
mb = bpy.data.metaballs.new('EspumaMB'); mb.resolution = 0.0008; mb.render_resolution = 0.0008; mb.threshold = 0.5
ESF = [((0, 0, -0.004), 0.0062), ((0, 0, -0.012), 0.011), ((0, 0, -0.026), 0.019), ((0, 0, -0.040), 0.017)]   # gota cremosa
for _ in range(6):                # pocos lóbulos grandes y muy solapados: contorno blando, no de palomita
    a_ = rnd.uniform(0, 2 * math.pi); z_ = rnd.uniform(-0.040, -0.020)
    ESF.append(((0.008 * math.cos(a_), 0.007 * math.sin(a_), z_), rnd.uniform(0.014, 0.017)))
for co_, r_ in ESF:
    e = mb.elements.new(); e.co = co_; e.radius = r_
tmp = bpy.data.objects.new('tmp', mb); sc.collection.objects.link(tmp)
dg = bpy.context.evaluated_depsgraph_get(); me_esp = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg)); bpy.data.objects.remove(tmp)
espuma = bpy.data.objects.new('Espuma', me_esp); sc.collection.objects.link(espuma); espuma.location = BOQ - Vector((0, 0, 0.0085))
for p in me_esp.polygons: p.use_smooth = True
m_esp = principled('Espuma', (0.86, 0.86, 0.84), rug=0.55, **{'Subsurface Weight': 0.45, 'Subsurface Scale': 0.002, 'Sheen Weight': 0.2})
N, L = m_esp.node_tree.nodes, m_esp.node_tree.links; co = N.new('ShaderNodeTexCoord')
vo = N.new('ShaderNodeTexVoronoi'); vo.feature = 'SMOOTH_F1'; vo.inputs['Scale'].default_value = 1500; L.new(co.outputs['Object'], vo.inputs['Vector'])
bu = N.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.8; bu.inputs['Distance'].default_value = 0.0005
L.new(vo.outputs['Distance'], bu.inputs['Height']); L.new(bu.outputs['Normal'], N['Principled BSDF'].inputs['Normal'])
me_esp.materials.append(m_esp)
m_burb = principled('Burbuja', (0.95, 0.95, 0.94), rug=0.12, **{'Transmission Weight': 0.25, 'IOR': 1.33, 'Subsurface Weight': 0.8, 'Subsurface Scale': 0.001})
# Geometry Nodes: puntos sobre la superficie → burbujas (esferas de 0,25 a 1,1 mm, medio hundidas)
ng = bpy.data.node_groups.new('Burbujas', 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
GN, GL = ng.nodes, ng.links
gi = GN.new('NodeGroupInput'); go = GN.new('NodeGroupOutput')
dist = GN.new('GeometryNodeDistributePointsOnFaces'); dist.inputs['Density'].default_value = 3.0e6
ico = GN.new('GeometryNodeMeshIcoSphere'); ico.inputs['Radius'].default_value = 1.0; ico.inputs['Subdivisions'].default_value = 2
rv = GN.new('FunctionNodeRandomValue'); rv.data_type = 'FLOAT'; rv.inputs[2].default_value = 0.00015; rv.inputs[3].default_value = 0.0007
inst = GN.new('GeometryNodeInstanceOnPoints')
smat = GN.new('GeometryNodeSetMaterial'); smat.inputs['Material'].default_value = m_burb
join = GN.new('GeometryNodeJoinGeometry')
GL.new(gi.outputs[0], dist.inputs['Mesh']); GL.new(dist.outputs['Points'], inst.inputs['Points']); GL.new(ico.outputs['Mesh'], inst.inputs['Instance'])
GL.new(rv.outputs[1], inst.inputs['Scale']); GL.new(inst.outputs['Instances'], smat.inputs['Geometry'])
# y unas pocas burbujas grandes sueltas (1-2,5 mm), brillantes: es lo que hace que la espuma parezca de verdad
dist2 = GN.new('GeometryNodeDistributePointsOnFaces'); dist2.inputs['Density'].default_value = 8e3; dist2.inputs['Seed'].default_value = 3
rv2 = GN.new('FunctionNodeRandomValue'); rv2.data_type = 'FLOAT'; rv2.inputs[2].default_value = 0.0007; rv2.inputs[3].default_value = 0.0016
inst2 = GN.new('GeometryNodeInstanceOnPoints'); GL.new(gi.outputs[0], dist2.inputs['Mesh']); GL.new(dist2.outputs['Points'], inst2.inputs['Points'])
GL.new(ico.outputs['Mesh'], inst2.inputs['Instance']); GL.new(rv2.outputs[1], inst2.inputs['Scale'])
smat2 = GN.new('GeometryNodeSetMaterial'); GL.new(inst2.outputs['Instances'], smat2.inputs['Geometry'])
GL.new(gi.outputs[0], join.inputs[0]); GL.new(smat.outputs[0], join.inputs[0]); GL.new(smat2.outputs[0], join.inputs[0]); GL.new(join.outputs[0], go.inputs[0])
me_esp.materials.append(m_burb)
m_gota = principled('BurbujaGrande', (0.95, 0.95, 0.94), rug=0.2, coat=1.0, coat_rug=0.02, **{'Subsurface Weight': 0.5, 'Subsurface Scale': 0.001}); me_esp.materials.append(m_gota)
smat2.inputs['Material'].default_value = m_gota
espuma.modifiers.new('Burbujas', 'NODES').node_group = ng
# sale de la boquilla: crece hacia abajo (origen en la boquilla), se ensancha y se asienta con un leve rebote
e0, e1 = ESPUMA
for f, s in ((e0, (0.35, 0.35, 0.02)), (e0 + 5, (0.45, 0.45, 0.22)), (e0 + 14, (0.75, 0.75, 0.62)), (e0 + 26, (0.97, 0.97, 1.03)),
             (e0 + 34, (1.0, 1.0, 0.98)), (e1, (1.02, 1.02, 1.0))):
    espuma.scale = s; espuma.keyframe_insert('scale', frame=f)
for f, v in ((1, True), (e0, False)):
    espuma.hide_render = v; espuma.keyframe_insert('hide_render', frame=f)

# ---------- baño: pared lisa beige, espejo redondo de madera, encimera blanca con lavabo, grifo y suculenta ----------
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0.0005, 0), rotation=(math.radians(90), 0, 0)); pared = bpy.context.object
pared.data.materials.append(tex_pbr(principled('Pared'), 'beige_wall_001', 2.0, tinte=(0.98, 0.92, 0.84), sat=0.5, normal=0.4, coords='Object'))
madera = principled('Madera', (0.55, 0.36, 0.20), rug=0.45, coat=0.2)
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, segments=96, radius=0.28)
espejo_aro = objeto('Aro', bm); espejo_aro.location = (-0.42, -0.012, 0.36); espejo_aro.rotation_euler = (math.radians(90), 0, 0)
espejo_aro.modifiers.new('s', 'SKIN')
for v in espejo_aro.data.skin_vertices[0].data: v.radius = (0.012, 0.012)
espejo_aro.modifiers.new('sub', 'SUBSURF').levels = 2; espejo_aro.data.materials.append(madera)
cilindro('Espejo', 0.275, 0.004, (-0.42, -0.008, 0.36), principled('EspejoM', (0.9, 0.9, 0.9), metal=1.0, rug=0.0), rot=(math.radians(90), 0, 0), seg=96)
ceram = principled('Ceramica', (0.92, 0.92, 0.91), rug=0.08, coat=0.6)
caja('Encimera', (0.9, 0.45, 0.04), (-0.12, -0.225, -0.30), ceram, bisel=0.008)
cromo = principled('Cromo', (0.92, 0.92, 0.94), metal=1.0, rug=0.06)
cilindro('GrifoBase', 0.022, 0.03, (-0.26, -0.06, -0.265), cromo)
cilindro('GrifoCuerpo', 0.014, 0.14, (-0.26, -0.06, -0.21), cromo)
cilindro('GrifoCano', 0.009, 0.09, (-0.26, -0.105, -0.15), cromo, rot=(math.radians(90), 0, 0))
cilindro('Maceta', 0.042, 0.06, (0.17, -0.10, -0.25), principled('MacetaM', (0.93, 0.93, 0.9), rug=0.5), r2=0.05)
try:
    bpy.ops.import_scene.gltf(filepath=os.path.join(REC, 'cheiridopsis_succulent', 'cheiridopsis_succulent.gltf'))
    for o in bpy.context.selected_objects:
        if o.parent is None: o.location = (0.17, -0.10, -0.226); o.scale = (0.16, 0.16, 0.16); o.rotation_euler = (math.radians(90), 0, 0.6)
except Exception as e_: print('suculenta no cargada:', e_)

# ---------- luz de estudio de producto ----------
def luz(nombre, loc, mira, potencia, tam, color=(1, 1, 1), tam_y=None, forma='RECTANGLE'):
    d = bpy.data.lights.new(nombre, 'AREA'); d.energy = potencia; d.shape = forma; d.size = tam; d.size_y = tam_y or tam; d.color = color
    o = bpy.data.objects.new(nombre, d); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(mira) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
luz('Clave', (-0.7, -0.9, 0.6), (0, -D, 0), 90, 1.0, (1.0, 0.97, 0.93), tam_y=0.7)          # ventana grande y suave arriba a la izquierda
luz('Tira', (0.55, -0.45, 0.05), (0, -D, 0), 28, 0.08, (1.0, 0.98, 0.96), tam_y=0.9)       # tira a la derecha: filo de luz en el marco
luz('Cenital', (0.0, -0.25, 0.7), (0, -D, 0), 25, 0.6, (1.0, 0.97, 0.94), tam_y=0.4)
w = bpy.data.worlds.new('Mundo'); sc.world = w; WN, WL = w.node_tree.nodes, w.node_tree.links
env = WN.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(REC, 'bathroom_2k.hdr'))
WL.new(env.outputs['Color'], WN['Background'].inputs['Color']); WN['Background'].inputs['Strength'].default_value = 0.35

# ---------- cámara: acercamiento lento de tres cuartos a casi frente (85 mm) ----------
cd = bpy.data.cameras.new('Cam'); cd.lens = 85; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 36
cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
mira = bpy.data.objects.new('Mira', None); sc.collection.objects.link(mira)
tr = cam.constraints.new('TRACK_TO'); tr.target = mira; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
for f, pos, m_ in ((1, (-0.55, -1.02, -0.02), (0.0, -D, -0.035)), (45, (-0.26, -1.12, -0.04), (0.0, -D, -0.045)),
                   (90, (0.05, -1.14, -0.05), (0.0, -D, -0.05))):
    cam.location = pos; cam.keyframe_insert('location', frame=f); mira.location = m_; mira.keyframe_insert('location', frame=f)
foco = bpy.data.objects.new('Foco', None); sc.collection.objects.link(foco); foco.location = (0, -D - 0.005, -0.01)
cd.dof.use_dof = True; cd.dof.focus_object = foco; cd.dof.aperture_fstop = 2.8; cd.dof.aperture_blades = 9

# ---------- render ----------
r = sc.render; r.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = args.muestras; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.008
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.cycles.max_bounces = 12; sc.cycles.transmission_bounces = 12; sc.cycles.blur_glossy = 0.2
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
r.resolution_x = args.ancho; r.resolution_y = round(args.ancho * 16 / 9); r.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -0.6
LISTA = [int(x) for x in args.lista.split(',')] if args.lista else range(args.desde, args.hasta + 1)
for f in LISTA:
    sc.frame_set(f); r.filepath = os.path.join(args.salida, f'f{f:04d}.png')
    t = time.time(); bpy.ops.render.render(write_still=True); print(f'fotograma {f}: {time.time() - t:.1f} s', flush=True)
