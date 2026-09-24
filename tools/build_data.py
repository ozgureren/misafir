"""Collect every exterior element (in local metres, Z=0 at +-0.00) into model.json for Blender."""
import json, pickle, numpy as np, collections
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, box as sbox
from shapely.ops import unary_union, polygonize, linemerge
from shapely.affinity import scale as sscale
from plans import plan_items, plan_texts, PLANS, SITE_O
from facades import load_outlines, facade_segments, backproject, ELEVS, WALL_T, b_parapet
from elevwin import elev_rects

OUT = dict(prisms=[], meshes=[], openings=[], windows=[], doors=[], notes=[], stats={})
def poly_rings(p):
    return [list(map(list, np.array(p.exterior.coords)[:-1]))] + [list(map(list, np.array(i.coords)[:-1])) for i in p.interiors]
def add_prism(name, coll, mat, geom, z0, z1, cut=None):
    geoms = geom.geoms if hasattr(geom, 'geoms') else [geom]
    for k, g in enumerate(geoms):
        if g.is_empty or g.area < 1e-4 or g.geom_type != 'Polygon': continue
        OUT['prisms'].append(dict(name=f'{name}' if len(geoms) == 1 else f'{name}_{k:02d}', coll=coll, mat=mat,
                                  rings=poly_rings(g.simplify(0.005)), z0=z0, z1=z1, cut=cut))
def add_mesh(name, coll, mat, verts, faces, thick=0.0):
    OUT['meshes'].append(dict(name=name, coll=coll, mat=mat, verts=[list(map(float, v)) for v in verts], faces=faces, thick=thick))

O = load_outlines()
A_zem, A_tip, A_16, B_zem = O['A_zem'], O['A_tip'], O['A_16'], O['B_zem']
T = WALL_T
def ring(p, t=T):
    return p.difference(p.buffer(-t, join_style=2))

# ------------------------------------------------------------------ A BLOCK
# walls: plinth (travertine + brick band per section), ground floor (travertine per elevation), upper floors (silicone render)
add_prism('A_PLINTH', 'BUILDING_SHELL', 'ASHLAR', A_zem, -1.0, 0.10, cut='A')          # photos: stone base ~1.1 m above grade
add_prism('A_PLINTH_UPPER', 'BUILDING_SHELL', 'TRAVERTINE', A_zem, 0.10, 1.0, cut='A')            # solid: basement below
add_prism('A_WALL_GF', 'EXTERIOR_WALLS', 'TRAVERTINE', ring(A_zem), 1.0, 4.0, cut='A')
add_prism('A_SLAB_GF', 'BUILDING_SHELL', 'CONCRETE', A_zem.buffer(-T + 0.01), 3.7, 4.0)
add_prism('A_WALL_UPPER', 'EXTERIOR_WALLS', 'PLASTER_A', ring(A_tip), 4.0, 16.0, cut='A')
# parapet/cornice follows the ROOF PLAN outline, which spans straight across the recessed window bays
# of the NW and SE faces (photos: deep cornice with consoles over the recessed bays)
from outline import outline as _outline
A_cat = _outline('A_cat', layers=('r 4', 'r 2', 'Betonarme', 'r 3', 'r 5'), close=0.3)[0]
A_cat = Polygon(A_cat.exterior).union(A_tip).buffer(0.01, join_style=2).buffer(-0.01, join_style=2)
add_prism('A_PARAPET', 'PARAPETS', 'PLASTER_A', ring(A_cat, 0.25), 16.0, 17.4)
add_prism('A_PARAPET_COPING', 'PARAPETS', 'COPING_A', A_cat.buffer(0.04, join_style=2).difference(A_cat.buffer(-0.29, join_style=2)), 17.4, 17.6)
overhang = unary_union([g for g in (lambda d: d.geoms if hasattr(d, 'geoms') else [d])(A_cat.difference(A_tip)) if g.area > 0.3])
add_prism('A_CORNICE_SOFFIT', 'PARAPETS', 'PLASTER_A', overhang.difference(A_cat.buffer(-0.24, join_style=2)).union(overhang.intersection(ring(A_cat, 0.26))), 15.80, 16.0)
OUT['stats']['A_cornice_overhang_m2'] = round(overhang.area, 1)
# roof slab (flat part, +16.00) minus atrium opening
atrium = Polygon([(0.05, -13.44), (6.03, -7.46), (12.62, -14.06), (6.65, -20.03)])
add_prism('A_ROOF_SLAB', 'ROOF', 'ROOF_FLAT', A_cat.buffer(-0.24, join_style=2).difference(atrium), 15.7, 16.05)   # finish above soffit top
# floor slab edges at +4/+7/+10/+13 are hidden in the wall; "Fuga" joint lines skipped.
# roof-top core (+16.00 plan): walls to +19.20 slab, parapet to +19.80 (section A-A)
add_prism('A_CORE_WALLS', 'BUILDING_SHELL', 'PLASTER_A', A_16, 16.0, 19.6)
add_prism('A_CORE_COPING', 'PARAPETS', 'COPING_A', A_16.buffer(0.04, join_style=2), 19.6, 19.8)
# atrium roof: mono-pitch metal roof, +16.95 (axis-1 side) -> +16.00 (axis-8 side) per section A-A
c = np.array(atrium.exterior.coords)[:-1]
# axis-8 side edge is the NE edge (6.03,-7.46)-(12.62,-14.06); height falls toward it
def atr_z(p):
    d = abs((p[0] + p[1]) - (6.03 - 7.46)) / np.sqrt(2)   # distance from NE edge line x+y=-1.43
    return 16.0 + 0.95 * min(d, 9.33) / 9.33
