"""Reference implementation (numpy, vectorised) of Simon 32/64 with key-schedule variants.
std = official Simon 32/64;  v2 = manuscript schedule with unconditional nl();  v3 = proposed schedule.
16-bit words, bit 0 = LSB.  rk[0..3] = master key words."""
import numpy as np
U=np.uint16
Z0=[int(c) for c in "11111010001001010110000111001101111101000100101011000011100110"]
def const(i): return 0xFFFC ^ Z0[(i-4)%62]          # ~x ^ z ^ 3  ==  x ^ const(i)
def ror(x,n): n%=16; return x if n==0 else ((x>>U(n))|(x<<U(16-n))).astype(U)
def rol(x,n): return ror(x,16-n)
def bit(x,n): return (x>>U(n))&U(1)
def nl(w): return (((w<<U(1))&U(0xFFFE))|(bit(w,3)|(bit(w,15)&bit(w,7)&bit(w,13)))).astype(U)
def step(kind,k0,k1,k2,k3,i,consts=True):
    """k0..k3 = rk[i-4..i-1]; returns rk[i]"""
    c=U(const(i) if consts else 0xFFFF)
    if kind=='std': t=ror(k3,3)^k1; return (k0^t^ror(t,1)^c).astype(U)
    if kind=='v2':  t=ror(k3,3)^nl(k1); return (k0^t^ror(t,5)^c).astype(U)
    if kind=='v3':  t=ror(k3,3)^k1^(rol(k3,1)&rol(k3,8)); return (k0^t^ror(t,1)^c).astype(U)
    if kind.startswith('v3m'): t=ror(k3,3)^k1^(rol(k3,1)&rol(k3,8)&U(int(kind[3:],16))); return (k0^t^ror(t,1)^c).astype(U)
    raise ValueError(kind)
def key_schedule(kind,mk,rounds=32,consts=True):
    k=[np.ascontiguousarray(mk[:,j]).astype(U) for j in range(4)]
    for i in range(4,rounds): k.append(step(kind,k[i-4],k[i-3],k[i-2],k[i-1],i,consts))
    return k[:rounds]
def encrypt(x,y,rk,rounds=32):
    for r in range(rounds): x,y=(y^(rol(x,1)&rol(x,8))^rol(x,2)^rk[r]).astype(U),x
    return x,y
def decrypt(x,y,rk,rounds=32):
    for r in range(rounds-1,-1,-1): x,y=y,(x^(rol(y,1)&rol(y,8))^rol(y,2)^rk[r]).astype(U)
    return x,y
TV_KEY=np.array([[0x0100,0x0908,0x1110,0x1918]],dtype=U); TV_PT=(np.array([0x6565],dtype=U),np.array([0x6877],dtype=U))
TV_CT={'std':(0xc69b,0xe9bb),'v3':(0xc619,0x41b4)}
def selftest():
    for kind,ct in TV_CT.items():
        rk=key_schedule(kind,TV_KEY); x,y=encrypt(*TV_PT,rk); assert (int(x[0]),int(y[0]))==ct,kind
        px,py=decrypt(x,y,rk); assert (int(px[0]),int(py[0]))==(0x6565,0x6877)
    return True
selftest()
if __name__=='__main__':
    for kind in('std','v2','v3'):
        rk=key_schedule(kind,TV_KEY); x,y=encrypt(*TV_PT,rk)
        print(kind,"ciphertext %04x %04x | round keys:"%(x[0],y[0]),' '.join('%04x'%int(r[0]) for r in rk))
