"""Experimental check of trails found by trail_search.py, using the real key schedules and cipher (simon_ks.py).
  python3 verify_trails.py results/<file>.jsonl [log2_samples=22] [seed=20261126]
For each trail: draw random master keys K and plaintexts P (numpy PCG64, fixed seed), form the partner
(rk: K^dK, P^dP ; rx: ROL_g(K)^dK, ROL_g(P)^dP), run both through the reduced-round cipher, and report
 - key path : fraction of keys whose round-key differences equal the trail's (predicted 2^-w_key),
 - data path: among those keys, fraction of pairs with the trail's output difference (predicted >= 2^-w_data; other trails
   with the same end points can only add to it)."""
import sys, json, numpy as np
import simon_ks as S
f=sys.argv[1]; LN=int(sys.argv[2]) if len(sys.argv)>2 else 22; SEED=int(sys.argv[3]) if len(sys.argv)>3 else 20261126
U=np.uint16; CH=1<<20
print("file %s  samples 2^%d  seed %d"%(f,LN,SEED)); print("kind mode  R | w_key  measured key-path | w_data measured data-path (hits)")
for line in open(f):
    t=json.loads(line); R,g,rx=t['R'],t['gamma'],t['mode']=='rx'
    if t['w_data']>LN-6: print("%-4s %-3s %2d | skipped: 2^-%d needs more than 2^%d samples"%(t['kind'],t['mode'],R,t['w_data'],LN)); continue
    rng=np.random.default_rng([SEED,R,t['weight']]); nk=nd=hit=0
    for _ in range((1<<LN)//CH):
        mk=rng.integers(0,65536,(CH,4),dtype=U); x=rng.integers(0,65536,CH,dtype=U); y=rng.integers(0,65536,CH,dtype=U)
        rot=(lambda v:S.rol(v,g)) if rx else (lambda v:v)
        mk2=np.stack([rot(mk[:,j])^U(t['K'][j] if j<R else 0) for j in range(4)],1).astype(U)
        rk=S.key_schedule(t['kind'],mk,max(R,4)); rk2=S.key_schedule(t['kind'],mk2,max(R,4))
        ok=np.ones(CH,bool)
        for i in range(R): ok&=(rot(rk[i])^rk2[i])==U(t['K'][i])
        cx,cy=S.encrypt(x,y,rk,R); dx,dy=S.encrypt((rot(x)^U(t['X'][0])).astype(U),(rot(y)^U(t['Y'][0])).astype(U),rk2,R)
        h=ok&((rot(cx)^dx)==U(t['X'][R]))&((rot(cy)^dy)==U(t['Y'][R])); nk+=CH; nd+=int(ok.sum()); hit+=int(h.sum())
    lg=lambda a,b:("2^%.2f"%np.log2(a/b)) if a else "0"
    print("%-4s %-3s %2d | %2d     %-10s        | %2d     %-10s (%d)"%(t['kind'],t['mode'],R,t['w_key'],lg(nd,nk),t['w_data'],lg(hit,nd) if nd else 'n/a',hit))