top = [[*p, atr_z(p) + 0.15] for p in c]
add_mesh('A_ATRIUM_ROOF', 'ROOF', 'ROOF_METAL', top, [[0, 1, 2, 3]], thick=0.15)
# fascia closing the gap between slab (+16.0) and sloped atrium roof
fv = []; ff = []
for i in range(4):
    p, q = c[i], c[(i + 1) % 4]
    k = len(fv); fv += [[*p, 16.0], [*q, 16.0], [*q, atr_z(q)], [*p, atr_z(p)]]; ff.append([k, k + 1, k + 2, k + 3])
add_mesh('A_ATRIUM_ROOF_FASCIA', 'ROOF', 'RED_PAINT', fv, ff, thick=0.0)
# inclined glass curtain wall ("Egik Cam"): bottom on axis-8 line at +5.00, top 1.0 m inward at +15.90
b0, b1 = np.array([6.79, -6.81]), np.array([13.30, -13.31])
t0, t1 = np.array([6.08, -7.51]), np.array([12.59, -14.02])
add_mesh('A_INCLINED_CURTAIN_GLASS', 'WINDOW_GLASS', 'BLUE_GLASS', [[*b0, 5.0], [*b1, 5.0], [*t1, 15.9], [*t0, 15.9]], [[0, 1, 2, 3]], thick=0.0)
# curtain-wall grid: 6 vertical mullions (plan 'A-Cam' divisions) + transoms at floor lines
cw_v = []; cw_f = []
def bar(pa, pb, w=0.08, d=0.10):
    pa, pb = np.array(pa, float), np.array(pb, float)
    ax = pb - pa; L = np.linalg.norm(ax); ax /= L
    nrm = np.array([S := np.sqrt(0.5), S, 0.0])
    side = np.cross(ax, nrm); side /= np.linalg.norm(side)
    k = len(cw_v)
    for s in (-w / 2, w / 2):
        for dd in (0, d):
            pass
    corners = []
    for e in (pa, pb):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            corners.append(e + side * sx * w / 2 + nrm * sy * d / 2)
    cw_v.extend(corners)
    f = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
    cw_f.extend([[k + i for i in q] for q in f])
div = [0.0, 0.1428, 0.3121, 0.4815, 0.6508, 0.8201, 1.0]
for s in div:
    pb = b0 + (b1 - b0) * s; pt = t0 + (t1 - t0) * s
    bar([*pb, 5.0], [*pt, 15.9])
for z in (5.0, 7.0, 10.0, 13.0, 15.9):
    s = (z - 5.0) / (15.9 - 5.0)
    pa = b0 + (t0 - b0) * s; pb = b1 + (t1 - b1) * s
    bar([*pa, z], [*pb, z])
