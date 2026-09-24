#!/usr/bin/env bash
# Reproduce the exterior model from the DWG.
# Needs: LibreDWG (dwgread) >= 0.13, Python 3.11 with bpy==5.0.1, numpy, shapely, matplotlib.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(dirname "$HERE")"
WORK="${1:-$REPO/_work}"; mkdir -p "$WORK"; cd "$WORK"
export TKI_WORK="$WORK" PYTHONPATH="$HERE"
DWG="$(ls "$REPO"/source/*.dwg | head -1)"
dwgread -O JSON -o src.json "$DWG" || true          # LibreDWG reports non-fatal warnings
python3 "$HERE/00_json_to_pickle.py" src.json
python3 "$HERE/01_flatten.py"                        # blocks exploded -> flat.pkl
python3 "$HERE/02_ground_polys.py"
python3 "$HERE/build_data.py"                        # shell, roofs, canopies, columns
python3 "$HERE/build_data2.py"                       # openings (elevation back-projection), stairs, terraces, court
python3 "$HERE/make_textures.py" "$REPO/model/textures"  # photo-matched seamless PBR textures
python3 "$HERE/blender_build.py" --out "$REPO/model" # .blend + .glb + .fbx
rm -f "$REPO"/model/*.blend1
python3 "$HERE/qc_render.py" --blend "$REPO/model/tki_misafirhane_exterior.blend" --qc "$WORK/qc"
python3 "$HERE/compare.py"
python3 - <<'PY'
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, glob
for f in glob.glob('qc/*.png'):
    im = plt.imread(f)
    if im.ndim == 3 and im.shape[2] == 4:
        a = im[:, :, 3:4]; plt.imsave(f, im[:, :, :3] * a + (1 - a))
PY
cp qc/*.png "$REPO/qc/"
python3 "$HERE/render_photo_views.py" --blend "$REPO/model/tki_misafirhane_exterior.blend" --out "$REPO/qc/photo_views" --samples 48
python3 "$HERE/photo_compare.py" "$REPO/source/photos" "$REPO/qc/photo_views"
cp model.json "$REPO/model/model_data.json"
echo done
