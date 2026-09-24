"""Facade rings + elevation back-projection of window/door rectangles."""
import numpy as np, pickle
from shapely.geometry import Polygon, Point, box as sbox
from outline import outline
from elevwin import elev_rects

S2 = np.sqrt(0.5)
# view dir v (into scene), right vector r, c0 (elev x of site origin, cm), zero (elev y of +-0.00, cm)
ELEVS = {
    'DOGU': dict(v=np.array([0.0, -1.0]), r=np.array([-1.0, 0.0]), c0=526962.0, zero=38528.0),
    'KB':   dict(v=np.array([S2, S2]),   r=np.array([S2, -S2]),  c0=528828.0, zero=38528.0),
    'GB':   dict(v=np.array([-S2, S2]),  r=np.array([S2, S2]),   c0=538574.0, zero=38568.0),
}
WALL_T = 0.29

def ccw(poly):
    from shapely.geometry.polygon import orient
    return orient(poly, 1.0)

def load_outlines():
    O = {}
    O['A_zem'] = ccw(outline('A_zem', close=0.9)[0])
    # the atrium stretch of the NE facade has no wall line in the tip plan (only the inclined glazing), so the
    # automatic outline runs along the interior gallery edge; close it on the facade line (x+y = 0.18*sqrt2)
    patch = Polygon([(6.57, -6.32), (13.38, -13.17), (12.62, -13.93), (6.17, -7.48)])
    tower = O['A_zem'].intersection(Polygon([(5.8, -29.6), (8.4, -27.0), (11.4, -30.0), (8.1, -33.3)]))   # rounded stair tower (full height in KB elevation)
    O['A_tip'] = ccw(outline('A_tip')[0].union(patch).union(tower).buffer(0.01, join_style=2).buffer(-0.01, join_style=2))
    O['A_16'] = ccw(outline('A_16')[0])
    O['B_zem'] = ccw(outline('B_zem')[0])
    O['B_bod'] = ccw(outline('B_bod')[0])
    O['A_bod'] = ccw(outline('A_bod')[0])
    return O

# B/C parapet height by region
def b_parapet(p):
    x, y = p
    if (x >= 47.4 and y >= -6.9) or (x >= 33.8 and y >= 10.3):
        return 5.60
    if x < 20.5 and y < 0.5:
        return 4.80
    return 4.60

def facade_segments(O):
    """list of dict(ring, i, p, q, n, z0, z1, floor)"""
    segs = []
    def add(name, poly, z0, z1, floors):
        c = np.array(poly.exterior.coords)
        for i in range(len(c) - 1):
            p, q = c[i], c[i + 1]
            d = q - p; L = np.linalg.norm(d)
            if L < 1e-6: continue
            n = np.array([d[1], -d[0]]) / L   # outward for CCW ring
            zz1 = z1(0.5 * (p + q)) if callable(z1) else z1
            segs.append(dict(ring=name, i=i, p=p, q=q, n=n, z0=z0, z1=zz1, floors=floors, L=L))
    add('A_zem', O['A_zem'], -1.0, 4.0, [1.0])
    add('A_tip', O['A_tip'], 4.0, 17.6, [4.0, 7.0, 10.0, 13.0])
    add('A_16', O['A_16'], 16.0, 19.8, [16.0])
    add('B_zem', O['B_zem'], -1.0, b_parapet, [0.0])
    return segs

