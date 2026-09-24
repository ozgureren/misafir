import pickle, numpy as np
import os
from reg import R
segs,cols,texts=pickle.load(open(os.path.join(os.environ.get('TKI_WORK', '.'), 'flat.pkl'),'rb'))
SITE_O=np.array([486527.0,39614.0])   # axis 8 x axis A intersection in B/C ground-plan frame (cm)
def rot(origin):
    o=np.array(origin,float)
    return lambda P:((np.asarray(P,float)-o)@R.T+SITE_O)
def shift(dx):
    return lambda P:np.asarray(P,float)+np.array([dx,0.0])
PLANS={
 'A_bod':((461800,37700,465300,41300),rot((464762,40948))),
 'A_zem':((465300,37700,468700,41300),rot((468109,40948))),
 'A_tip':((468700,37700,472000,41300),rot((471370,40948))),
 'A_cat':((473000,37700,476500,41300),rot((475684,40948))),
 'A_16':((472000,37700,473000,41300),rot((473672,40948))),
 'B_bod':((476800,37000,486200,41250),shift(9395)),
 'B_zem':((486200,37000,496300,41250),shift(0)),
 'B_cat':((496300,37000,506000,41250),shift(-9864)),
}
def to_m(P):  # site cm -> local meters
    return (np.asarray(P,float)-SITE_O)/100.0
def plan_items(name, layers=None, kinds=('seg',)):
    box,T=PLANS[name]
    out=[]
    for s,L in zip(segs,cols):
        if s[:,0].min()>=box[0] and s[:,0].max()<=box[2] and s[:,1].min()>=box[1] and s[:,1].max()<=box[3]:
            if layers is None or any(l in L for l in layers):
                out.append((to_m(T(s)),L))
    return out
def plan_texts(name):
    box,T=PLANS[name]
    return [(to_m(T([p]))[0],v,L) for L,p,v,h in texts if box[0]<=p[0]<=box[2] and box[1]<=p[1]<=box[3]]
