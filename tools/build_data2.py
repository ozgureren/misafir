"""Part 2: openings (elevation back-projection + plan fallback), exterior stairs, terraces, court."""
import json, pickle, re, numpy as np, collections
from shapely.geometry import Polygon, LineString, Point, box as sbox
from shapely.ops import unary_union
from plans import plan_items, plan_texts
from facades import load_outlines, facade_segments, backproject, ELEVS, WALL_T
from elevwin import elev_rects

OUT = json.load(open('model_part1.json'))
def poly_rings(p):
    return [list(map(list, np.array(p.exterior.coords)[:-1]))] + [list(map(list, np.array(i.coords)[:-1])) for i in p.interiors]
def add_prism(name, coll, mat, geom, z0, z1, cut=None):
    geoms = geom.geoms if hasattr(geom, 'geoms') else [geom]
    for k, g in enumerate(geoms):
        if g.is_empty or g.geom_type != 'Polygon' or g.area < 1e-3: continue
        OUT['prisms'].append(dict(name=name if len(geoms) == 1 else f'{name}_{k:02d}', coll=coll, mat=mat,
                                  rings=poly_rings(g.simplify(0.005)), z0=z0, z1=z1, cut=cut))
O = load_outlines()
segs = facade_segments(O)
from facades import set_rings; set_rings(O)
Bu = unary_union([O['B_zem'], O['A_zem'], O['A_tip']])
NOTES = OUT['notes']

# ---------------------------------------------------------------- openings from elevations
ops = []
EXTRA = {'KB': [r for r in elev_rects('KB', layers=('r 3',), tol=3.0) if 531580 <= r[0] and r[2] <= 531760]}
OUT['stats']['stair_shaft_windows_KB'] = len(EXTRA['KB'])
for name in ELEVS:
    for rc in elev_rects(name) + EXTRA.get(name, []):
        if name == 'DOGU' and rc[0] > 525600 and rc[2] < 526300 and (rc[1] - ELEVS[name]['zero']) / 100 > 4.0:
            NOTES.append('DOGU: inclined curtain wall rectangle represented by A_INCLINED_CURTAIN_* (not as a window)'); continue
        oo = backproject(segs, name, rc)
        if oo is None:
            NOTES.append(f'elevation {name}: rectangle at elev-x {rc[0]:.0f}-{rc[2]:.0f}, z {(rc[1]-ELEVS[name]["zero"])/100:+.2f}..{(rc[3]-ELEVS[name]["zero"])/100:+.2f} not matched to a facade')
            continue
        for o in oo:
            o['face_on'] = float(-(o['n'] @ ELEVS[name]['v']))
            ops.append(o)
# dedupe (same opening seen in two elevations) -> keep most face-on view
def overl(a, b):
    if a['ring'] != b['ring']: return False
    ma, mb = (a['p0'] + a['p1']) / 2, (b['p0'] + b['p1']) / 2
    if np.linalg.norm(ma - mb) > 0.5 * max(a['width'], b['width']) + 0.15: return False
    zo = min(a['z1'], b['z1']) - max(a['z0'], b['z0'])
    return zo > 0.5 * min(a['z1'] - a['z0'], b['z1'] - b['z0'])
ops.sort(key=lambda o: -o['face_on'])
keep = []
for o in ops:
    if not any(overl(o, k) for k in keep): keep.append(o)
OUT['stats']['elev_openings_raw'] = len(ops); OUT['stats']['elev_openings'] = len(keep)
for o in keep: o['src'] = 'elevation'

# ---------------------------------------------------------------- plan windows (A-Cam inside exterior wall band) as cross-check / fallback
def plan_windows(plan, ring_name, poly):
    ringL = LineString(poly.exterior.coords)
    band = poly.difference(poly.buffer(-0.40)).buffer(0.05)
    iv = collections.defaultdict(list)
    for P, L in plan_items(plan, ['Cam']):
        l = LineString(P)
        if l.length < 0.25 or not band.contains(l): continue
        # parallel to ring locally?
        a, b = ringL.project(Point(P[0])), ringL.project(Point(P[-1]))
        if abs(abs(b - a) - l.length) > 0.12: continue
        iv[0].append(sorted([a, b]))
    ivs = sorted(iv[0]); merged = []
    for a, b in ivs:
        if merged and a <= merged[-1][1] + 0.12: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    out = []
    for a, b in merged:
        if b - a < 0.35: continue
        p0 = np.array(ringL.interpolate(a).coords[0]); p1 = np.array(ringL.interpolate(b).coords[0])
        d = p1 - p0; n = np.array([d[1], -d[0]]) / max(np.linalg.norm(d), 1e-9)
        out.append(dict(ring=ring_name, p0=p0, p1=p1, n=n, width=float(np.linalg.norm(d)), s0=a, s1=b))
    return out