def backproject(segs, name, rect, tol=0.02):
    E = ELEVS[name]; v, r = E['v'], E['r']
    u0 = (rect[0] - E['c0']) / 100; u1 = (rect[2] - E['c0']) / 100
    z0 = (rect[1] - E['zero']) / 100; z1 = (rect[3] - E['zero']) / 100
    uc, zc = 0.5 * (u0 + u1), 0.5 * (z0 + z1)
    best = None
    for s in segs:
        if s['n'] @ v > -0.25: continue
        if not (s['z0'] - 0.05 <= zc <= s['z1'] + 0.05): continue
        up, uq = s['p'] @ r, s['q'] @ r
        if abs(uq - up) < 1e-6: continue
        t = (uc - up) / (uq - up)
        if -tol <= t <= 1 + tol:
            pt = s['p'] + t * (s['q'] - s['p'])
            dep = pt @ v
            if best is None or dep < best[0]:
                best = (dep, s, t)
    if best is None: return None
    dep, s, t = best
    # walk along the facade polyline from the hit point until the projected coordinate reaches each end
    from shapely.geometry import LineString as _LS, Point as _P
    RING = _RINGS[s['ring']]
    sc0 = RING.project(_P(s['p'] + t * (s['q'] - s['p'])))
    L = RING.length; step = 0.05
    def walk(ut):
        best_ = None
        for sgn in (1, -1):
            prev = None
            for k in range(0, int(60 / step)):
                sp = (sc0 + sgn * k * step) % L
                pt = np.array(RING.interpolate(sp).coords[0]); uu = pt @ r
                if prev is not None and (prev[1] - ut) * (uu - ut) <= 0:
                    f = (ut - prev[1]) / (uu - prev[1] + 1e-12)
                    arc = k - 1 + f
                    if best_ is None or arc < best_[0]: best_ = (arc, (sc0 + sgn * arc * step) % L, sgn)
                    break
                prev = (sp, uu)
        return best_
    ea, eb = walk(u0), walk(u1)
    if ea is None or eb is None: return None
    sa, sb = ea[1], eb[1]
    # sub-polyline between sa and sb (short way through the hit point)
    def seg_pts(a, b, sgn):
        n_ = max(2, int(abs(((b - a) * sgn) % L) / 0.05) + 1)
        span = ((b - a) * sgn) % L
        return [np.array(RING.interpolate((a + sgn * span * i / (n_ - 1)) % L).coords[0]) for i in range(n_)]
    pts = seg_pts(sa, sb, 1) if ea[2] == -1 else seg_pts(sa, sb, -1)
    # split into straight pieces (vertex where direction changes > 4 deg)
    pieces = [[pts[0]]]
    for i in range(1, len(pts) - 1):
        d1 = pts[i] - pts[i - 1]; d2 = pts[i + 1] - pts[i]
        if np.linalg.norm(d1) < 1e-6 or np.linalg.norm(d2) < 1e-6: continue
        ang = np.degrees(np.arccos(np.clip(d1 @ d2 / np.linalg.norm(d1) / np.linalg.norm(d2), -1, 1)))
        pieces[-1].append(pts[i])
        if ang > 4: pieces.append([pts[i]])
    pieces[-1].append(pts[-1])
    out = []
    for pc in pieces:
        P0, P1 = pc[0], pc[-1]
        d = P1 - P0; w = float(np.linalg.norm(d))
        if w < 0.12: continue
        n = np.array([d[1], -d[0]]) / w
        if n @ s['n'] < 0: n = -n; P0, P1 = P1, P0
        out.append(dict(elev=name, ring=s['ring'], seg=s['i'], p0=P0, p1=P1, z0=z0, z1=z1, n=n,
                        width=w, floors=s['floors'], depth=dep))
    return out or None

_RINGS = {}
def set_rings(O):
    from shapely.geometry import LineString as _LS
    for k in ('A_zem', 'A_tip', 'A_16', 'B_zem'):
        _RINGS[k] = _LS(O[k].exterior.coords)

def all_openings():
    O = load_outlines(); segs = facade_segments(O); set_rings(O)
    res = []; miss = []
    for name in ELEVS:
        for rc in elev_rects(name):
            o = backproject(segs, name, rc)
            (res if o else miss).append((name, rc) if not o else o)
    return O, segs, res, miss

if __name__ == '__main__':
    O, segs, res, miss = all_openings()
    print(len(res), 'openings;', len(miss), 'unassigned')
    for m in miss: print(' miss', m)
    pickle.dump((O, res, miss), open('openings_raw.pkl', 'wb'))
