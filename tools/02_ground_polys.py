"""Closed ground-level polygons outside the building: terrace faces (terr_holes.pkl) and the sunken court (extpolys.pkl)."""
import pickle, numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union, polygonize
from plans import plan_items
from facades import load_outlines
O = load_outlines()
Bu = unary_union([O['B_zem'], O['A_zem'], O['A_tip']]); Bin = Bu.buffer(-0.05)
# sunken court etc.: polygonize exterior lines + building edge
ls = [LineString(Bu.exterior.coords)]
for P, L in plan_items('B_zem', ['r 2', 'Dash', 'Merdiven', 'r 3', 'r 4', 'Betonarme', 'Duvar']):
    l = LineString(P)
    if not Bin.contains(l): ls.append(l)
ps = [p for p in polygonize(unary_union(ls)) if p.area > 8 and not Bin.contains(p.representative_point())]
pickle.dump(ps, open('extpolys.pkl', 'wb'))
# terrace faces south of the building (lines closed by 0.2 m buffering)
ls = [LineString(Bu.exterior.coords)]
for P, L in plan_items('B_zem', ['r 2', 'Dash', 'Merdiven', 'Duvar', 'Betonarme']):
    l = LineString(P)
    if l.centroid.y < -5: ls.append(l)
for P, L in plan_items('B_cat', ['r 4']):
    l = LineString(P)
    if l.centroid.y < -5 and l.length > 3: ls.append(l)
U = unary_union([l.buffer(0.2, cap_style=2) for l in ls])
holes = [Polygon(h) for g in (U.geoms if hasattr(U, 'geoms') else [U]) for h in g.interiors]
holes = [h for h in holes if h.area > 5 and not Bu.buffer(-0.3).contains(h.representative_point())]
pickle.dump(holes, open('terr_holes.pkl', 'wb'))
print('court/ext polys', len(ps), 'terrace faces', len(holes))