def covered(pw, cand):
    m = (pw['p0'] + pw['p1']) / 2
    for o in cand:
        if o['ring'] != pw['ring']: continue
        mo = (o['p0'] + o['p1']) / 2
        if np.linalg.norm(m - mo) < 0.5 * max(pw['width'], o['width']) + 0.2: return o
    return None

FLOOR = {'A_zem': [1.0], 'A_tip': [4.0, 7.0, 10.0, 13.0], 'B_zem': [0.0]}
added = []; cmp = collections.Counter()
for plan, ringn in (('A_zem', 'A_zem'), ('A_tip', 'A_tip'), ('B_zem', 'B_zem')):
    pws = plan_windows(plan, ringn, O[ringn])
    cmp[f'{ringn}_plan_windows'] = len(pws)
    for pw in pws:
        if covered(pw, keep): cmp[f'{ringn}_matched'] += 1; continue
        # nearest elevation-derived opening on the same ring gives sill/head relative to its floor
        same = [o for o in keep if o['ring'] == ringn]
        if not same: continue
        m = (pw['p0'] + pw['p1']) / 2
        ref = min(same, key=lambda o: np.linalg.norm((o['p0'] + o['p1']) / 2 - m))
        fl_ref = max([f for f in FLOOR[ringn] if f <= ref['z0'] + 0.05] or [FLOOR[ringn][0]])
        for fl in FLOOR[ringn]:
            added.append(dict(src='plan', ring=ringn, p0=pw['p0'], p1=pw['p1'], n=pw['n'], width=pw['width'],
                              z0=ref['z0'] - fl_ref + fl, z1=ref['z1'] - fl_ref + fl, ref_dist=float(np.linalg.norm((ref['p0'] + ref['p1']) / 2 - m))))
        cmp[f'{ringn}_plan_only'] += 1
OUT['stats'].update(cmp)
allops = keep + added

# ---------------------------------------------------------------- classify + emit
TARGET = {'A_zem': 'A', 'A_tip': 'A', 'A_16': 'A', 'B_zem': 'B'}
BASEF = {'A_zem': 1.0, 'A_tip': None, 'A_16': 16.0, 'B_zem': 0.0}
MAIN_ENTRANCES = [np.array([8.3, -31.0]), np.array([19.6, -15.0])]   # A curved vestibule; B entrance under skylight
nw = nd = 0
for o in allops:
    bf = BASEF[o['ring']]
    is_door = bf is not None and o['z0'] <= bf + 0.12 and o['z1'] - o['z0'] > 1.8
    rec = dict(p0=list(map(float, o['p0'])), p1=list(map(float, o['p1'])), n=list(map(float, o['n'])),
               z0=float(o['z0']), z1=float(o['z1']), ring=o['ring'], src=o['src'], elev=o.get('elev'))
    OUT['openings'].append(dict(target=TARGET[o['ring']], kind='box', p0=rec['p0'], p1=rec['p1'], n=rec['n'],
                                z0=rec['z0'], z1=rec['z1'], depth_out=0.05, depth_in=WALL_T + 0.08))
    if is_door:
        m = (o['p0'] + o['p1']) / 2
        rec['entrance'] = bool(min(np.linalg.norm(m - e) for e in MAIN_ENTRANCES) < 3.0)
        OUT['doors'].append(rec); nd += 1
    else:
        OUT['windows'].append(rec); nw += 1
OUT['stats']['windows'] = nw; OUT['stats']['doors'] = nd

