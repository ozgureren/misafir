import pickle,numpy as np
import os
from shapely.geometry import box as sbox, LineString
from shapely.ops import unary_union
segs,cols,texts=pickle.load(open(os.path.join(os.environ.get('TKI_WORK', '.'), 'flat.pkl'),'rb'))
ELEV={'DOGU':(519000,528500),'KB':(528500,536000),'GB':(536000,545400)}
ZERO=38528.0
def elev_rects(name, layers=('Cam','Kap'), tol=4.0):
    x0,x1=ELEV[name]
    G=[]
    for s,L in zip(segs,cols):
        if x0<=s[:,0].min() and s[:,0].max()<x1 and 38300<s[:,1].min() and s[:,1].max()<40900 and any(l in L for l in layers):
            G.append(LineString(s).buffer(tol))
    U=unary_union(G)
    out=[]
    for g in (U.geoms if hasattr(U,'geoms') else [U]):
        b=g.bounds; b=(b[0]+tol,b[1]+tol,b[2]-tol,b[3]-tol)
        if b[2]-b[0]>20 and b[3]-b[1]>20: out.append(b)   # >=20cm both
    return out   # elevation cm coords
if __name__=='__main__':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    for n,(x0,x1) in ELEV.items():
        R=elev_rects(n); print(n,len(R))
        fig,ax=plt.subplots(figsize=(40,9))
        S=[s for s in segs if x0<=s[:,0].min() and s[:,0].max()<x1 and 38300<s[:,1].min() and s[:,1].max()<40900]
        ax.add_collection(LineCollection(S,colors='gray',linewidths=.3))
        for b in R: ax.add_patch(plt.Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],fill=False,ec='r',lw=1))
        ax.set_aspect('equal'); ax.autoscale(); plt.savefig(f'ew_{n}.png',dpi=60,bbox_inches='tight')
