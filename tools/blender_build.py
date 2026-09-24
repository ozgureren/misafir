"""Build tki_misafirhane_exterior.blend / .glb from model.json (Blender 5.0 bpy module)."""
import bpy, bmesh, json, math, sys, os
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon

SCR = os.path.dirname(os.path.abspath(__file__))
OUTDIR = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else SCR
M = json.load(open(os.path.join(os.environ.get('TKI_WORK', '.'), 'model.json')))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 1.0; sc.unit_settings.length_unit = 'METERS'

# ------------------------------------------------------------ collections
ROOT = bpy.data.collections.new('TKI_MISAFIRHANE_EXTERIOR'); sc.collection.children.link(ROOT)
COLL = {}
for n in ['BUILDING_SHELL', 'EXTERIOR_WALLS', 'WINDOWS', 'WINDOW_GLASS', 'EXTERIOR_DOORS', 'ROOF', 'PARAPETS', 'BALCONIES',
          'RAILINGS', 'ENTRANCE', 'EXTERIOR_STAIRS', 'RAMPS', 'CANOPIES', 'COLUMNS']:
    c = bpy.data.collections.new(n); ROOT.children.link(c); COLL[n] = c

# ------------------------------------------------------------ materials (neutral where the drawing gives no colour)
# textured PBR materials (textures from tools/make_textures.py, colours matched to the site photos)
TEXDIR = os.path.join(OUTDIR, 'textures')
#  key: (texture or None, tile_m, base colour/tint, metallic, roughness, normal strength, alpha, description)
MATS = {
    'PLASTER_A':  ('plaster_a', 3.0, (1, 1, 1, 1), 0.0, 0.88, 0.6, 1, 'Silikon esasli dis cephe sivasi - krem, granullu, yatay derzli (fotograf)'),
    'TRAVERTINE': ('travertine', 2.4, (1, 1, 1, 1), 0.0, 0.62, 0.4, 1, 'Traverten kaplama - krem (DWG + fotograf)'),
    'ASHLAR':     ('ashlar', 1.6, (1, 1, 1, 1), 0.0, 0.85, 0.9, 1, 'Tas kaplama subasman - bej kesme tas (fotograf)'),
    'RED_MARBLE': ('red_marble', 1.5, (1, 1, 1, 1), 0.0, 0.22, 0.2, 1, 'Harpustali tas kaplama alinli / giris portali - kirmizi damarli mermer (fotograf)'),
    'COPING_A':   ('ochre', 1.5, (0.95, 0.88, 0.70, 1), 0.2, 0.5, 0.2, 1, 'A blok parapet harpustasi - hardal/oker (fotograf)'),
    'OCHRE':      ('ochre', 3.0, (1, 1, 1, 1), 0.0, 0.85, 0.3, 1, 'Pergola arkasi cephe sivasi - hardal sari (fotograf)'),
    'GRANITE':    ('granite', 2.4, (1, 1, 1, 1), 0.0, 0.55, 0.5, 1, 'Teras kaplamasi - acik gri granit plak (fotograf)'),
    'ROOF_METAL': ('metal_roof', 2.0, (1, 1, 1, 1), 0.6, 0.45, 0.8, 1, 'Renkli metal yaprak cati ortusu (renk fotograflarda gorunmuyor - notr gri)'),
    'ROOF_FLAT':  ('roof_flat', 2.0, (1, 1, 1, 1), 0.0, 0.95, 0.6, 1, 'Duz cati (notr)'),
    'CONCRETE':   ('concrete', 2.4, (1, 1, 1, 1), 0.0, 0.90, 0.4, 1, 'Betonarme (notr)'),
    'RED_ALU':    (None, 1, (0.56, 0.04, 0.07, 1), 0.35, 0.35, 0, 1, 'Renkli eloksal aluminyum dograma - kirmizi (fotograf)'),
    'FRAME_DARK': (None, 1, (0.10, 0.11, 0.13, 1), 0.7, 0.35, 0, 1, 'Giydirme cephe kayitlari - koyu'),
    'RED_PAINT':  (None, 1, (0.62, 0.05, 0.06, 1), 0.3, 0.40, 0, 1, 'Atrium cati alni - kirmizi (fotograf)'),
    'GLASS':      (None, 1, (0.03, 0.04, 0.05, 0.45), 0.0, 0.04, 0, 0.45, 'Isicam'),
    'BLUE_GLASS': (None, 1, (0.03, 0.08, 0.22, 0.9), 0.2, 0.05, 0, 0.9, 'Egik giydirme cephe - koyu mavi reflektif cam (fotograf)'),
    'CURTAIN':    ('curtain', 1.2, (1, 1, 1, 1), 0.0, 0.9, 0.3, 1, 'Pencere arkasi perde (fotograf; ic mekan degil, sadece cam arkasi panel)'),
    'STAINLESS':  (None, 1, (0.80, 0.80, 0.82, 1), 0.9, 0.35, 0, 1, 'Paslanmaz/aluminyum boru korkuluk h:90 (DWG notu + fotograf)'),
    'SIGN':       (None, 1, (0.97, 0.97, 0.97, 1), 0.3, 0.3, 0, 1, 'TKI MISAFIRHANE yazisi (fotograf)'),
    'SOVE':       ('travertine', 2.4, (0.93, 0.91, 0.86, 1), 0.0, 0.6, 0.3, 1, 'Pencere sovesi / denizlik - traverten (DWG + fotograf)'),
}
TILE = {k: v[1] for k, v in MATS.items()}
MAT = {}
def _img(name, noncolor=False):
    p = os.path.join(TEXDIR, name)
    im = bpy.data.images.load(p, check_existing=True)
    if noncolor: im.colorspace_settings.name = 'Non-Color'
    return im