# ---------------------------------------------------------------- exterior stairs (numbered treads, riser data from plan labels)
STAIRS = {  # name: (plan, label box, z_bottom, riser, n, parapet_top or None)
    'BM1': ('B_zem', (22, -20, 27, -15), -1.00, 1.0 / 6, 6),
    'BM2': ('B_zem', (79, -18, 84, -12.5), -1.00, 1.0 / 6, 6),
    'BM4': ('B_zem', (51.5, 11, 55, 14), -1.00, 1.0 / 6, 6),
    'BM5': ('B_zem', (23.5, 11, 30, 14), -4.15, 0.175, 18),
    'BM6a': ('B_zem', (-2, 0, 0.5, 6.5), -4.15, 0.175, 18),
    'BM6b': ('B_zem', (1.0, 7.0, 7.5, 9.5), -4.15, 0.175, 18),
    'BM7': ('A_zem', (-13, -19, -7, -12), -4.15, 0.175, 18),
}
def merd_lines(plan, bx):
    out = []
    for P, L in plan_items(plan, ['Merdiven']):
        if P[:, 0].min() >= bx[0] - 1.5 and P[:, 0].max() <= bx[2] + 1.5 and P[:, 1].min() >= bx[1] - 1.5 and P[:, 1].max() <= bx[3] + 1.5:
            for i in range(len(P) - 1):
                if np.linalg.norm(P[i + 1] - P[i]) > 0.05: out.append((P[i], P[i + 1]))
    return out
for sname, (plan, bx, zb, riser, n) in STAIRS.items():
    nums = {}
    for p, v, L in plan_texts(plan):
        if 'Merdiven' in L and v.strip().isdigit() and bx[0] <= p[0] <= bx[2] and bx[1] <= p[1] <= bx[3]:
            nums.setdefault(int(v.strip()), p)
    lines = merd_lines(plan, bx)
    if len(nums) >= 3:
        ks = sorted(nums)
        C = np.array([nums[k] for k in ks])
    else:
        # BM1: no numbers -> nosing lines ordered along stair direction; top toward the +-0.00 level mark
        L2 = [l for l in lines if np.linalg.norm(l[1] - l[0]) > 1.5]
        d = L2[0][1] - L2[0][0]; d /= np.linalg.norm(d); nrm = np.array([-d[1], d[0]])
        pos = sorted({round(float(((l[0] + l[1]) / 2) @ nrm), 2) for l in L2})
        top_pt = np.array([22.9, -16.2]); mid = np.mean([(l[0] + l[1]) / 2 for l in L2], axis=0)
        mid_d = float(mid @ d)
        if (top_pt @ nrm) > np.mean(pos): pos = pos[::-1]    # start from bottom
        C = np.array([mid_d * d + ((pos[i] + pos[i + 1]) / 2) * nrm for i in range(len(pos) - 1)] +
                     [mid_d * d + (pos[-1] + (pos[-1] - pos[-2]) / 2) * nrm])
        C = C[:n]
        ks = list(range(1, len(C) + 1))
    # tread quads: nosing lines nearest to each centre on either side, along the local walking direction
    verts = []; faces = []
    zt = zb + riser * n
    for i, k in enumerate(ks):
        c = C[i]
        dirv = (C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]); dirv /= np.linalg.norm(dirv)
        cand = []
        for a, b in lines:
            ab = b - a; L = np.linalg.norm(ab)
            if L < 0.6: continue
            if abs((ab / L) @ dirv) > 0.5: continue       # must be roughly across the walking direction
            t = np.clip((c - a) @ ab / L ** 2, 0, 1); q = a + t * ab
            dist = (q - c) @ dirv
            if np.linalg.norm(q - c) < 0.45: cand.append((dist, a, b))
        back = [x for x in cand if x[0] < 0]; fwd = [x for x in cand if x[0] > 0]
        if back and fwd:
            b0 = max(back, key=lambda x: x[0]); f0 = min(fwd, key=lambda x: x[0])
            a1, b1 = b0[1], b0[2]; a2, b2 = f0[1], f0[2]
            if np.dot(b1 - a1, b2 - a2) < 0: a2, b2 = b2, a2
            quad = [a1, b1, b2, a2]
        else:
            # fall back: rectangle from tread depth and stair width of nearest line
            near = min(cand, key=lambda x: abs(x[0])) if cand else None
            wv = (near[2] - near[1]) if near else np.array([-dirv[1], dirv[0]]) * 1.2
            depth = np.linalg.norm(C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]) / (2 if 0 < i < len(C) - 1 else 1)
            h = wv / 2; e = dirv * depth / 2
            quad = [c - h - e, c + h - e, c + h + e, c - h + e]
        ztop = zb + riser * k
        g = Polygon(quad)
        if not g.is_valid or g.area < 0.02: g = g.convex_hull
        if g.area < 0.02: continue
        add_prism(f'{sname}_STEP_{k:02d}', 'EXTERIOR_STAIRS', 'TRAVERTINE', g, zb - 0.05, ztop)
    OUT['stats'][f'stair_{sname}'] = dict(steps=len(ks), z_bottom=zb, z_top=round(zt, 3), riser=round(riser, 4))

