"""Simeck 32/64 (Yang, Zhu, Suder, Aagaard, Gong, CHES 2015) in the same trail model as trail_search.py.
  python3 simeck.py selftest
  python3 simeck.py <sk|rk|rx> Rmin Rmax [--objective total|data] [--gamma G] [--bound W] [--out f.jsonl]
Round: (x,y) -> (y ^ f(x) ^ k, x),  f(x) = (x & S^5 x) ^ S^1 x.   Key schedule: k_{i+4} = k_i ^ f(k_{i+1}) ^ 0xFFFC ^ z_i,
z = m-sequence constant 0x9A42BB1F (LSB first).  Differential model of the AND layer: Koelbl-Leander-Tiessen conditions for
offsets (5,0), checked exhaustively by `selftest`."""
import sys, json, time, argparse, numpy as np
from pysat.solvers import Cadical153
from pysat.card import ITotalizer, CardEnc, EncType
from trail_search import Mo, rolc
N=16; SEQ=0x9A42BB1F
U=np.uint16
def rol(v,n): n%=16; return v if n==0 else ((v<<U(n))|(v>>U(16-n))).astype(U)
def f(x): return ((x&rol(x,5))^rol(x,1)).astype(U)
def cst(i): return 0xFFFC ^ ((SEQ>>i)&1)
def key_schedule(mk,rounds=32):
    k=[np.ascontiguousarray(mk[:,j]).astype(U) for j in range(4)]
    for i in range(rounds-4): k.append((k[i]^f(k[i+1])^U(cst(i))).astype(U))
    return k[:rounds]
def encrypt(x,y,rk,rounds=32):
    for r in range(rounds): x,y=(y^f(x)^rk[r]).astype(U),x
    return x,y
def and_layer(m,a,g,W,A=5,B=0):
    """a -> g through S^A x & S^B x (exact, including the all-ones input difference)."""
    AL=m.new(); m.cl.append([AL]+[-v for v in a]); m.cl+=[[-AL,v] for v in a]
    par=g[0]
    for i in range(1,N):
        q=m.new(); m.xor([q,par,g[i]]); par=q
    m.cl.append([-AL,-par])
    for i in range(N):
        sa,sb,s2=a[(i-A)%N],a[(i-B)%N],a[(i-(2*A-B))%N]
        vb=m.new(); m.OR(vb,sa,sb); t=m.new(); m.AND(t,sb,-sa); db=m.new(); m.AND(db,t,s2)
        w=m.new(); W.append(w)
        if i==0: m.cl+=[[-w,vb],[-w,-db],[-w,-AL],[w,-vb,db,AL]]
        else: m.AND(w,vb,-db)
        j=(i-(A-B))%N; m.cl+=[[-g[i],vb,AL],[-db,-g[i],g[j]],[-db,g[i],-g[j]]]
def build(R,mode,gamma=1):
    m=Mo(); X=[m.new(N) for _ in range(R+1)]; Y=[m.new(N) for _ in range(R+1)]; K=[m.new(N) for _ in range(R)]; W=[]; KW=[]
    for r in range(R):
        g=m.new(N); and_layer(m,X[r],g,W)
        for i in range(N): m.xor([X[r+1][i],Y[r][i],g[i],X[r][(i-1)%N],K[r][i]]); m.xor([Y[r+1][i],X[r][i]])
    for i in range(R-4):
        g=m.new(N); and_layer(m,K[i+1],g,KW); cd=(rolc(cst(i),gamma)^cst(i)) if mode=='rx' else 0
        for j in range(N): m.xor([K[i+4][j],K[i][j],g[j],K[i+1][(j-1)%N]],(cd>>j)&1)
    if mode=='rk': m.cl.append([v for k in K[:4] for v in k])
    if mode=='sk':
        for k in K:
            for v in k: m.cl.append([-v])
        m.cl.append(X[0]+Y[0])
    return m,X,Y,K,W,KW
def read(md,X,Y,K,W,KW):
    val=lambda ws:sum(((v in md)<<j) for j,v in enumerate(ws))
    return dict(X=[val(x) for x in X],Y=[val(y) for y in Y],K=[val(k) for k in K],wd=sum(v in md for v in W),wk=sum(v in md for v in KW))