for k, (tex, tile, col, met, rough, nstr, alpha, desc) in MATS.items():
    m = bpy.data.materials.new(k); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    b.inputs['Metallic'].default_value = met; b.inputs['Roughness'].default_value = rough
    if tex:
        tc = nt.nodes.new('ShaderNodeTexImage'); tc.image = _img(f'{tex}_col.jpg'); tc.location = (-600, 200)
        if col[:3] != (1, 1, 1):
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0; mix.inputs[7].default_value = col
            nt.links.new(tc.outputs['Color'], mix.inputs[6]); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
        else:
            nt.links.new(tc.outputs['Color'], b.inputs['Base Color'])
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = _img(f'{tex}_nrm.png', True); tn.location = (-600, -200)
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstr; nm.location = (-300, -200)
        nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    else:
        b.inputs['Base Color'].default_value = col
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    m.diffuse_color = col
    m['dwg_description'] = desc
    MAT[k] = m
# legacy keys still present in model data
for old, new in (('PLASTER', 'PLASTER_A'), ('STONE_TRAVERTINE', 'TRAVERTINE'), ('STONE_CLADDING', 'ASHLAR'), ('STONE_COPING', 'RED_MARBLE'),
                 ('FRAME_ALU', 'RED_ALU'), ('ROOF_MEMBRANE', 'ROOF_FLAT')):
    MAT[old] = MAT[new]; TILE[old] = TILE[new]

def world_uv(me, tile, M_=None):
    """box-like projection in metres: vertical faces u along the wall, v = z; sloped faces u along contour, v up-slope"""
    if not me.polygons: return
    uvl = me.uv_layers.new(name='UVMap') if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        n = poly.normal
        if abs(n.z) > 0.999: t = Vector((1, 0, 0)); bvec = Vector((0, 1, 0))
        else:
            t = Vector((0, 0, 1)).cross(n).normalized(); bvec = n.cross(t).normalized()
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (p.dot(t) / tile, p.dot(bvec) / tile)

def new_obj(name, me, coll, mat=None):
    ob = bpy.data.objects.new(name, me); COLL[coll].objects.link(ob)
    if mat and not me.materials: me.materials.append(MAT[mat])
    if mat: ob['material_key'] = mat
    return ob