# stair pits (BM5, BM7): retaining walls; BM7 labelled "-0.70 Parapet ust kotu"
for sname, bx, top in (('BM7', (-13, -19, -7, -12), -0.70), ('BM5', (23.5, 11, 30, 14), -0.70)):
    pit = unary_union([p for p in [Polygon(q['rings'][0]) for q in OUT['prisms'] if q['name'].startswith(sname + '_STEP')]]).buffer(0.05, join_style=2)
    pit = pit.convex_hull.difference(Bu.buffer(0.02))
    wall = pit.buffer(0.20, join_style=2).difference(pit).difference(Bu)
    add_prism(f'{sname}_PIT_WALL', 'EXTERIOR_STAIRS', 'CONCRETE', wall, -4.15, top)

# ---------------------------------------------------------------- terraces
holes = pickle.load(open('terr_holes.pkl', 'rb'))
def pick(pred): return unary_union([h for h in holes if pred(h)])
t040 = pick(lambda h: 16.4 < h.bounds[0] < 16.6 and h.area < 20)
t070 = pick(lambda h: 25.4 < h.bounds[0] < 25.6 and h.bounds[1] < -16)
t000 = pick(lambda h: not (16.4 < h.bounds[0] < 16.6 and h.area < 20) and not (25.4 < h.bounds[0] < 25.6 and h.bounds[1] < -16))
t000 = t000.buffer(0.22, join_style=2).buffer(-0.02, join_style=2).difference(Bu)
t070 = t070.buffer(0.2, join_style=2).difference(t000).difference(Bu)
t040 = t040.buffer(0.2, join_style=2).difference(t000).difference(t070).difference(Bu)
add_prism('TERRACE_000', 'ENTRANCE', 'GRANITE', t000, -1.0, 0.0)
add_prism('TERRACE_070', 'ENTRANCE', 'GRANITE', t070, -1.0, -0.70)
add_prism('TERRACE_040', 'ENTRANCE', 'GRANITE', t040, -1.0, -0.40)
# SE open terrace: 95 cm wall (top +0.95) on its free edges (x=48.1 side and south edge), per "h: 95 cm Duvar" / +0.95
se = max(holes, key=lambda h: h.area)
edge = se.buffer(0.2, join_style=2).difference(se.buffer(0.0))
free = edge.intersection(unary_union([sbox(47.5, -22, 48.7, -12.2), sbox(47.5, -22, 77.5, -20.9), Polygon([(76.4, -21.8), (81.6, -16.6), (80.9, -16.1), (75.9, -21.2)])]))
# NOTE: site photos show only a railing on this edge; the DWG 'h: 95 cm Duvar' is read as the terrace edge wall
# from grade (-1.00) to the terrace (~0.00), which the TERRACE_000 podium already forms. No wall above the terrace.

# ---------------------------------------------------------------- sunken pool court (-4.15) between A and the NW wing of B
court = max(pickle.load(open('extpolys.pkl', 'rb')), key=lambda p: p.area)
add_prism('COURT_FLOOR', 'BUILDING_SHELL', 'GRANITE', court.difference(Bu), -4.45, -4.15)
# building faces toward the court continue down to the court floor (basement facade visible here)
for nm, poly in (('A', O['A_zem']), ('B', O['B_zem'])):
    r = poly.difference(poly.buffer(-WALL_T, join_style=2)).intersection(court.buffer(0.6))
    add_prism(f'{nm}_COURT_BASEMENT_WALL', 'EXTERIOR_WALLS', 'PLASTER_A' if nm == 'A' else 'TRAVERTINE', r, -4.15, -1.0, cut=nm)