add_mesh('A_INCLINED_CURTAIN_FRAME', 'WINDOWS', 'FRAME_DARK', cw_v, cw_f)
# cut the A upper wall where the inclined glazing replaces the facade (+5.00..+15.90)
OUT['openings'].append(dict(target='A', kind='box', p0=[6.79 - 0.2, -6.81 + 0.2], p1=[13.30 + 0.2, -13.31 - 0.2],
                            n=[np.sqrt(.5), np.sqrt(.5)], z0=5.0, z1=15.95, depth_out=0.6, depth_in=1.2))

# ------------------------------------------------------------------ B/C BLOCK
add_prism('B_PLINTH', 'BUILDING_SHELL', 'ASHLAR', B_zem, -1.0, 0.0, cut='B')
Bring = ring(B_zem)
hi = unary_union([sbox(47.4, -6.9, 90, 30), sbox(33.8, 10.3, 90, 30)])
sw = sbox(-20, -40, 20.5, 0.5)
TZ = sbox(20.5, -40, 71.0, -5.8)     # facade behind the south colonnade/pergola (photos: ochre render below the beams)
def bwall(name, geom, top):
    add_prism(name + '_T_LOW', 'EXTERIOR_WALLS', 'OCHRE', geom.intersection(TZ), 0.0, 3.70, cut='B')
    add_prism(name + '_T_HIGH', 'EXTERIOR_WALLS', 'TRAVERTINE', geom.intersection(TZ), 3.70, top, cut='B')
    add_prism(name, 'EXTERIOR_WALLS', 'TRAVERTINE', geom.difference(TZ), 0.0, top, cut='B')
bwall('B_WALL_H560', Bring.intersection(hi), 5.30)
bwall('B_WALL_H480', Bring.intersection(sw).difference(hi), 4.50)
bwall('B_WALL_H460', Bring.difference(hi).difference(sw), 4.30)
cop = Bring.buffer(0.04, join_style=2).intersection(B_zem.buffer(0.04, join_style=2))
add_prism('B_COPING_H560', 'PARAPETS', 'RED_MARBLE', cop.intersection(hi), 5.30, 5.60)
add_prism('B_COPING_H480', 'PARAPETS', 'RED_MARBLE', cop.intersection(sw).difference(hi), 4.50, 4.80)
add_prism('B_COPING_H460', 'PARAPETS', 'RED_MARBLE', cop.difference(hi).difference(sw), 4.30, 4.60)
add_prism('B_ROOF_SLAB', 'ROOF', 'ROOF_FLAT', B_zem.buffer(-T + 0.01, join_style=2), 3.7, 4.0)

def planes_roof(name, region, planes, mat='ROOF_METAL', thick=0.12):
    """lower envelope of planes z = a*x + b*y + c, clipped to region -> planar faces"""
    region = region.buffer(0)
    BIG = 500
    verts = []; faces = []
    for i, (a, b, c0) in enumerate(planes):
        cell = region
        for j, (a2, b2, c2) in enumerate(planes):
            if i == j: continue
            # keep where plane_i <= plane_j : (a-a2)x + (b-b2)y + (c0-c2) <= 0
            A_, B_, C_ = a - a2, b - b2, c0 - c2
            nrm = np.hypot(A_, B_)
            if nrm < 1e-9:
                if C_ > 0: cell = Polygon()
                continue
            # half-plane polygon
            d = np.array([B_, -A_]) / nrm; nvec = np.array([A_, B_]) / nrm
            p0 = -C_ * nvec / nrm
            hp = Polygon([p0 + d * BIG, p0 - d * BIG, p0 - d * BIG - nvec * BIG, p0 + d * BIG - nvec * BIG])
            cell = cell.intersection(hp)
            if cell.is_empty: break
        for g in (cell.geoms if hasattr(cell, 'geoms') else [cell]):
            if g.is_empty or g.geom_type != 'Polygon' or g.area < 1e-3: continue
            pts = np.array(g.exterior.coords)[:-1]
            k = len(verts)
            verts += [[p[0], p[1], a * p[0] + b * p[1] + c0 + thick] for p in pts]
            faces.append(list(range(k, k + len(pts))))
    add_mesh(name, 'ROOF', mat, verts, faces, thick=thick)