def minweight(R,mode,gamma,wt,objective):
    m,X,Y,K,W,KW=build(R,mode,gamma); lits=W+KW if objective=='total' else W
    tot=ITotalizer(lits=lits,ubound=min(70,len(lits)),top_id=m.nv); s=Cadical153(bootstrap_with=m.cl+tot.cnf.clauses)
    while not s.solve(assumptions=[-tot.rhs[wt]] if wt<len(tot.rhs) else []): wt+=1
    return wt,read(set(v for v in s.get_model() if v>0),X,Y,K,W,KW)
def decide(R,mode,gamma,bound):
    m,X,Y,K,W,KW=build(R,mode,gamma); ce=CardEnc.atmost(lits=W+KW,bound=bound,top_id=m.nv,encoding=EncType.seqcounter)
    s=Cadical153(bootstrap_with=m.cl+ce.clauses)
    return read(set(v for v in s.get_model() if v>0),X,Y,K,W,KW) if s.solve() else None
def selftest():
    mk=np.array([[0x0100,0x0908,0x1110,0x1918]],dtype=U); x,y=encrypt(np.array([0x6565],dtype=U),np.array([0x6877],dtype=U),key_schedule(mk))
    print("Simeck32/64 test vector: %04x %04x (specification: 770d 2c76)"%(x[0],y[0])); assert (int(x[0]),int(y[0]))==(0x770d,0x2c76)
    xs=np.arange(65536,dtype=np.uint32); r=lambda v,n:((v<<n)|(v>>(16-n)))&0xFFFF if n else v
    g=xs&r(xs,5); pc=np.array([bin(i).count('1') for i in range(65536)]); bad=0; b=xs
    for a in range(1,65536):
        cnt=np.bincount(g^g[xs^a],minlength=65536)
        if a==0xFFFF: ok=(pc%2==0); w=15
        else:
            v=int(r(a,5)|a); db=int(a&(r(a,5)^0xFFFF)&r(a,10)); ok=((b&(v^0xFFFF))==0)&(((b^r(b,5))&db)==0); w=bin(v^db).count('1')
        bad+=not np.array_equal(cnt,np.where(ok,65536>>w,0))
    print("AND-layer model (offsets 5,0): mismatches over 65,535 input differences:",bad); assert bad==0
if __name__=='__main__':
    if sys.argv[1]=='selftest': selftest(); sys.exit(0)
    ap=argparse.ArgumentParser(); ap.add_argument('mode'); ap.add_argument('rmin',type=int); ap.add_argument('rmax',type=int); ap.add_argument('--gamma',type=int,default=1)
    ap.add_argument('--objective',default='total',choices=['total','data']); ap.add_argument('--bound',type=int,default=None); ap.add_argument('--start',type=int,default=0); ap.add_argument('--out',default=None); a=ap.parse_args(); wt=a.start
    for R in range(a.rmin,a.rmax+1):
        t=time.time(); g=a.gamma if a.mode=='rx' else 0
        if a.bound is not None:
            r=decide(R,a.mode,a.gamma,a.bound); sec=time.time()-t
            print(("B simeck %s g=%d R=%2d bound=%d: TRAIL of weight %d (data %d + key %d) %.0fs"%(a.mode,g,R,a.bound,r['wd']+r['wk'],r['wd'],r['wk'],sec)) if r else ("B simeck %s g=%d R=%2d bound=%d: NO TRAIL (minimum >= %d) %.0fs"%(a.mode,g,R,a.bound,a.bound+1,sec)),flush=True)
            rec=dict(cipher='simeck',objective='bound',bound=a.bound,mode=a.mode,gamma=g,R=R,found=bool(r),sec=round(sec,1),**(r or {}))
        else:
            wt,r=minweight(R,a.mode,a.gamma,wt,a.objective); sec=time.time()-t
            print("%s simeck %s g=%d R=%2d weight=%2d (data %d + key %d) %5.0fs dK=%s"%(a.objective[0].upper(),a.mode,g,R,wt,r['wd'],r['wk'],sec,' '.join('%04x'%k for k in r['K'][:4])),flush=True)
            rec=dict(cipher='simeck',objective=a.objective,mode=a.mode,gamma=g,R=R,weight=wt,w_data=r['wd'],w_key=r['wk'],sec=round(sec,1),K=r['K'],X=r['X'],Y=r['Y'])
        if a.out: open(a.out,'a').write(json.dumps(rec)+'\n')