# free court edge (not against a building): retaining wall to the -0.70 parapet level marked on the stair's outer arc
cedge = court.buffer(0.2, join_style=2).difference(court).difference(Bu.buffer(0.3))
add_prism('COURT_RETAINING_WALL', 'EXTERIOR_STAIRS', 'CONCRETE', cedge, -4.15, -0.70)

# ---------------------------------------------------------------- cornice consoles (photos): under the A cornice soffit,
# between neighbouring top-floor windows of each recessed bay; triangular, 0.20 thick, 0.60 deep at the wall
from outline import outline as _outline
A_cat = _outline('A_cat', layers=('r 4', 'r 2', 'Betonarme', 'r 3', 'r 5'), close=0.3)[0]
A_cat = Polygon(A_cat.exterior).union(O['A_tip']).buffer(0.01, join_style=2).buffer(-0.01, join_style=2)
ovh = [g for g in (lambda d: d.geoms if hasattr(d, 'geoms') else [d])(A_cat.difference(O['A_tip'])) if g.area > 5]
top = [o for o in OUT['windows'] if o['ring'] == 'A_tip' and 13.3 < o['z0'] < 14.2]
bv = []; bfc = []; nb = 0
for zone in ovh:
    ws = [o for o in top if zone.buffer(0.4).contains(Point(np.mean([o['p0'], o['p1']], axis=0)))]
    if len(ws) < 2: continue
    n = np.array(ws[0]['n']); t = np.array([-n[1], n[0]])
    ws.sort(key=lambda o: np.mean([o['p0'], o['p1']], axis=0) @ t)
    mids = [(np.mean([a['p0'], a['p1']], axis=0) + np.mean([b['p0'], b['p1']], axis=0)) / 2 for a, b in zip(ws[:-1], ws[1:])]
    ends = [np.mean([ws[0]['p0'], ws[0]['p1']], axis=0) - t * (np.linalg.norm(mids[0] - np.mean([ws[0]['p0'], ws[0]['p1']], axis=0)) if mids else 1.2),
            np.mean([ws[-1]['p0'], ws[-1]['p1']], axis=0) + t * (np.linalg.norm(mids[-1] - np.mean([ws[-1]['p0'], ws[-1]['p1']], axis=0)) if mids else 1.2)]
    for m in mids + ends:
        if not zone.buffer(0.3).contains(Point(m)): continue
        # depth: from wall face to cornice front
        d = 0.0
        while d < 2.5 and A_cat.buffer(-0.02).contains(Point(m + n * (d + 0.05))): d += 0.05
        if d < 0.3: continue
        k0 = len(bv)
        for sgn in (-0.10, 0.10):
            q = m + t * sgn
            bv += [[*q, 15.80], [*(q + n * d), 15.80], [*q, 15.20]]
        bfc += [[k0 + 0, k0 + 1, k0 + 2], [k0 + 5, k0 + 4, k0 + 3], [k0 + 0, k0 + 3, k0 + 4, k0 + 1], [k0 + 1, k0 + 4, k0 + 5, k0 + 2], [k0 + 2, k0 + 5, k0 + 3, k0 + 0]]
        nb += 1
OUT['meshes'].append(dict(name='A_CORNICE_CONSOLES', coll='PARAPETS', mat='PLASTER_A', verts=bv, faces=bfc, thick=0.0))
OUT['stats']['cornice_consoles'] = nb

# ---------------------------------------------------------------- railings: stainless tube, h 0.90 (DWG note "Alu. boru korkuluk h: 90 cm", photos)
# on free terrace edges: not against the building, not across stair flights / portal
stairsU = unary_union([Polygon(q['rings'][0]) for q in OUT['prisms'] if '_STEP_' in q['name']]).buffer(0.6)
portal = Polygon([np.array([22.2, -18.4]), np.array([25.6, -15.0]), np.array([26.2, -15.6]), np.array([22.8, -19.0])]).buffer(0.8)
keepout = unary_union([Bu.buffer(0.7), stairsU, portal])
rv = []; rf = []
def rbox(p, q, z0, z1, wd):
    p, q = np.array(p), np.array(q); d = q - p; L = np.linalg.norm(d)
    if L < 1e-3: return
    d /= L; nn = np.array([-d[1], d[0]]) * wd / 2; dd = d * 0.0
    k = len(rv)
    for zz in (z0, z1):
        rv.extend([[*(p - nn), zz], [*(q - nn), zz], [*(q + nn), zz], [*(p + nn), zz]])
    rf.extend([[k + a for a in f] for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))])
