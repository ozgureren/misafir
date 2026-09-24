"""Site photo (left) vs photo-matched render (right)."""
import sys, os, glob
from PIL import Image, ImageDraw
ph, rd = sys.argv[1], sys.argv[2]
pairs = [('1', 'PHOTO1_entrance_portal'), ('2', 'PHOTO2_tower_and_portal'), ('3', 'PHOTO3_terrace_to_tower'), ('4', 'PHOTO4_tower_recessed_bay')]
for p, r in pairs:
    fp = next(iter(glob.glob(os.path.join(ph, p + '.*'))), None); fr = os.path.join(rd, r + '.jpg')
    if not fp or not os.path.exists(fr): continue
    a = Image.open(fp).convert('RGB'); b = Image.open(fr).convert('RGB')
    H = 620; a = a.resize((int(a.width * H / a.height), H)); b = b.resize((int(b.width * H / b.height), H))
    im = Image.new('RGB', (a.width + b.width + 20, H + 40), 'white'); im.paste(a, (0, 40)); im.paste(b, (a.width + 20, 40))
    d = ImageDraw.Draw(im); d.text((10, 12), 'FOTOGRAF', fill='black'); d.text((a.width + 30, 12), 'MODEL (Blender Cycles)', fill='black')
    im.save(os.path.join(rd, f'COMPARE_{r}.jpg'), quality=88)
print('photo comparisons written')
