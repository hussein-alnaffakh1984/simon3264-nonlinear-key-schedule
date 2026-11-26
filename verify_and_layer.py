"""Exhaustive check of the AND-layer model g(x) = ROL1(x) & ROL8(x) over all 65,536 input differences:
 (i)  support and probability of every output difference against the closed-form conditions (Eq. 6 and Eq. 7 of the manuscript),
 (ii) existence of x with zero output difference (Proposition 3 / remark).   python3 verify_and_layer.py"""
import numpy as np, time
U=np.uint16; x=np.arange(65536,dtype=np.uint32)
rol=lambda v,n:((v<<n)|(v>>(16-n)))&0xFFFF
g=rol(x,1)&rol(x,8); pc=np.array([bin(i).count('1') for i in range(65536)],dtype=np.int64)
t=time.time(); bad_model=0; bad_zero=0; b=np.arange(65536,dtype=np.uint32)
for a in range(1,65536):
    d=g^g[x^a]; cnt=np.bincount(d,minlength=65536)
    if cnt[0]==0: bad_zero+=1
    if a==0xFFFF:
        ok=(pc%2==0); w=15
    else:
        v=int(rol(a,1)|rol(a,8)); db=int(rol(a,1)&~rol(a,8)&rol(a,15))&0xFFFF
        ok=((b&(v^0xFFFF))==0)&(((b^rol(b,7))&db)==0); w=bin(v^db).count('1')
    exp=np.where(ok,65536>>w,0)
    if not np.array_equal(cnt,exp): bad_model+=1
print("input differences checked: 65535 | mismatches with Eq.(6)-(7): %d | differences with no zero-output x: %d | %.0f s"%(bad_model,bad_zero,time.time()-t))