nrail = 0.0
for tname, tpoly, zt in (('000', t000, 0.0), ('040', t040, -0.40)):
    for g in (tpoly.geoms if hasattr(tpoly, 'geoms') else [tpoly]):
        edge = LineString(g.exterior.coords).difference(keepout)
        for ln in (edge.geoms if hasattr(edge, 'geoms') else [edge]):
            if ln.is_empty or ln.length < 1.0: continue
            c = np.array(ln.coords)
            # inset 0.08 m into the terrace
            for a, b in zip(c[:-1], c[1:]):
                L = np.linalg.norm(b - a)
                if L < 0.05: continue
                rbox(a, b, zt + 0.87, zt + 0.92, 0.05)                 # handrail
                for zz in (0.25, 0.45, 0.65):
                    rbox(a, b, zt + zz, zt + zz + 0.02, 0.02)          # rods (photo: horizontal rods)
                npost = max(1, int(L / 1.5))
                for i in range(npost + 1):
                    pp = a + (b - a) * i / npost
                    d_ = (b - a) / L * 0.025
                    rbox(pp - d_, pp + d_, zt, zt + 0.92, 0.05)
                nrail += L
OUT['meshes'].append(dict(name='TERRACE_RAILINGS', coll='RAILINGS', mat='STAINLESS', verts=rv, faces=rf, thick=0.0))
OUT['stats']['railing_length_m'] = round(nrail, 1)

OUT['stats']['counts'] = dict(prisms=len(OUT['prisms']), meshes=len(OUT['meshes']), openings=len(OUT['openings']))
json.dump(OUT, open('model.json', 'w'))
pickle.dump(allops, open('allops.pkl', 'wb'))
print(json.dumps(OUT['stats'], indent=1))
print('\n'.join(NOTES))

# ---------------------------------------------------------------- robust opening cut: horizontal bands, 2D difference
def opening_fp(o):
    p0, p1, n = np.array(o['p0']), np.array(o['p1']), np.array(o['n'])
    ax = p1 - p0; L = np.linalg.norm(ax); ax = ax / max(L, 1e-9)
    ins = -n
    return Polygon([p0 - ins * o['depth_out'], p1 - ins * o['depth_out'], p1 + ins * o['depth_in'], p0 + ins * o['depth_in']]).buffer(0)
FPS = {'A': [], 'B': []}
for o in OUT['openings']:
    FPS[o['target']].append((opening_fp(o), o['z0'], o['z1']))
newp = []
for p in OUT['prisms']:
    if not p.get('cut'):
        newp.append(p); continue
    base = Polygon(p['rings'][0], p['rings'][1:]).buffer(0)
    rel = [(f, max(z0, p['z0']), min(z1, p['z1'])) for f, z0, z1 in FPS[p['cut']] if z1 > p['z0'] + 1e-3 and z0 < p['z1'] - 1e-3 and f.intersects(base)]
    zs = sorted({round(p['z0'], 3), round(p['z1'], 3)} | {round(z, 3) for _, a, b in rel for z in (a, b)})
    bands = []
    for za, zb in zip(zs[:-1], zs[1:]):
        if zb - za < 1e-3: continue
        zm = (za + zb) / 2
        cut = unary_union([f for f, a, b in rel if a <= zm <= b])
        g = base.difference(cut) if not cut.is_empty else base
        key = g.wkb
        if bands and bands[-1][2] == key: bands[-1][1] = zb   # merge identical consecutive bands
        else: bands.append([za, zb, key, g])
    for i, (za, zb, _, g) in enumerate(bands):
        for k, gg in enumerate(g.geoms if hasattr(g, 'geoms') else [g]):
            if gg.is_empty or gg.geom_type != 'Polygon' or gg.area < 1e-4: continue
            newp.append(dict(name=f"{p['name']}|{i:02d}{k:02d}", group=p['name'], coll=p['coll'], mat=p['mat'],
                             rings=poly_rings(gg.simplify(0.003)), z0=za, z1=zb, cut=None))
OUT['prisms'] = newp
json.dump(OUT, open('model.json', 'w'))
print('banded prisms', len(newp))
