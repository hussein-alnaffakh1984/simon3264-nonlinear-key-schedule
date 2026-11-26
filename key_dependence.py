"""Dependence of round-key bits on master-key bits, and avalanche of the key schedule (Section 4.5).
  python3 key_dependence.py [log2 keys, default 16] [seed, default 20261126]
For N uniform master keys and each of the 64 master-key bits j, the key with bit j flipped is expanded and compared
with the original.  (a) Dependence: output bit b of round key k_i depends on master bit j if the flip changed it for
at least one of the N keys (an observed change proves dependence; all 1024 pairs (j, b) observed = full dependence).
(b) Avalanche: Hamming distance between k_i and its counterpart, averaged over the N keys and the 64 flipped bits;
the summary figure is the further average over i = 8..31.  Output: results/key_dependence.txt"""
import sys, numpy as np, simon_ks as S
LN=int(sys.argv[1]) if len(sys.argv)>1 else 16; SEED=int(sys.argv[2]) if len(sys.argv)>2 else 20261126
N=1<<LN; U=np.uint16; rng=np.random.default_rng(SEED); mk=rng.integers(0,65536,(N,4),dtype=U)
pc=np.array([bin(v).count('1') for v in range(65536)],dtype=np.uint8)
out=["keys 2^%d  seed %d  flipped bits 64  round keys k4..k31"%(LN,SEED)]
for kind in('std','v3'):
    base=S.key_schedule(kind,mk); dep=np.zeros((32,64),dtype=np.uint16); hd=np.zeros((32,64))
    for j in range(64):
        m2=mk.copy(); m2[:,j//16]^=U(1<<(j%16)); ks=S.key_schedule(kind,m2)
        for i in range(4,32):
            d=base[i]^ks[i]; dep[i,j]=np.bitwise_or.reduce(d); hd[i,j]=pc[d].mean()
    pairs=[int(sum(bin(int(v)).count('1') for v in dep[i])) for i in range(32)]
    full=[i for i in range(4,32) if all(p==1024 for p in pairs[i:])]
    mean=hd[8:32].mean()
    out.append("\n%s  (%s)"%(kind,'standard schedule' if kind=='std' else 'proposed schedule'))
    out.append("  i : dependent (master bit, round-key bit) pairs of 1024 | mean Hamming distance of 16 (min..max over the 64 flipped bits)")
    for i in range(4,32): out.append("  %2d: %4d | %.3f (%.3f..%.3f)"%(i,pairs[i],hd[i].mean(),hd[i].min(),hd[i].max()))
    out.append("  first round key from which all 1024 pairs are observed for every later round key: %s"%(full[0] if full else 'none'))
    out.append("  mean Hamming distance over k8..k31: %.3f of 16;  range of the per-round-key means %.3f..%.3f"%(mean,hd[8:32].mean(axis=1).min(),hd[8:32].mean(axis=1).max()))
open('results/key_dependence.txt','w').write('\n'.join(out)+'\n'); print('\n'.join(out))