def prism_mesh(name, rings, z0, z1):
    bm = bmesh.new()
    loops = []
    for r in rings:
        # ensure outer CCW, holes CW
        loops.append([Vector((x, y, 0)) for x, y in r])
    def area(l): return sum(l[i].x * l[(i + 1) % len(l)].y - l[(i + 1) % len(l)].x * l[i].y for i in range(len(l))) / 2
    if area(loops[0]) < 0: loops[0].reverse()
    for i in range(1, len(loops)):
        if area(loops[i]) > 0: loops[i].reverse()
    tris = tessellate_polygon([[v for v in l] for l in loops])
    flat = [v for l in loops for v in l]
    bot = [bm.verts.new((v.x, v.y, z0)) for v in flat]
    top = [bm.verts.new((v.x, v.y, z1)) for v in flat]
    for t in tris:
        try:
            bm.faces.new([top[t[0]], top[t[1]], top[t[2]]]) if True else None
        except ValueError: pass
        try: bm.faces.new([bot[t[2]], bot[t[1]], bot[t[0]]])
        except ValueError: pass
    off = 0
    for l in loops:
        n = len(l)
        for i in range(n):
            a, b_ = off + i, off + (i + 1) % n
            try: bm.faces.new([bot[a], bot[b_], top[b_], top[a]])
            except ValueError: pass
        off += n
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # merge coplanar cap triangles back into n-gons (cleaner, lower poly)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts, edges=bm.edges, delimit={'NORMAL'})
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me

# ------------------------------------------------------------ prisms (banded walls are joined into one object per wall)
import collections
GROUPS = collections.OrderedDict()
for p in M['prisms']:
    GROUPS.setdefault(p.get('group') or p['name'], []).append(p)
PR = {}
for gname, plist in GROUPS.items():
    bm_all = bmesh.new()
    for p in plist:
        me_t = prism_mesh('_tmp', p['rings'], p['z0'], p['z1'])
        bm_all.from_mesh(me_t); bpy.data.meshes.remove(me_t)
    bmesh.ops.remove_doubles(bm_all, verts=bm_all.verts, dist=0.001)
    # drop internal horizontal faces between stacked bands (both sides solid => duplicate coplanar faces)
    seen = {}
    dup = []
    for f in bm_all.faces:
        k = tuple(sorted(v.index for v in f.verts))
        if k in seen: dup += [f, seen[k]]
        else: seen[k] = f
    if dup: bmesh.ops.delete(bm_all, geom=list(set(dup)), context='FACES')
    me = bpy.data.meshes.new(gname); bm_all.to_mesh(me); bm_all.free()
    p = plist[0]
    ob = new_obj(gname, me, p['coll'], p['mat'])
    ob['dwg_z_range'] = f"{min(q['z0'] for q in plist):+.2f}..{max(q['z1'] for q in plist):+.2f}"
    PR[gname] = (ob, None)

# ------------------------------------------------------------ free meshes (roof planes, curtain wall ...)
for m in M['meshes']:
    me = bpy.data.meshes.new(m['name'])
    me.from_pydata([tuple(v) for v in m['verts']], [], m['faces']); me.update()
    ob = new_obj(m['name'], me, m['coll'], m['mat'])
    if m.get('thick', 0) > 0:
        # roof faces were emitted at top-of-covering height; thicken downward
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            if f.normal.z < 0: f.normal_flip()
        bm.to_mesh(me); bm.free()
        mod = ob.modifiers.new('thick', 'SOLIDIFY'); mod.thickness = m['thick']; mod.offset = -1.0
        bpy.context.view_layer.objects.active = ob
        with bpy.context.temp_override(object=ob): bpy.ops.object.modifier_apply(modifier=mod.name)

# ------------------------------------------------------------ openings are already cut (2D banding in build_data2.py)
def frame_basis(o):
    p0 = Vector((*o['p0'], 0)); p1 = Vector((*o['p1'], 0)); n = Vector((*o['n'], 0)).normalized()
    ax = (p1 - p0); w = ax.length; ax.normalize()
    return p0, p1, ax, -n, n, w

# ------------------------------------------------------------ window / door instances
def box(bm, x0, x1, y0, y1, z0, z1):
    v = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                     (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])
