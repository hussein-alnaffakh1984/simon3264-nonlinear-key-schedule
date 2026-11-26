"""SAT search (CaDiCaL 1.5.3 through PySAT) for minimum-weight trails of round-reduced Simon 32/64.
  python3 trail_search.py <std|v2|v3> <sk|rk|rx> Rmin Rmax [--gamma G] [--start W] [--out file.jsonl]
modes: sk = single-key differential; rk = related-key differential (nonzero key difference);
       rx = rotational-XOR with rotation amount G: difference of a pair (v, v') is ROL_G(v) ^ v'.
Model.  AND layer f(x)=ROL1(x)&ROL8(x): exact differential distribution (Koelbl-Leander-Tiessen, CRYPTO 2015),
including the all-ones input difference.  Because f commutes with rotation, an RX-difference propagates through f exactly
like an XOR difference; the only RX-specific term is the constant ROL_G(c_i)^c_i injected by each key-schedule step.
std schedule is linear (weight 0).  v3 schedule contains the same AND layer on rk[i-1] (exact model, weight counted).
v2 schedule: nonlinear bit n1 with integer weight floor(-log2 p), p in {1/8,7/8} (conservative: never over-counts).
--objective data minimises the data-path weight only and leaves key-schedule transitions free (weak-key setting:
the reported key weight w_key is then the log2 size reduction of the key class for which the trail can hold).
The solver is deterministic: the same command returns the same weights; a found trail is then checked by experiment (verify_trails.py)."""
import sys, itertools, math, time, json, argparse
from pysat.solvers import Cadical153
from pysat.card import ITotalizer
from simon_ks import const
N=16
rolc=lambda v,g:((v<<g)|(v>>(N-g)))&0xFFFF if g%N else v
DDT={}
for d in range(16):                                   # n1 = b3 | (b15&b7&b13); inputs ordered (15,7,3,13)
    c=0
    for x in range(16):
        f=lambda v:((v>>2)&1)|((v&1)&((v>>1)&1)&((v>>3)&1)); c+=f(x)^f(x^d)
    DDT[d]=c/16
class Mo:
    def __init__(s): s.nv=0; s.cl=[]
    def new(s,n=1):
        r=list(range(s.nv+1,s.nv+n+1)); s.nv+=n; return r if n>1 else r[0]
    def xor(s,vs,rhs=0):
        for signs in itertools.product([0,1],repeat=len(vs)):
            if sum(signs)%2!=rhs: s.cl.append([v if sg==0 else -v for v,sg in zip(vs,signs)])
    def AND(s,o,a,b): s.cl+= [[-o,a],[-o,b],[o,-a,-b]]
    def OR(s,o,a,b): s.cl+= [[o,-a],[o,-b],[-o,a,b]]
def and_layer(m,a,g,W):
    """a -> g through f(x)=ROL1(x)&ROL8(x); appends 16 weight literals to W (weight = number of true literals)."""
    A=m.new(); m.cl.append([A]+[-v for v in a]); m.cl+=[[-A,v] for v in a]      # A <=> input difference is all-ones
    par=g[0]
    for i in range(1,N):
        q=m.new(); m.xor([q,par,g[i]]); par=q
    m.cl.append([-A,-par])                                                       # all-ones: output has even weight, cost 15
    for i in range(N):
        s1,s8,s15=a[(i-1)%N],a[(i-8)%N],a[(i-15)%N]
        vb=m.new(); m.OR(vb,s1,s8); t=m.new(); m.AND(t,s1,-s8); db=m.new(); m.AND(db,t,s15)
        w=m.new(); W.append(w)
        if i==0: m.cl+=[[-w,vb],[-w,-db],[-w,-A],[w,-vb,db,A]]
        else: m.AND(w,vb,-db)
        m.cl+=[[-g[i],vb,A],[-db,-g[i],g[(i-7)%N]],[-db,g[i],-g[(i-7)%N]]]
