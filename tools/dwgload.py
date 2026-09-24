"""Load LibreDWG JSON dump (pickled) and flatten model space into world-space primitives."""
import pickle, math, collections, os
import numpy as np

D = pickle.load(open(os.path.join(os.environ.get('TKI_WORK', '.'), 'src.pkl'), 'rb'))
O = D['OBJECTS']
H = {}
for o in O:
    H[o['handle'][-1]] = o

def typ(o): return o.get('entity', o.get('object'))

LAYERS = {o['handle'][-1]: o['name'] for o in O if typ(o) == 'LAYER'}
LAYER_OBJ = {o['name']: o for o in O if typ(o) == 'LAYER'}

def layer(e):
    l = e.get('layer')
    return LAYERS.get(l[-1], '?') if l else '?'

BH = {o['handle'][-1]: o for o in O if typ(o) == 'BLOCK_HEADER'}
BLOCK_NAME = {h: b['name'] for h, b in BH.items()}
# entities per block header (by ownerhandle)
BLOCK_ENTS = collections.defaultdict(list)
MS = []
for o in O:
    if 'entity' not in o: continue
    t = o['entity']
    if t in ('BLOCK', 'ENDBLK', 'SEQEND'): continue
    if o.get('entmode') == 2:
        MS.append(o)
    elif o.get('entmode') == 1:
        pass  # paper space
    else:
        oh = o.get('ownerhandle')
        if oh: BLOCK_ENTS[oh[-1]].append(o)
# also block header 'entities' list
for h, b in BH.items():
    if b['name'] in ('*Model_Space', '*Paper_Space'): continue
    ents = b.get('entities') or []
    if ents and not BLOCK_ENTS.get(h):
        BLOCK_ENTS[h] = [H[r[-1]] for r in ents if r[-1] in H]

def mat_insert(e, bh):
    ip = e['ins_pt']; sc = e.get('scale', [1, 1, 1]); r = e.get('rotation', 0.0)
    base = bh.get('base_pt', [0, 0, 0])
    c, s = math.cos(r), math.sin(r)
    M = np.array([[c * sc[0], -s * sc[1], ip[0]], [s * sc[0], c * sc[1], ip[1]], [0, 0, 1.0]])
    B = np.array([[1, 0, -base[0]], [0, 1, -base[1]], [0, 0, 1.0]])
    ex = e.get('extrusion', [0, 0, 1])
    if ex[2] < 0:  # mirrored OCS
        F = np.diag([-1, 1, 1.0]); M = F @ M
    return M @ B

def arcpts(cx, cy, r, a0, a1, n=24):
    if a1 < a0: a1 += 2 * math.pi
    t = np.linspace(a0, a1, max(4, int(n * (a1 - a0) / (2 * math.pi)) + 2))
    return np.c_[cx + r * np.cos(t), cy + r * np.sin(t)]

def bulge_poly(pts, bulges, closed):
    out = []
    n = len(pts)
    segs = n if closed else n - 1
    for i in range(segs):
        p0 = np.array(pts[i][:2]); p1 = np.array(pts[(i + 1) % n][:2])
        b = bulges[i] if bulges and i < len(bulges) else 0
        out.append(p0)
        if abs(b) > 1e-9:
            th = 4 * math.atan(b); d = np.linalg.norm(p1 - p0)
            if d < 1e-12: continue
            rr = d / (2 * math.sin(th / 2))
            mid = (p0 + p1) / 2; nrm = np.array([-(p1 - p0)[1], (p1 - p0)[0]]) / d
            h = rr * math.cos(th / 2)
            c = mid + nrm * h * (1 if b > 0 else 1)
            a0 = math.atan2(p0[1] - c[1], p0[0] - c[0]); a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
            k = 8
            if b > 0:
                if a1 < a0: a1 += 2 * math.pi
            else:
                if a1 > a0: a1 -= 2 * math.pi
            for t in np.linspace(a0, a1, k)[1:-1]:
                out.append(c + abs(rr) * np.array([math.cos(t), math.sin(t)]))
    if not closed: out.append(np.array(pts[-1][:2]))
    else: out.append(np.array(pts[0][:2]))
    return np.array(out)

def xf(M, P):
    P = np.asarray(P, float)[:, :2]
    return (M @ np.c_[P, np.ones(len(P))].T).T[:, :2]

def flatten(ents, M=np.eye(3), lay=None, depth=0, path=()):
    """yield (kind, layer, data, path) ; kind in polyline/text"""
    for e in ents:
        t = e['entity']; L = layer(e)
        if L == '0' and lay: L = lay
        if t == 'LINE':
            yield 'pl', L, xf(M, [e['start'], e['end']]), path
        elif t == 'LWPOLYLINE':
            pts = e.get('points') or []
            if len(pts) < 2: continue
            closed = bool(e.get('flag', 0) & 1) or bool(e.get('flag', 0) & 512 and False)
            yield 'pl', L, xf(M, bulge_poly(pts, e.get('bulges'), bool(e.get('flag', 0) & 1))), path
        elif t == 'ARC':
            c = e['center']; ex = e.get('extrusion', [0, 0, 1])
            a0, a1 = e['start_angle'], e['end_angle']
            P = arcpts(c[0], c[1], e['radius'], a0, a1)
            if ex[2] < 0: P[:, 0] *= -1
            yield 'pl', L, xf(M, P), path
        elif t == 'CIRCLE':
            c = e['center']; ex = e.get('extrusion', [0, 0, 1])
            P = arcpts(c[0], c[1], e['radius'], 0, 2 * math.pi)
            if ex[2] < 0: P[:, 0] *= -1
            yield 'pl', L, xf(M, P), path
        elif t in ('TEXT', 'MTEXT', 'ATTRIB'):
            v = e.get('text_value') or e.get('text') or ''
            ip = e['ins_pt']
            yield 'tx', L, (xf(M, [ip])[0], v, e.get('height', 1) * abs(M[0, 0] ** 2 + M[1, 0] ** 2) ** .5), path
        elif t == 'INSERT':
            bh = BH.get(e['block_header'][-1]) if e.get('block_header') else None
            if not bh or depth > 8: continue
            M2 = M @ mat_insert(e, bh)
            yield 'ins', L, (M2, bh['name']), path
            yield from flatten(BLOCK_ENTS.get(bh['handle'][-1], []), M2, L, depth + 1, path + (bh['name'],))
        elif t.startswith('DIMENSION'):
            yield 'dim', L, e, path
