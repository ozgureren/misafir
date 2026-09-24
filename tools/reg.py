import numpy as np
r=np.radians(45); c,s=np.cos(r),np.sin(r)
R=np.array([[c,-s],[s,c]])
# A-zemin (axis8,axisA)=(468109,40948) -> site (486527,39614)
def a2site(P, origin=(468109,40948)):
    P=np.asarray(P,float)
    return (P-np.array(origin))@R.T+np.array([486527,39614])