def build(kind,R,mode,gamma=1):
    m=Mo(); X=[m.new(N) for _ in range(R+1)]; Y=[m.new(N) for _ in range(R+1)]; K=[m.new(N) for _ in range(R)]; W=[]; KW=[]
    for r in range(R):
        g=m.new(N); and_layer(m,X[r],g,W)
        for i in range(N):
            m.xor([X[r+1][i],Y[r][i],g[i],X[r][(i-2)%N],K[r][i]]); m.xor([Y[r+1][i],X[r][i]])
    for i in range(4,R):
        k0,k1,k3=K[i-4],K[i-3],K[i-1]; u=m.new(N); b=5 if kind=='v2' else 1
        assert kind in('std','v2','v3') or kind.startswith('v3m'),kind
        cd=(rolc(const(i),gamma)^const(i)) if mode=='rx' else 0
        if kind=='std':
            for j in range(N): m.xor([u[j],k3[(j+3)%N],k1[j]])
        elif kind=='v3':
            g=m.new(N); and_layer(m,k3,g,KW)
            for j in range(N): m.xor([u[j],k3[(j+3)%N],k1[j],g[j]])
        elif kind.startswith('v3m'):
            mask=int(kind[3:],16); g=m.new(N); used=[]
            for j in range(N):
                if not (mask>>j)&1: m.cl.append([-g[j]]); continue
                ia,ib=(j-1)%N,(j-8)%N; used+=[ia,ib]
                act=m.new(); m.OR(act,k3[ia],k3[ib]); m.cl.append([-g[j],act]); KW.append(act)   # active gate: weight 1, output difference free
            assert len(set(used))==len(used),"gates share an input bit: per-gate model would not be exact"
            for j in range(N): m.xor([u[j],k3[(j+3)%N],k1[j],g[j]])
        elif kind=='v2':
            assert mode!='rx',"v2 schedule is not rotation-equivariant; RX model not defined here"
            dn=m.new(); ins=[k1[15],k1[7],k1[3],k1[13]]; wk=m.new(3); KW+=wk
            for d in range(16):
                pre=[(-ins[j] if (d>>j)&1 else ins[j]) for j in range(4)]
                for o in (0,1):
                    p=DDT[d] if o else 1-DDT[d]; lit=-dn if o else dn
                    if p==0: m.cl.append(pre+[lit])
                    else:
                        for k in range(int(math.floor(-math.log2(p)+1e-9))): m.cl.append(pre+[lit,wk[k]])
            for j in range(N): m.xor([u[j],k3[(j+3)%N],dn if j==0 else k1[j-1]])
        for j in range(N): m.xor([K[i][j],k0[j],u[j],u[(j+b)%N]],(cd>>j)&1)
    if mode in('sk','rk') and kind in('std','v3'):
        # Rotating every word of a trail by the same amount gives a trail of equal weight (round function and both schedules
        # commute with rotation for XOR differences).  Keep one representative: with d[j] = OR of bit j over the reference
        # words (master-key difference in rk, plaintext difference in sk), require d[0]=1 and d[15]=0, unless d is all-ones.
        ref=K[:min(4,R)] if mode=='rk' else [X[0],Y[0]]; d=[]
        for j in range(N):
            o=m.new(); m.cl.append([-o]+[w[j] for w in ref]); m.cl+=[[o,-w[j]] for w in ref]; d.append(o)
        allone=m.new(); m.cl.append([allone]+[-v for v in d]); m.cl+=[[-allone,v] for v in d]
        m.cl+=[[d[0],allone],[-d[15],allone]]
    if mode=='rk': m.cl.append([v for k in K[:4] for v in k])
    if mode=='sk':
        for k in K:
            for v in k: m.cl.append([-v])
        m.cl.append(X[0]+Y[0])
    return m,X,Y,K,W,KW
# Optimal total weights already established with this model (used only as lower bounds on sub-trails, Matsui-style).
KNOWN={('std','sk'):[0,0,2,4,6,8,12,14,18,20],('std','rk'):[0,0,0,0,0,0,2,4,8,11],('v3','rk'):[0,0,0,0,0,0,2,6,11,19],
       ('std','rx',1):[0,0,0,0,0,0,0,4,6,10],('v3','rx',1):[0,0,0,0,0,0,0,4,8,14,22]}