# Great hall: hipped roof, eaves (gutter) +5.60, ridge +7.65 (roof plan); eave rectangle = hip end points
hall = Polygon([(48.9, -5.23), (69.72, -5.23), (69.72, 10.86), (48.9, 10.86)])
k = (7.65 - 5.60) / ((10.86 + 5.23) / 2)
x0, x1, y0, y1 = 48.9, 69.72, -5.23, 10.86
planes_roof('B_ROOF_HALL', hall, [(0, k, 5.60 - k * y0), (0, -k, 5.60 + k * y1), (k, 0, 5.60 - k * x0), (-k, 0, 5.60 + k * x1)])
add_prism('B_HALL_ROOF_BASE', 'ROOF', 'ROOF_FLAT', hall.buffer(0.6, join_style=2).intersection(B_zem), 5.30, 5.60)
# West wing: gable, eaves +4.15 on north (y=12.0) and south (y=-6.4), ridge +5.50 at y=2.79
W = Polygon([(9.8, 9.8), (12.0, 12.0), (34.3, 12.0), (34.3, 10.8), (47.4, 10.8), (47.4, -6.35), (20.6, -6.45), (20.6, -1.0)])
kw = (5.50 - 4.15) / 9.2
planes_roof('B_ROOF_WEST', W.intersection(B_zem.buffer(-0.2, join_style=2)), [(0, -kw, 4.15 + kw * 12.0), (0, kw, 4.15 + kw * 6.4)])
# Skylight strip between A and B ("Isiklik"): gable glass roof, eaves +4.80, ridge +5.20
S_ = np.sqrt(.5)
u = np.array([S_, -S_]); w = np.array([S_, S_])
def uw(uu, ww): return (uu * u + ww * w).tolist()
# skylight extents read from the roof-plan grid lines (u along the strip, w across; ridge line at w=5.11)
sky_c = np.array([uw(11.37, 3.31), uw(28.35, 3.31), uw(28.35, 6.91), uw(11.37, 6.91)])
skyP = Polygon(sky_c)
ks = (5.20 - 4.80) / 1.80
planes_roof('B_SKYLIGHT_GLASS', skyP, [(ks * w[0], ks * w[1], 4.80 - ks * 3.31), (-ks * w[0], -ks * w[1], 4.80 + ks * 6.91)], mat='GLASS', thick=0.02)
add_prism('B_SKYLIGHT_CURB', 'ROOF', 'RED_ALU', skyP.difference(skyP.buffer(-0.12, join_style=2)), 4.0, 4.80)

# ENTRANCE PORTAL: piers on the skylight end line (plan squares at w=3.46 / 6.79, u~28.5), pediment eaves +4.65,
# apex +5.40 (GB elevation), panel below the pediment from +3.00 (door head in GB); red marble per photo
def uwp(uu, ww): return (uu * u + ww * w)
for k_, wc in enumerate((3.46, 6.79)):
    add_prism(f'ENTRANCE_PORTAL_PIER_{k_}', 'ENTRANCE', 'RED_MARBLE',
              Polygon([uwp(28.25, wc - 0.25), uwp(28.75, wc - 0.25), uwp(28.75, wc + 0.25), uwp(28.25, wc + 0.25)]), 0.0, 4.65)
add_prism('ENTRANCE_PORTAL_LINTEL', 'ENTRANCE', 'RED_MARBLE',
          Polygon([uwp(28.25, 3.21), uwp(28.75, 3.21), uwp(28.75, 7.04), uwp(28.25, 7.04)]), 3.00, 4.65)
pv = []; pf = []
for uu in (28.25, 28.75):
    for ww, zz in ((3.11, 4.65), (5.12, 5.40), (7.14, 4.65)):
        pv.append([*uwp(uu, ww), zz])
pf = [[0, 1, 2], [5, 4, 3], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]]
add_mesh('ENTRANCE_PORTAL_PEDIMENT', 'ENTRANCE', 'RED_MARBLE', pv, pf)
OUT['sign'] = dict(text='TKİ\nMİSAFİRHANE', center=[*uwp(28.76, 5.125), 3.80], normal=[float(u[0]), float(u[1])], height=0.30)

# ------------------------------------------------------------------ PERGOLA / CANOPY beams (+4.00 top, B roof plan)
segs2 = []
BZb = B_zem.buffer(0.05)
for P, L in plan_items('B_cat', ['r 4']):
    for i in range(len(P) - 1):
        a_, b_ = P[i], P[i + 1]
        if np.linalg.norm(b_ - a_) > 0.9 and not BZb.contains(Point((a_ + b_) / 2)):
            segs2.append((a_, b_))
