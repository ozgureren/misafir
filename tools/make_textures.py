"""Procedural, seamless PBR textures matched to the site photos (colour sampled by eye from the photographs).
Writes <out>/<name>_col.jpg and <out>/<name>_nrm.png (OpenGL/glTF tangent-space normal).
Each texture covers TILE metres (see TEX below) so UVs = world metres / tile."""
import numpy as np, os, sys
from PIL import Image
N = 1024
rng = np.random.default_rng(7)
OUT = sys.argv[1] if len(sys.argv) > 1 else 'textures'
os.makedirs(OUT, exist_ok=True)

def pnoise(scale_px, n=N, seed=None, aniso=(1.0, 1.0)):
    """periodic (tileable) fractal-ish noise via filtered spectrum, output 0..1"""
    r = np.random.default_rng(seed)
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f * aniso[0], f * aniso[1])
    k = np.sqrt(fx ** 2 + fy ** 2) + 1e-6
    amp = np.exp(-(k * scale_px) ** 2) / np.sqrt(k)
    ph = r.normal(size=(n, n)) + 1j * r.normal(size=(n, n))
    img = np.real(np.fft.ifft2(amp * ph))
    img -= img.min(); img /= img.max()
    return img

def grain(n=N, seed=None):
    r = np.random.default_rng(seed)
    return r.random((n, n))