KNOWN[('v3','sk')]=KNOWN[('v2','sk')]=KNOWN[('std','sk')]
def bounds(kind,mode,gamma,R,nkw):
    """Sets of literals whose sum is at most W - b for every trail of total weight W.
    A prefix of r rounds of an R-round trail is itself an r-round trail (all modes), so the remaining rounds weigh at most
    W - Opt(r).  For XOR differences (sk, rk) the key-schedule difference recurrence does not depend on the round index, so any
    window of r consecutive rounds is an r-round trail too; every such window is used.  (In rk mode a window of
    >= 4 rounds cannot have an all-zero key difference because the state update is a bijection; shorter windows have bound 0.)"""
    opt=KNOWN.get((kind,mode,gamma) if mode=='rx' else (kind,mode)); out=[]
    if not opt: return out
    dl=lambda a,b:[('d',r) for r in range(a,b)]; kl=lambda a,b:[('k',i) for i in range(max(a,4),min(b,R))]
    for r in range(1,min(R,len(opt))):
        if opt[r]==0: continue
        out.append((dl(r,R)+kl(r,R),opt[r]))                                  # complement of prefix [0,r)
        if mode in('sk','rk') and kind in('std','v3'):
            for a in range(1,R-r+1):                                              # complement of window [a,a+r)
                out.append((dl(0,a)+dl(a+r,R)+kl(4,a+4)+kl(a+r,R),opt[r]))
    return out
def minweight(kind,R,mode,gamma=1,wt=0,objective='total',dmax=None,matsui=True):
    m,X,Y,K,W,KW=build(kind,R,mode,gamma); lits={'total':W+KW,'data':W,'key':KW}[objective]; extra=[]
    val_of=lambda md,ws:sum(((v in md)<<j) for j,v in enumerate(ws))
    if not lits:
        s=Cadical153(bootstrap_with=m.cl); assert s.solve(); md=set(v for v in s.get_model() if v>0)
        return 0,dict(X=[val_of(md,x) for x in X],Y=[val_of(md,y) for y in Y],K=[val_of(md,k) for k in K],wd=sum(v in md for v in W),wk=0)
    tot=ITotalizer(lits=lits,ubound=min(70,len(lits)),top_id=m.nv); top=tot.top_id
    if objective=='key':                                   # minimise key weight subject to data weight <= dmax
        td=ITotalizer(lits=W,ubound=dmax+1,top_id=top); extra=td.cnf.clauses+[[-td.rhs[dmax]]]; top=td.top_id
    parts=[]
    if matsui and objective=='total':
        nk=len(KW)//max(R-4,1) if R>4 else 0
        grp={('d',r):W[16*r:16*r+16] for r in range(R)}; grp.update({('k',i):KW[nk*(i-4):nk*(i-3)] for i in range(4,R)})
        for names,b in bounds(kind,mode,gamma,R,nk):
            ls=[v for n in names for v in grp[n]]
            if ls: t=ITotalizer(lits=ls,ubound=min(70,len(ls)),top_id=top); top=t.top_id; extra+=t.cnf.clauses; parts.append((t,b))
    s=Cadical153(bootstrap_with=m.cl+tot.cnf.clauses+extra)
    def assume(w):
        a=[-tot.rhs[w]] if w<len(tot.rhs) else []
        for t,b in parts:
            if w-b<0: return None                           # W below a proven sub-trail bound: infeasible without solving
            if w-b<len(t.rhs): a.append(-t.rhs[w-b])
        return a
    while True:
        a=assume(wt)
        if a is not None and s.solve(assumptions=a): break
        wt+=1
    md=set(v for v in s.get_model() if v>0)
    return wt,dict(X=[val_of(md,x) for x in X],Y=[val_of(md,y) for y in Y],K=[val_of(md,k) for k in K],wd=sum(v in md for v in W),wk=sum(v in md for v in KW))
