"""DWG elevation (top) vs orthographic render (bottom) at identical horizontal scale."""
import pickle, numpy as np, sys, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from facades import ELEVS
from elevwin import ELEV
segs, cols, texts = pickle.load(open('flat.pkl', 'rb'))
bounds = json.load(open('qc/bounds.json'))
for name, rn in (('DOGU', 'DWG_DOGU_CEPHESI'), ('KB', 'DWG_KUZEY_BATI_CEPHESI'), ('GB', 'DWG_GUNEY_BATI_CEPHESI')):
    E = ELEVS[name]; x0, x1 = ELEV[name]
    b = bounds[rn]          # u range, z range of the render (metres)
    ex0, ex1 = E['c0'] + 100 * b['u0'], E['c0'] + 100 * b['u1']
    ey0, ey1 = E['zero'] + 100 * b['z0'], E['zero'] + 100 * b['z1']
    img = plt.imread(f'qc/{rn}.png')
    if img.shape[2] == 4:
        a = img[:, :, 3:4]; img = img[:, :, :3] * a + (1 - a) * 1.0
    fig, ax = plt.subplots(2, 1, figsize=(26, 2 * 26 * (ey1 - ey0) / (ex1 - ex0) + 1.2))
    S = [s for s, L in zip(segs, cols) if x0 <= s[:, 0].min() and s[:, 0].max() < x1 and 38300 < s[:, 1].min() and s[:, 1].max() < 40950
         and not any(k in L for k in ('Kot', 'Yaz', 'Aks', 'Olcu'))]
    ax[0].add_collection(LineCollection(S, colors='k', linewidths=0.35))
    ax[0].set_xlim(ex0, ex1); ax[0].set_ylim(ey0, ey1); ax[0].set_aspect('equal'); ax[0].axis('off')
    ax[0].set_title(f'DWG: {rn.replace("DWG_", "")}  (cm, as drawn)', fontsize=12)
    ax[1].imshow(img, extent=(ex0, ex1, ey0, ey1)); ax[1].set_xlim(ex0, ex1); ax[1].set_ylim(ey0, ey1); ax[1].axis('off')
    ax[1].set_title('3D model - orthographic render, same scale & origin', fontsize=12)
    for a in ax:
        for zz in (-1, 0, 4, 16, 17.6):
            a.axhline(E['zero'] + 100 * zz, color='r', lw=0.4, ls='--')
    plt.tight_layout(); plt.savefig(f'qc/COMPARE_{name}.png', dpi=80)
    print('ok', name)