def normal_from_height(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nz = np.ones_like(h)
    nrm = np.stack([-gx, gy, nz], -1)       # image row 0 = top (V=1) -> flip y for OpenGL convention
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    return ((nrm * 0.5 + 0.5) * 255).astype(np.uint8)

def save(name, col, h, strength):
    col = np.clip(col, 0, 1)
    Image.fromarray((col * 255).astype(np.uint8)).save(os.path.join(OUT, f'{name}_col.jpg'), quality=90)
    Image.fromarray(normal_from_height(h, strength)).save(os.path.join(OUT, f'{name}_nrm.png'), optimize=True)

def tint(base, v, amt):
    return np.clip(np.array(base)[None, None, :] * (1 - amt + 2 * amt * v[..., None]), 0, 1)

yy, xx = np.mgrid[0:N, 0:N] / N

# 1 A-block facade: silicone render, granular, horizontal "fuga" grooves every 1.5 m (tile 3.0 x 3.0 m -> grooves at v=0, 0.5)
g = grain(seed=1); lo = pnoise(60, seed=2); st = pnoise(8, seed=3, aniso=(6, 0.3))
h = 0.55 * g + 0.45 * lo
groove = np.zeros((N, N))
for v0 in (0.0, 0.5):
    d = np.minimum(np.abs(yy - v0), 1 - np.abs(yy - v0))
    groove = np.maximum(groove, np.exp(-(d / 0.0025) ** 2))
h = h - 0.9 * groove
col = tint((0.86, 0.83, 0.75), 0.35 * g + 0.65 * lo, 0.07) * (1 - 0.10 * groove[..., None]) * (1 - 0.05 * st[..., None])
save('plaster_a', col, h, 3.0)

# 2 travertine panels (B/C walls, A ground floor, columns, sills): cream, horizontal veins, pits; 1.20 x 0.60 m joints (tile 2.4 x 2.4)
v1 = pnoise(4, seed=4, aniso=(0.15, 3.0)); pits = (grain(seed=5) > 0.992).astype(float); lo = pnoise(50, seed=6)
jx = np.minimum((xx * 2) % 1, 1 - (xx * 2) % 1); jy = np.minimum((yy * 4) % 1, 1 - (yy * 4) % 1)
joint = np.maximum(np.exp(-(jx / 0.004) ** 2), np.exp(-(jy / 0.008) ** 2))
h = 0.6 * lo + 0.4 * v1 - 0.8 * pits - 0.5 * joint
col = tint((0.87, 0.82, 0.70), 0.6 * v1 + 0.4 * lo, 0.08) * (1 - 0.25 * pits[..., None]) * (1 - 0.12 * joint[..., None])
save('travertine', col, h, 1.6)

# 3 ashlar stone plinth ("tas kaplama"): 0.40 x 0.20 m blocks, running bond, tile 1.6 x 1.6 m (4 x 8 blocks)
bw, bh = N // 4, N // 8
row = (yy * 8).astype(int); off = (row % 2) * 0.5
bx = ((xx * 4 + off) % 4).astype(int)
bid = (row * 7 + bx * 13) % 97
blocktone = np.random.default_rng(8).random(97)[bid]
fx = (xx * 4 + off) % 1; fy = (yy * 8) % 1
mortar = np.maximum(np.exp(-(np.minimum(fx, 1 - fx) / 0.025) ** 2), np.exp(-(np.minimum(fy, 1 - fy) / 0.05) ** 2))
rough = pnoise(6, seed=9); lo = pnoise(40, seed=10)
bev = np.minimum(np.minimum(fx, 1 - fx) * 4, np.minimum(fy, 1 - fy) * 2); bev = np.clip(bev * 6, 0, 1)
h = 0.5 * bev + 0.3 * rough + 0.2 * lo - 0.6 * mortar
base = np.array([0.80, 0.75, 0.64])
col = base[None, None] * (0.78 + 0.30 * blocktone[..., None]) * (0.90 + 0.16 * rough[..., None]) * (0.85 + 0.15 * bev[..., None])
col = col * (1 - mortar[..., None]) + mortar[..., None] * np.array([0.50, 0.48, 0.44])
save('ashlar', col, h, 4.0)

# 4 red marble ("Rosso Levanto"-like): coping band, entrance portal; tile 1.5 x 1.5 m
w1 = pnoise(220, seed=11); w2 = pnoise(40, seed=12); w3 = pnoise(120, seed=25)
f1 = (w1 + 0.12 * w2) * 3.2; f2 = (w3 + 0.1 * w2) * 4.5
vein = np.exp(-((f1 % 1 - 0.5) / 0.018) ** 2) * (0.5 + 0.5 * w2)          # meandering contour veins
vein2 = np.exp(-((f2 % 1 - 0.5) / 0.012) ** 2) * 0.55 * w3
lo = pnoise(30, seed=13); sp = grain(seed=26)
col = np.array([0.40, 0.11, 0.12])[None, None] * (0.75 + 0.45 * lo[..., None]) * (0.95 + 0.1 * sp[..., None])
v = np.clip(vein + vein2, 0, 1)[..., None]
col = col * (1 - 0.85 * v) + 0.85 * v * np.array([0.88, 0.78, 0.76])
save('red_marble', col, 0.3 * lo, 0.3)

# 5 granite floor tiles (terraces): light grey, 0.60 m squares, speckle; tile 2.4 x 2.4
sp = grain(seed=14); lo = pnoise(30, seed=15)
tx = (xx * 4) % 1; ty = (yy * 4) % 1
tj = np.maximum(np.exp(-(np.minimum(tx, 1 - tx) / 0.006) ** 2), np.exp(-(np.minimum(ty, 1 - ty) / 0.006) ** 2))
tid = ((yy * 4).astype(int) * 4 + (xx * 4).astype(int))
ttone = np.random.default_rng(16).random(16)[tid]
col = np.array([0.66, 0.66, 0.65])[None, None] * (0.9 + 0.1 * ttone[..., None]) * (0.85 + 0.25 * sp[..., None] ** 3)
col = col * (1 - 0.35 * tj[..., None])
save('granite', col, 0.4 * sp - tj, 1.2)

# 6 standing-seam metal roof: seams every 0.50 m (tile 2.0 x 2.0), neutral grey (roof colour not visible in photos)
sx = (xx * 4) % 1
seam = np.exp(-(np.minimum(sx, 1 - sx) / 0.012) ** 2)
lo = pnoise(80, seed=17); streak = pnoise(3, seed=18, aniso=(4, 0.2))
col = np.array([0.40, 0.40, 0.41])[None, None] * (0.92 + 0.1 * lo[..., None] + 0.05 * streak[..., None])
col = col * (1 + 0.25 * seam[..., None])
save('metal_roof', col, seam + 0.05 * lo, 6.0)

# 7 ochre render (walls behind the pergola, canopy soffit): smooth warm yellow; tile 3 x 3
g = grain(seed=19); lo = pnoise(60, seed=20)
col = tint((0.86, 0.74, 0.54), 0.3 * g + 0.7 * lo, 0.05)
save('ochre', col, 0.5 * g + 0.5 * lo, 1.2)

# 8 flat roof membrane / gravel: grey; tile 2 x 2
g = grain(seed=21); lo = pnoise(20, seed=22)
col = tint((0.55, 0.54, 0.52), 0.6 * g + 0.4 * lo, 0.12)
save('roof_flat', col, g, 2.0)

# 9 exposed concrete (pit/retaining walls): tile 2.4 x 2.4, form-tie holes grid
g = grain(seed=23); lo = pnoise(35, seed=24)
col = tint((0.66, 0.65, 0.62), 0.3 * g + 0.7 * lo, 0.10)
save('concrete', col, 0.3 * g + 0.7 * lo, 1.5)
print('textures written to', OUT)

# 10 curtains seen behind the hotel-room glazing (photos: light beige sheer curtains with vertical folds); tile 1.2 x 1.2
f = np.sin(xx * 2 * np.pi * 14 + 1.5 * pnoise(20, seed=27)) * 0.5 + 0.5
col = tint((0.80, 0.74, 0.62), 0.7 * f + 0.3 * pnoise(40, seed=28), 0.18)
save('curtain', col, f, 2.0)
print('curtain added')
