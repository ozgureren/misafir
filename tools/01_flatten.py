import sys, pickle
from dwgload import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
segs=[];cols=[];texts=[]
for k,L,dat,p in flatten(MS):
    if k=='pl': segs.append(dat); cols.append(L)
    elif k=='tx': texts.append((L,)+tuple(dat))
pickle.dump((segs,cols,texts),open('flat.pkl','wb'))
print(len(segs),len(texts))
