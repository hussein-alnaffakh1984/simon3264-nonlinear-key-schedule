"""Experimental check of weak-key trails (key-schedule weight too large for plain sampling in verify_trails.py).
  python3 verify_weak.py results/<file>.jsonl [log2_key_trials=27] [log2_pairs_per_key=14] [seed=20261126]
Stage 1: draw 2^t random master keys (fixed seed) and keep those whose round-key differences follow the trail
         (predicted fraction 2^-w_key).  Stage 2: for every kept key, encrypt 2^p random pairs and count the trail's
         output difference (predicted >= 2^-w_data)."""
import sys, json, numpy as np
import simon_ks as S
f=sys.argv[1]; LT=int(sys.argv[2]) if len(sys.argv)>2 else 27; LP=int(sys.argv[3]) if len(sys.argv)>3 else 14; SEED=int(sys.argv[4]) if len(sys.argv)>4 else 20261126
U=np.uint16; CH=1<<20
print("file %s  key trials 2^%d  pairs per key 2^%d  seed %d"%(f,LT,LP,SEED)); print("kind mode  R | w_key  keys found / expected  measured | w_data measured data-path (hits/pairs)")
for line in open(f):
    t=json.loads(line); R,g,rx=t['R'],t['gamma'],t['mode']=='rx'; rot=(lambda v:S.rol(v,g)) if rx else (lambda v:v)
    if t['w_key']>LT-3: print("%-4s %-3s %2d | w_key %d: skipped (needs more than 2^%d key trials)"%(t['kind'],t['mode'],R,t['w_key'],LT)); continue
    rng=np.random.default_rng([SEED,R,t['w_key'],t['w_data']]); good=[]
    for _ in range((1<<LT)//CH):
        mk=rng.integers(0,65536,(CH,4),dtype=U); mk2=np.stack([rot(mk[:,j])^U(t['K'][j]) for j in range(4)],1).astype(U)
        rk=S.key_schedule(t['kind'],mk,R); rk2=S.key_schedule(t['kind'],mk2,R); ok=np.ones(CH,bool)
        for i in range(4,R): ok&=(rot(rk[i])^rk2[i])==U(t['K'][i])
        good.append(mk[ok])
    good=np.concatenate(good); n=len(good); hits=tot=0
    if n:
        P=1<<LP; mk=np.repeat(good[:256],P,axis=0); m=len(mk); mk2=np.stack([rot(mk[:,j])^U(t['K'][j]) for j in range(4)],1).astype(U)
        x=rng.integers(0,65536,m,dtype=U); y=rng.integers(0,65536,m,dtype=U); rk=S.key_schedule(t['kind'],mk,R); rk2=S.key_schedule(t['kind'],mk2,R)
        cx,cy=S.encrypt(x,y,rk,R); dx,dy=S.encrypt((rot(x)^U(t['X'][0])).astype(U),(rot(y)^U(t['Y'][0])).astype(U),rk2,R)
        hits=int((((rot(cx)^dx)==U(t['X'][R]))&((rot(cy)^dy)==U(t['Y'][R]))).sum()); tot=m
    print("%-4s %-3s %2d | %2d     %5d / %-7.1f      %-8s | %2d     %-9s (%d/%d)"%(t['kind'],t['mode'],R,t['w_key'],n,2.0**(LT-t['w_key']),("2^%.2f"%np.log2(n/2**LT)) if n else "0",t['w_data'],("2^%.2f"%np.log2(hits/tot)) if hits else "0",hits,tot))