rects = []
for i in range(len(segs2)):
    a1, b1_ = segs2[i]; d1 = (b1_ - a1) / np.linalg.norm(b1_ - a1)
    for j in range(i + 1, len(segs2)):
        a2, b2_ = segs2[j]; d2 = (b2_ - a2) / np.linalg.norm(b2_ - a2)
        if abs(d1[0] * d2[1] - d1[1] * d2[0]) > 0.02: continue
        nrm = np.array([-d1[1], d1[0]])
        off = (a2 - a1) @ nrm
        if not (0.12 <= abs(off) <= 0.45): continue
        s1 = sorted([0, (b1_ - a1) @ d1]); s2 = sorted([(a2 - a1) @ d1, (b2_ - a1) @ d1])
        lo, hi_ = max(s1[0], s2[0]), min(s1[1], s2[1])
        if hi_ - lo < 1.0: continue
        rects.append(Polygon([a1 + d1 * lo, a1 + d1 * hi_, a1 + d1 * hi_ + nrm * off, a1 + d1 * lo + nrm * off]))
bu = unary_union(rects)
beam_polys = [g for g in (bu.geoms if hasattr(bu, 'geoms') else [bu]) if g.area > 0.2]
OUT['stats']['pergola_beams'] = len(beam_polys)
for i, p in enumerate(beam_polys):
    ztop = 4.70 if p.centroid.x > 79 and p.centroid.y < -14 else 4.00
    add_prism(f'CANOPY_BEAM_{i:02d}', 'CANOPIES', 'TRAVERTINE', p, ztop - 0.30, ztop)

# SE skylight ("+4.60 ISIKLIK MAHYA KOTU", beams "+4.00 KIRIS UST KOTU"): glazed gable over the SE beam grid
se_beams = unary_union([LineString(P) for P, L in plan_items('B_cat', ['r 4']) if P[:, 0].min() > 75 and P[:, 1].max() < -7 and P[:, 1].min() > -16 and np.linalg.norm(P[-1] - P[0]) > 0.8])
if not se_beams.is_empty:
    mrr = se_beams.minimum_rotated_rectangle; cc = np.array(mrr.exterior.coords)[:-1]
    e1, e2 = cc[1] - cc[0], cc[2] - cc[1]
    ax_long = e1 if np.linalg.norm(e1) > np.linalg.norm(e2) else e2
    ax_long = ax_long / np.linalg.norm(ax_long); ax_w = np.array([-ax_long[1], ax_long[0]])
    wv = cc @ ax_w; w0, w1 = wv.min(), wv.max(); half = (w1 - w0) / 2
    kk = (4.60 - 4.00) / half
    planes_roof('B_SKYLIGHT_SE_GLASS', mrr, [(kk * ax_w[0], kk * ax_w[1], 4.00 - kk * w0), (-kk * ax_w[0], -kk * ax_w[1], 4.00 + kk * w1)], mat='GLASS', thick=0.02)
    OUT['stats']['se_skylight'] = dict(area=round(mrr.area, 1), ridge=4.60, eaves=4.00)

# ------------------------------------------------------------------ COLUMNS (free-standing, 'A-Betonarme' outside the shell)
Bx = unary_union([B_zem, A_zem, A_tip]).buffer(0.3)
cols = []
for n in ('B_zem', 'A_zem'):
    for P, L in plan_items(n, ['Betonarme']):
        if len(P) >= 3 and np.ptp(P, axis=0).max() < 0.8:
            c_ = P.mean(0)
            if not Bx.contains(Point(c_)):
                cols.append(Polygon(P).convex_hull if len(P) >= 3 else None)
colU = unary_union([c for c in cols if c is not None and c.area > 0.02])
colU = [g for g in (colU.geoms if hasattr(colU, 'geoms') else [colU])]
OUT['stats']['columns'] = len(colU)
for i, g in enumerate(colU):
    x_, y_ = g.centroid.x, g.centroid.y
    court = (-3 < x_ < 12 and 0 < y_ < 12)
    z0 = -4.15 if court else 0.0
    ztop = 3.70 if y_ < -5 else 4.0
    add_prism(f'COLUMN_{i:02d}', 'COLUMNS', 'TRAVERTINE', g, z0, ztop)

json.dump(OUT, open('model_part1.json', 'w'))
print({k: len(v) if isinstance(v, list) else v for k, v in OUT.items()})
