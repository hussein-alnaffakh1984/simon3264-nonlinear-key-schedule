"""Bit-bias experiments behind the first two rows of Table 5.
  python3 bit_bias.py [log2 samples, default 18]      -> results/bit_bias.txt
(1) Related-key: for each bit b of k0, dK = bit b of k0 and dP = (0, bit b), which cancels the key difference in the
    first round.  N random (key, plaintext) pairs per b (generator seed 100 + b).  Statistic: |frequency - 1/2| of each of
    the 32 bits of the ciphertext difference after r rounds; the maximum over the 16 x 32 tests is reported.
(2) Rotational-XOR, rotation 1: K' = rotation of every key word by one position, optionally with one of the 64 key
    bits flipped (65 offsets), P' = rotation of both plaintext words.  N pairs per offset (seed 9).  Statistic: the same
    for the 32 bits of the RX-difference of the ciphertexts; maximum over 65 x 32 tests.
Threshold: two-sided, level 0.01 with Bonferroni correction over the tests of one round count,
|bias| > z / (2 sqrt(N)), z = normal quantile for 0.01 / (2 m), m = 512 for (1) and 2080 for (2)."""
import sys, numpy as np, simon_ks as S
from scipy.stats import norm
LN=int(sys.argv[1]) if len(sys.argv)>1 else 18; N=1<<LN; U=np.uint16; R=15
thr=lambda m: norm.isf(0.01/m/2)/(2*np.sqrt(N))
def trace(x,y,rk):
    out={}
    for r in range(R):
        x,y=(y^(S.rol(x,1)&S.rol(x,8))^S.rol(x,2)^rk[r]).astype(U),x; out[r+1]=(x,y)
    return out
def maxbias(dx,dy):
    d=dx.astype(np.uint32)<<16|dy; return np.abs(np.array([((d>>j)&1).mean() for j in range(32)])-.5).max()
def related_key(kind):
    out=np.zeros(R+1)
    for b in range(16):
        g=np.random.default_rng(100+b); mk=g.integers(0,65536,(N,4),dtype=U); mk2=mk.copy(); mk2[:,0]^=U(1<<b)
        x=g.integers(0,65536,N,dtype=U); y=g.integers(0,65536,N,dtype=U)
        t1=trace(x,y,S.key_schedule(kind,mk,R)); t2=trace(x,(y^U(1<<b)).astype(U),S.key_schedule(kind,mk2,R))
        for r in range(1,R+1): out[r]=max(out[r],maxbias(t1[r][0]^t2[r][0],t1[r][1]^t2[r][1]))
    return out
def rx_one(kind,off):
    g=np.random.default_rng(9); mk=g.integers(0,65536,(N,4),dtype=U); mk2=S.rol(mk,1)
    if off is not None: mk2[:,off[0]]^=U(1<<off[1])
    x=g.integers(0,65536,N,dtype=U); y=g.integers(0,65536,N,dtype=U)
    t1=trace(x,y,S.key_schedule(kind,mk,R)); t2=trace(S.rol(x,1),S.rol(y,1),S.key_schedule(kind,mk2,R))
    return np.array([0]+[maxbias(S.rol(t1[r][0],1)^t2[r][0],S.rol(t1[r][1],1)^t2[r][1]) for r in range(1,R+1)])
def rx(kind):
    best=rx_one(kind,None)
    for w in range(4):
        for b in range(16): best=np.maximum(best,rx_one(kind,(w,b)))
    return best
L=["samples per test 2^%d, rounds 1..%d, schedules: std = standard, v3 = proposed; * = above threshold"%(LN,R)]
for name,fn,m,r0 in(("related-key bit bias (16 key bits x 32 output bits)",related_key,16*32,6),("rotational-XOR bit bias, rotation 1 (65 key offsets x 32 output bits)",rx,65*32,5)):
    T=thr(m); res={k:fn(k) for k in('std','v3')}
    L+=["","%s: m = %d tests per round count, threshold %.5f"%(name,m,T),"rounds      std        v3"]
    for r in range(r0,R+1): L.append("%-6d "%r+"".join(("%.5f%s"%(res[k][r],'*' if res[k][r]>T else ' ')).rjust(11) for k in res))
    L.append("last round above threshold: "+", ".join("%s %d"%(k,max(r for r in range(1,R+1) if res[k][r]>T)) for k in res))
open('results/bit_bias.txt','w').write('\n'.join(L)+'\n'); print('\n'.join(L))