def decide(kind,R,mode,gamma,bound):
    """One-shot question: is there a trail of total weight <= bound?  Returns (True, trail) or (False, None).
    A 'False' is a proof (UNSAT) that every trail weighs at least bound+1."""
    from pysat.card import CardEnc, EncType
    m,X,Y,K,W,KW=build(kind,R,mode,gamma); lits=W+KW
    ce=CardEnc.atmost(lits=lits,bound=bound,top_id=m.nv,encoding=EncType.seqcounter); s=Cadical153(bootstrap_with=m.cl+ce.clauses)
    if not s.solve(): return False,None
    md=set(v for v in s.get_model() if v>0); val=lambda ws:sum(((v in md)<<j) for j,v in enumerate(ws))
    return True,dict(X=[val(x) for x in X],Y=[val(y) for y in Y],K=[val(k) for k in K],wd=sum(v in md for v in W),wk=sum(v in md for v in KW))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('kind'); ap.add_argument('mode'); ap.add_argument('rmin',type=int); ap.add_argument('rmax',type=int)
    ap.add_argument('--gamma',type=int,default=1); ap.add_argument('--start',type=int,default=0); ap.add_argument('--objective',default='total',choices=['total','data','key']); ap.add_argument('--dmax',type=int,default=None); ap.add_argument('--no-matsui',action='store_true'); ap.add_argument('--bound',type=int,default=None); ap.add_argument('--out',default=None); a=ap.parse_args(); wt=a.start
    if a.bound is not None:
        for R in range(a.rmin,a.rmax+1):
            t=time.time(); ok,r=decide(a.kind,R,a.mode,a.gamma,a.bound); sec=round(time.time()-t,1); g=a.gamma if a.mode=='rx' else 0
            if ok:
                print("B %s %s g=%d R=%2d bound=%d: TRAIL of weight %d (data %d + key %d) %.0fs dK=%s dP=%04x,%04x dC=%04x,%04x"%(a.kind,a.mode,g,R,a.bound,r['wd']+r['wk'],r['wd'],r['wk'],sec,' '.join('%04x'%k for k in r['K'][:4]),r['X'][0],r['Y'][0],r['X'][R],r['Y'][R]),flush=True)
                rec=dict(objective='bound',bound=a.bound,kind=a.kind,mode=a.mode,gamma=g,R=R,weight=r['wd']+r['wk'],w_data=r['wd'],w_key=r['wk'],sec=sec,K=r['K'],X=r['X'],Y=r['Y'])
            else:
                print("B %s %s g=%d R=%2d bound=%d: NO TRAIL (proved: minimum weight >= %d) %.0fs"%(a.kind,a.mode,g,R,a.bound,a.bound+1,sec),flush=True)
                rec=dict(objective='bound',bound=a.bound,kind=a.kind,mode=a.mode,gamma=g,R=R,proved_min=a.bound+1,sec=sec)
            if a.out: open(a.out,'a').write(json.dumps(rec)+'\n')
        sys.exit(0)
    for R in range(a.rmin,a.rmax+1):
        t=time.time(); wt,r=minweight(a.kind,R,a.mode,a.gamma,wt,a.objective,a.dmax,not a.no_matsui)        # the minimum is non-decreasing in R
        rec=dict(objective=a.objective,dmax=a.dmax,kind=a.kind,mode=a.mode,gamma=a.gamma if a.mode=='rx' else 0,R=R,weight=wt,w_data=r['wd'],w_key=r['wk'],sec=round(time.time()-t,1),K=r['K'],X=r['X'],Y=r['Y'])
        print(a.objective[0].upper()+" %s %s%s R=%2d weight=%2d (data %d + key %d) %5.0fs dK=%s dP=%04x,%04x dC=%04x,%04x"%(a.kind,a.mode,(' g=%d'%a.gamma) if a.mode=='rx' else '',R,wt,r['wd'],r['wk'],rec['sec'],' '.join('%04x'%k for k in r['K'][:4]),r['X'][0],r['Y'][0],r['X'][R],r['Y'][R]),flush=True)
        if a.out: open(a.out,'a').write(json.dumps(rec)+'\n')
