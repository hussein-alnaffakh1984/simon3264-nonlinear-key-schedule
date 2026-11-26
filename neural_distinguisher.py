"""Related-key neural distinguisher (multilayer perceptron) for round-reduced Simon 32/64 with the std or v3 key schedule.
  python3 neural_distinguisher.py <std|v3> <key bit 0..15 of k0> <rmin> <rmax> <seed>
Positive pairs: C = E_K(P), C' = E_{K ^ dK}(P ^ dP) with dK = one bit of k0 and dP = (0, same bit), which cancels the key
difference in the first round.  Negative pairs: C' uniform.  A fresh random key for every pair; training and test sets come from
different seeds.  Features: C, C' and C ^ C' as 96 bits.  Model: scikit-learn MLPClassifier(128, 64), ReLU, Adam, learning rate
0.002, batch 512, 6 passes.  Threshold: 0.5 + z/(2 sqrt(n_test)), z = normal quantile for 0.01/36 (one-sided)."""
import sys, json, numpy as np, warnings
from scipy.stats import norm
from sklearn.neural_network import MLPClassifier
import simon_ks as S
warnings.filterwarnings('ignore')
kind=sys.argv[1]; b=int(sys.argv[2]); RMIN=int(sys.argv[3]); RMAX=int(sys.argv[4]); SEED=int(sys.argv[5])
NTR=1<<17; NTE=100000; U=np.uint16; THR=0.5+norm.isf(0.01/36)*0.5/np.sqrt(NTE)
def trace(x,y,rk):
    out={}
    for r in range(RMAX):
        x,y=(y^(S.rol(x,1)&S.rol(x,8))^S.rol(x,2)^rk[r]).astype(U),x
        if r+1>=RMIN: out[r+1]=(x,y)
    return out
def gen(n,seed):
    rng=np.random.default_rng(seed); mk=rng.integers(0,65536,(n,4),dtype=U); x=rng.integers(0,65536,n,dtype=U); y=rng.integers(0,65536,n,dtype=U)
    lab=rng.integers(0,2,n).astype(bool); mk2=mk.copy(); mk2[:,0]^=U(1<<b)
    t1=trace(x,y,S.key_schedule(kind,mk,RMAX)); t2=trace(x,(y^U(1<<b)).astype(U),S.key_schedule(kind,mk2,RMAX))
    return t1,t2,rng.integers(0,65536,n,dtype=U),rng.integers(0,65536,n,dtype=U),lab
def feats(t1,t2,rx,ry,lab,r):
    cx=np.where(lab,t2[r][0],rx); cy=np.where(lab,t2[r][1],ry)
    w=np.stack([t1[r][0],t1[r][1],cx,cy,t1[r][0]^cx,t1[r][1]^cy],1).astype(U)
    return np.unpackbits(w.view(np.uint8),axis=1,bitorder='little').astype(np.float32)
tr=gen(NTR,SEED); te=gen(NTE,SEED+1); res=[]
for r in range(RMIN,RMAX+1):
    clf=MLPClassifier(hidden_layer_sizes=(128,64),batch_size=512,max_iter=6,random_state=SEED,learning_rate_init=2e-3)
    clf.fit(feats(*tr,r),tr[4]); acc=float((clf.predict(feats(*te,r))==te[4]).mean()); se=float(np.sqrt(acc*(1-acc)/NTE))
    res.append(dict(rounds=r,accuracy=acc,ci95=[acc-1.96*se,acc+1.96*se],above_threshold=bool(acc>THR)))
    print("%s bit %d seed %d r=%d accuracy=%.4f [%.4f, %.4f] threshold %.4f %s"%(kind,b,SEED,r,acc,acc-1.96*se,acc+1.96*se,THR,'ABOVE' if acc>THR else 'below'),flush=True)
json.dump(dict(kind=kind,bit=b,seed=SEED,n_train=NTR,n_test=NTE,threshold=float(THR),results=res),open('results/neural_seeds/%s_bit%d_seed%d.json'%(kind,b,SEED),'w'),indent=1)
