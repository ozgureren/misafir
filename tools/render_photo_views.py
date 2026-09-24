"""Photo-matched perspective renders (sun + sky + simple ground). Ground/sky exist only in this render scene."""
import bpy, math, sys, os
from mathutils import Vector
blend = sys.argv[sys.argv.index('--blend') + 1]; outd = sys.argv[sys.argv.index('--out') + 1]
samples = int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 48
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; os.makedirs(outd, exist_ok=True)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 4
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = -0.9
# sky + sun (spring afternoon as in the photos)
w = bpy.data.worlds.new('SKY'); sc.world = w; w.use_nodes = True
nt = w.node_tree; bg = nt.nodes['Background']
sky = nt.nodes.new('ShaderNodeTexSky')
try: sky.sky_type = 'NISHITA'
except Exception: pass
sky.sun_elevation = math.radians(38); sky.sun_rotation = math.radians(200)
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.35
sd = bpy.data.lights.new('SUN', 'SUN'); sd.energy = 3.2; sd.angle = math.radians(0.6); sd.color = (1.0, 0.96, 0.9)
so = bpy.data.objects.new('SUN', sd); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(52), 0, math.radians(200 - 90))
# ground: grass at -1.00 with a paved apron (render-only context, not part of the model)
def plane(name, size, z, col, rough, loc=(30, -10)):
    me = bpy.data.meshes.new(name); s = size / 2
    me.from_pydata([(loc[0]-s, loc[1]-s, z), (loc[0]+s, loc[1]-s, z), (loc[0]+s, loc[1]+s, z), (loc[0]-s, loc[1]+s, z)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = col; b.inputs['Roughness'].default_value = rough
    if name == 'GRASS':
        n = m.node_tree.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 40
        r = m.node_tree.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = (0.18, 0.26, 0.08, 1); r.color_ramp.elements[1].color = (0.32, 0.40, 0.14, 1)
        m.node_tree.links.new(n.outputs['Fac'], r.inputs['Fac']); m.node_tree.links.new(r.outputs['Color'], b.inputs['Base Color'])
    me.materials.append(m)
plane('GRASS', 4000, -1.02, (0.25, 0.33, 0.1, 1), 0.9)
cam_d = bpy.data.cameras.new('PH'); cam = bpy.data.objects.new('PH', cam_d); sc.collection.objects.link(cam); sc.camera = cam
S2 = math.sqrt(.5)
portal = Vector((23.96, -16.71, 2.0)); n = Vector((S2, -S2, 0))
VIEWS = {
  # name: (camera location, look-at, lens mm)
  'PHOTO1_entrance_portal': (portal + n * 13 + Vector((0, 0, -0.9)), portal + Vector((0, 0, 1.2)), 16),
  'PHOTO2_tower_and_portal': (portal + n * 24 + Vector((-10, -10, -1.4)) + Vector((-6, 6, 0)), Vector((6, -18, 7)), 14),
  'PHOTO3_terrace_to_tower': (Vector((62, -17.5, 1.6)), Vector((12, -8, 7)), 18),
  'PHOTO4_tower_recessed_bay': (Vector((24, -33, 0.7)), Vector((13, -24, 12)), 16),
  'AERIAL_TEXTURED_SW': (Vector((-45, -95, 65)), Vector((32, -8, 0)), 30),
  'AERIAL_TEXTURED_NE': (Vector((105, 70, 55)), Vector((32, -8, 0)), 30),
}
only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
for k, (loc, tgt, lens) in VIEWS.items():
    if only and k not in only: continue
    cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler(); cam_d.lens = lens
    sc.render.resolution_x = 1600; sc.render.resolution_y = 900 if 'AERIAL' in k else 720
    if 'PHOTO4' in k: sc.render.resolution_x, sc.render.resolution_y = 900, 1180
    sc.render.filepath = os.path.join(outd, k + '.jpg'); sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
    bpy.ops.render.render(write_still=True); print('rendered', k)