FR_W, FR_D, FR_Y = 0.06, 0.07, 0.08      # frame face width, depth, set-back from outer wall face (few-cm realistic profile)
CACHE = {}
def unit_meshes(kind, w, h, surround, curtain=False):
    key = (kind, round(w, 2), round(h, 2), surround, curtain)
    if key in CACHE: return CACHE[key]
    fb = bmesh.new()
    y0, y1 = FR_Y, FR_Y + FR_D
    box(fb, 0, w, y0, y1, 0, FR_W); box(fb, 0, w, y0, y1, h - FR_W, h)
    box(fb, 0, FR_W, y0, y1, FR_W, h - FR_W); box(fb, w - FR_W, w, y0, y1, FR_W, h - FR_W)
    if kind == 'DOOR':
        box(fb, FR_W, w - FR_W, y0 + 0.01, y1 - 0.01, 0.95, 1.05)            # door mid-rail
        if w > 1.3: box(fb, w / 2 - 0.03, w / 2 + 0.03, y0, y1, FR_W, h - FR_W)  # meeting stile (double leaf)
    elif w > 0.85:
        nm = max(1, int(w // 1.2))                                            # photos: two-sash windows, central mullion
        for i in range(1, nm + 1):
            x = w * i / (nm + 1); box(fb, x - 0.03, x + 0.03, y0 + 0.005, y1 - 0.005, FR_W, h - FR_W)
    # travertine sill ("Traverten denizlik") and "Sove" surround only where the drawings show them (windows)
    sb = None
    if kind == 'WIN':
        sb = bmesh.new()
        box(sb, -0.05, w + 0.05, -0.04, FR_Y, -0.03, 0.0)
        if surround:
            s = 0.10
            box(sb, -s, w + s, -0.03, 0.0, h, h + s); box(sb, -s, 0, -0.03, 0.0, 0, h); box(sb, w, w + s, -0.03, 0.0, 0, h)
    gb = bmesh.new()
    gy = FR_Y + FR_D / 2
    gv = [gb.verts.new(p) for p in ((FR_W, gy, FR_W), (w - FR_W, gy, FR_W), (w - FR_W, gy, h - FR_W), (FR_W, gy, h - FR_W))]
    gb.faces.new(gv)
    cb = None
    if curtain:                                                               # curtain panel just behind the glass (no interior modelled)
        cb = bmesh.new(); cy = y1 + 0.12
        cv = [cb.verts.new(p) for p in ((FR_W, cy, FR_W), (w - FR_W, cy, FR_W), (w - FR_W, cy, h - FR_W), (FR_W, cy, h - FR_W))]
        cb.faces.new(cv[::-1])
    tag = f'{kind}_{int(round(w*100))}x{int(round(h*100))}{"_S" if surround else ""}{"_C" if curtain else ""}'
    fm = bpy.data.meshes.new(f'{tag}_FRAME'); fb.to_mesh(fm); fb.free(); fm.materials.append(MAT['RED_ALU'])
    gm = bpy.data.meshes.new(f'{tag}_GLASS'); gb.to_mesh(gm); gb.free(); gm.materials.append(MAT['GLASS'])
    sm = None
    if sb is not None:
        sm = bpy.data.meshes.new(f'{tag}_SILL'); sb.to_mesh(sm); sb.free(); sm.materials.append(MAT['SOVE'])
    km = None
    if cb is not None:
        km = bpy.data.meshes.new(f'{tag}_CURTAIN'); cb.to_mesh(km); cb.free(); km.materials.append(MAT['CURTAIN'])
    CACHE[key] = (fm, gm, sm, km, tag)
    return CACHE[key]

def place(ob, o):
    p0, p1, ax, inward, n, w = frame_basis(o)
    up = Vector((0, 0, 1))
    R = Matrix(((ax.x, inward.x, 0), (ax.y, inward.y, 0), (0, 0, 1))).to_4x4()
    ob.matrix_world = Matrix.Translation((p0.x, p0.y, o['z0'])) @ R

counts = {'WIN': 0, 'DOOR': 0}
for kind, lst in (('WIN', M['windows']), ('DOOR', M['doors'])):
    for i, o in enumerate(lst):
        w = math.dist(o['p0'], o['p1']); h = o['z1'] - o['z0']
        surround = kind == 'WIN' and o['ring'] in ('A_tip', 'A_zem', 'B_zem') and w < 3.0
        curtain = kind == 'WIN' and o['ring'] in ('A_tip', 'A_zem') and o['z0'] > 0.5     # hotel rooms
        fm, gm, sm, km, tag = unit_meshes(kind, w, h, surround, curtain)
        base = f'{"WINDOW" if kind=="WIN" else "DOOR"}_{i:03d}'
        coll_f = 'WINDOWS' if kind == 'WIN' else ('ENTRANCE' if o.get('entrance') else 'EXTERIOR_DOORS')
        coll_g = 'WINDOW_GLASS' if kind == 'WIN' else coll_f
        for suffix, me, coll in (('FRAME', fm, coll_f), ('GLASS', gm, coll_g), ('SILL', sm, coll_f), ('CURTAIN', km, coll_g)):
            if me is None: continue
            ob = bpy.data.objects.new(f'{base}_{suffix}', me); COLL[coll].objects.link(ob); place(ob, o)
            ob['type'] = tag; ob['source'] = o['src'] + (f":{o['elev']}" if o.get('elev') else '')
        counts[kind] += 1

# ------------------------------------------------------------ entrance sign (photo: "TKI MISAFIRHANE" on the red marble portal)
if M.get('sign'):
    sg = M['sign']
    cu = bpy.data.curves.new('SIGN_TEXT', 'FONT'); cu.body = sg['text'].replace('\\n', '\n')
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.size = sg['height']; cu.extrude = 0.01; cu.space_line = 1.1
    tob = bpy.data.objects.new('ENTRANCE_SIGN_tmp', cu); COLL['ENTRANCE'].objects.link(tob)
    nx, ny = sg['normal']; ang = math.atan2(nx, -ny)
    tob.matrix_world = Matrix.Translation(Vector(sg['center'])) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'X')
    dg = bpy.context.evaluated_depsgraph_get()
    sme = bpy.data.meshes.new_from_object(tob.evaluated_get(dg))
    sob = bpy.data.objects.new('ENTRANCE_SIGN', sme); COLL['ENTRANCE'].objects.link(sob); sob.matrix_world = tob.matrix_world.copy()
    sme.materials.append(MAT['SIGN'])
    bpy.data.objects.remove(tob); bpy.data.curves.remove(cu)

# ------------------------------------------------------------ UVs in real-world metres for every textured mesh
MATNAME2KEY = {m.name: k for k, m in MAT.items()}
done = set()
for ob in list(bpy.data.objects):
    if ob.type != 'MESH' or ob.data.name in done or not ob.data.materials: continue
    key = MATNAME2KEY.get(ob.data.materials[0].name)
    if key and MATS.get(key, (None,))[0]:
        world_uv(ob.data, TILE[key]); done.add(ob.data.name)

# ------------------------------------------------------------ georeference / metadata
root = bpy.data.objects.new('TKI_MISAFIRHANE_ORIGIN', None); ROOT.objects.link(root)
root.empty_display_type = 'ARROWS'; root.empty_display_size = 5
root['origin_def'] = 'Local origin = intersection of grid axis 8 and axis A (A block / B-C block common axes). Z=0 = +-0.00 level.'
root['dwg_transform'] = ('B/C plans (Zemin Kat Plani frame): local_m = (DWG_cm - (486527, 39614)) / 100 ; '
                         'A plans: local_m = R(+45deg) * (DWG_cm - axis8xA_of_that_plan) / 100 ; see dwg_transform.json')
root['units'] = 'metres (DWG in centimetres)'
for k, v in M['stats'].items():
    if not isinstance(v, dict): root[f'stat_{k}'] = v

# remove empty helper collections? keep BALCONIES/RAILINGS/RAMPS for naming consistency (empty = not present in DWG)
os.makedirs(OUTDIR, exist_ok=True)
blend = os.path.join(OUTDIR, 'tki_misafirhane_exterior.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
glb = os.path.join(OUTDIR, 'tki_misafirhane_exterior.glb')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_yup=True, export_image_format='JPEG', export_image_quality=88)
fbx = os.path.join(OUTDIR, 'tki_misafirhane_exterior.fbx')
bpy.ops.export_scene.fbx(filepath=fbx, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS', use_mesh_modifiers=True, path_mode='RELATIVE')
tri = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        tri += sum(len(p.vertices) - 2 for p in ob.data.polygons)
print('DONE', counts, 'objects', len(bpy.data.objects), 'meshes', len(bpy.data.meshes), 'triangles~', tri)
