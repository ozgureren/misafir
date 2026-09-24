from plans import *
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.ops import unary_union
def outline(name, layers=('Duvar','Betonarme','Cam','Kap'), close=0.45, minarea=4):
    geo=[]
    for P,L in plan_items(name,layers):
        if len(P)>=2 and np.ptp(P,axis=0).max()<60: geo.append(LineString(P).buffer(0.04,cap_style=2))
    u=unary_union(geo).buffer(close,join_style=2).buffer(-close,join_style=2)
    polys=[Polygon(p.exterior) for p in (u.geoms if hasattr(u,'geoms') else [u])]
    polys=[p for p in polys if p.area>minarea]
    return unary_union(polys), u
if __name__=='__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,1,figsize=(30,16)); ax=axs
    C={'A_bod':'c','A_zem':'r','A_tip':'m','A_cat':'k','B_bod':'g','B_zem':'b','B_cat':'orange'}
    import pickle; res={}
    for n in PLANS:
        o,u=outline(n); res[n]=o
        for p in (o.geoms if hasattr(o,'geoms') else [o]):
            x,y=p.exterior.xy; ax.plot(x,y,color=C[n],lw=1,label=n)
        print(n, o.geom_type, round(o.area,1), [round(v,2) for v in o.bounds])
    ax.set_aspect('equal'); ax.legend(); ax.grid(True)
    plt.savefig('outlines.png',dpi=80,bbox_inches='tight')
    pickle.dump(res,open('outlines.pkl','wb'))
