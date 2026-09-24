import bpy, math, sys, os
from mathutils import Vector
SCR = os.path.dirname(os.path.abspath(__file__))
blend = sys.argv[sys.argv.index('--blend') + 1]; outd = sys.argv[sys.argv.index('--qc') + 1]
only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
os.makedirs(outd, exist_ok=True)
# bounds
mn = Vector((1e9, 1e9, 1e9)); mx = -mn
for ob in sc.objects:
    if ob.type != 'MESH': continue
    for c in ob.bound_box:
        w = ob.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
ctr = (mn + mx) / 2
print('BOUNDS', tuple(round(v, 2) for v in mn), tuple(round(v, 2) for v in mx))
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'; sc.cycles.samples = 12; sc.cycles.use_denoising = False
sc.cycles.max_bounces = 2; sc.cycles.transparent_max_bounces = 4
sc.render.film_transparent = True
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.9, 0.93, 1.0, 1); bg.inputs['Strength'].default_value = 0.45
sd = bpy.data.lights.new('SUN', 'SUN'); sd.energy = 2.2; sd.angle = 0.2
so = bpy.data.objects.new('SUN', sd); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_percentage = 100
S2 = math.sqrt(.5)
VIEWS = {  # name: (view dir into scene)
    'FRONT_from_W_terrace_side': Vector((0, 1, 0)), 'BACK_from_E_DOGU': Vector((0, -1, 0)), 'LEFT_from_N_A_block_end': Vector((1, 0, 0)), 'RIGHT_from_S_east_wing_end': Vector((-1, 0, 0)),
    'DWG_DOGU_CEPHESI': Vector((0, -1, 0)), 'DWG_KUZEY_BATI_CEPHESI': Vector((S2, S2, 0)), 'DWG_GUNEY_BATI_CEPHESI': Vector((-S2, S2, 0)),
}
BOUNDS = {}
cam_d = bpy.data.cameras.new('QC'); cam = bpy.data.objects.new('QC_CAM', cam_d); sc.collection.objects.link(cam); sc.camera = cam
def render(name, v, ortho=True, persp_from=None):
    if ortho:
        cam_d.type = 'ORTHO'
        r = v.cross(Vector((0, 0, 1))).normalized()
        pts = []
        for ob in sc.objects:
            if ob.type != 'MESH': continue
            for c in ob.bound_box: pts.append(ob.matrix_world @ Vector(c))
        us = [p.dot(r) for p in pts]; zs = [p.z for p in pts]
        wu = max(us) - min(us); hz = max(zs) - min(zs)
        uc = (max(us) + min(us)) / 2; zc = (max(zs) + min(zs)) / 2
        cam_d.ortho_scale = max(wu, hz * 4) * 1.04
        px = 2400; sc.render.resolution_x = px; sc.render.resolution_y = max(200, int(px * hz * 1.15 / (wu * 1.04)))
        cam_d.ortho_scale = wu * 1.04
        pos = r * uc + Vector((0, 0, zc)) - v * 300 + v * (ctr.dot(v))
        cam.location = pos
        cam.rotation_euler = (-v).to_track_quat('Z', 'Y').to_euler()
        cam_d.clip_end = 2000
        sS = cam_d.ortho_scale; hh = sS * sc.render.resolution_y / sc.render.resolution_x
        BOUNDS[name] = dict(u0=uc - sS / 2, u1=uc + sS / 2, z0=zc - hh / 2, z1=zc + hh / 2)
    else:
        cam_d.type = 'PERSP'; cam_d.lens = 35
        cam.location = persp_from; cam.rotation_euler = (ctr - persp_from).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x = 1800; sc.render.resolution_y = 1050; cam_d.clip_end = 2000
    sc.render.filepath = os.path.join(outd, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
for k, v in VIEWS.items():
    if only and k not in only: continue
    render(k, v)
if not only or 'AERIAL' in only:
    render('AERIAL_SW', None, ortho=False, persp_from=ctr + Vector((-70, -95, 70)))
    render('AERIAL_NE', None, ortho=False, persp_from=ctr + Vector((75, 80, 60)))

import json
json.dump(BOUNDS, open(os.path.join(outd, 'bounds.json'), 'w'), indent=1)
